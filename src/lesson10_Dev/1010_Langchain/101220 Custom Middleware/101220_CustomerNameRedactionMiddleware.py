# Demonstrates custom AgentMiddleware that anonymizes configured literals before each model call
# and restores them in the model output; includes a discovery step and contract pipeline test.

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, AnyMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)

DATA_DIR = Path(__file__).resolve().parent / "data"


def _placeholder_label(index: int) -> str:
    """Map 1-based index to A, B, …, Z, AA, AB, … for suffix after category prefix."""
    letters: list[str] = []
    n = index
    while n > 0:
        n, r = divmod(n - 1, 26)
        letters.append(chr(65 + r))
    return "".join(reversed(letters))


def _dedupe_literals_only(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for s in names:
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _dedupe_entries(entries: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for lit, cat in entries:
        lit = lit.strip()
        if not lit or lit in seen:
            continue
        seen.add(lit)
        out.append((lit, cat))
    return out


def _normalize_category(raw: str) -> str:
    """Map discovery category labels to short slugs used inside {类别_标签} placeholders."""
    s = (raw or "").strip()
    aliases: dict[str, str] = {
        "人名": "人名",
        "公司名称": "公司",
        "公司": "公司",
        "公司简称": "公司简称",
        "组织代码": "组织代码",
        "统一社会信用代码": "组织代码",
        "金额（大写）": "金额大写",
        "金额(大写)": "金额大写",
        "金额（小写）": "金额小写",
        "金额(小写)": "金额小写",
        "日期与时间": "日期",
        "日期": "日期",
        "电话号码": "电话",
        "电话": "电话",
        "电子邮箱": "邮箱",
        "邮箱": "邮箱",
        "通信地址": "地址",
        "地址": "地址",
        "合同编号": "文书编号",
        "项目编号": "文书编号",
        "文书编号": "文书编号",
        "其他": "其他",
        "未分类": "其他",
        "混合": "其他",
    }
    return aliases.get(s, s if s else "其他")


## ⬇️ Reusable middleware: redact literals with typed placeholders {类别_A} before the model
class CustomerNameRedactionMiddleware(AgentMiddleware):
    """Redact configured literals before each model call and restore them in model output."""

    def __init__(
        self,
        sensitive_names: list[str] | None = None,
        *,
        sensitive_entries: list[tuple[str, str]] | None = None,
        artifacts_dir: Path | None = None,
        debug_print: bool = False,
    ) -> None:
        super().__init__()
        if sensitive_entries is not None:
            self._entries = _dedupe_entries(sensitive_entries)
        elif sensitive_names is not None:
            self._entries = [(lit, "其他") for lit in _dedupe_literals_only(sensitive_names)]
        else:
            msg = "Provide either sensitive_entries [(literal, category), ...] or sensitive_names=[...]."
            raise ValueError(msg)
        self._artifacts_dir = artifacts_dir
        self._debug_print = debug_print

    def _build_maps(self) -> tuple[dict[str, str], dict[str, str]]:
        per_cat: dict[str, int] = {}
        real_to_placeholder: dict[str, str] = {}
        for literal, cat in self._entries:
            slug = _normalize_category(cat)
            per_cat[slug] = per_cat.get(slug, 0) + 1
            label = _placeholder_label(per_cat[slug])
            real_to_placeholder[literal] = f"{{{slug}_{label}}}"
        placeholder_to_real = {v: k for k, v in real_to_placeholder.items()}
        return real_to_placeholder, placeholder_to_real

    def redact_document(self, text: str) -> str:
        """Public helper: redact a full document string (for logging anonymized contract)."""
        return self._redact_text(text)

    def _redact_text(self, text: str) -> str:
        real_to_ph, _ = self._build_maps()
        out = text
        for real_name in sorted(real_to_ph.keys(), key=len, reverse=True):
            out = out.replace(real_name, real_to_ph[real_name])
        return out

    def _restore_text(self, text: str) -> str:
        _, ph_to_real = self._build_maps()
        out = text
        for token in sorted(ph_to_real.keys(), key=len, reverse=True):
            out = out.replace(token, ph_to_real[token])
        return out

    def _map_str_message(self, message: AnyMessage, transform: Callable[[str], str]) -> AnyMessage:
        content = message.content
        if not isinstance(content, str):
            return message
        updated = transform(content)
        if updated == content:
            return message
        return message.model_copy(update={"content": updated})

    def _redact_request(self, request: ModelRequest) -> ModelRequest:
        messages = [self._map_str_message(m, self._redact_text) for m in request.messages]
        sm = request.system_message
        if sm is not None:
            text = sm.text
            if text:
                rt = self._redact_text(text)
                if rt != text:
                    return request.override(
                        messages=messages,
                        system_message=SystemMessage(content=rt),
                    )
        return request.override(messages=messages)

    def _restore_response(self, response: ModelResponse) -> ModelResponse:
        new_result: list[BaseMessage] = []
        for m in response.result:
            if isinstance(m, AIMessage):
                new_result.append(self._map_str_message(m, self._restore_text))
            else:
                new_result.append(m)
        return ModelResponse(
            result=new_result,
            structured_response=response.structured_response,
        )

    def _write_artifact_files(self, raw: ModelResponse, restored: ModelResponse) -> None:
        if self._artifacts_dir is None:
            return
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)

        def _first_ai_text(resp: ModelResponse) -> str:
            for m in resp.result:
                if isinstance(m, AIMessage) and isinstance(m.content, str):
                    return m.content
            return ""

        raw_text = _first_ai_text(raw)
        restored_text = _first_ai_text(restored)
        (self._artifacts_dir / "4_模型译文_占位符.md").write_text(raw_text, encoding="utf-8")
        (self._artifacts_dir / "5_最终译文_已恢复.md").write_text(restored_text, encoding="utf-8")

    def _print_intermediate(
        self,
        request: ModelRequest,
        redacted: ModelRequest,
        raw: ModelResponse,
        restored: ModelResponse,
    ) -> None:
        self._write_artifact_files(raw, restored)
        if not self._debug_print:
            return
        real_to_ph, _ = self._build_maps()
        print("\n=== CustomerNameRedactionMiddleware (intermediate) ===")
        print("1) Real name -> placeholder:", dict(real_to_ph))
        print("2) Request messages before redaction (what the graph built):")
        for m in request.messages:
            c = m.content
            print(f"   - {type(m).__name__}: {c!r}" if isinstance(c, str) else f"   - {type(m).__name__}: <non-str>")
        if request.system_message is not None and request.system_message.text:
            t = request.system_message.text
            tail = " …" if len(t) > 160 else ""
            print(f"   - system_prompt (truncated): {t[:160]!r}{tail}")
        print("3) Payload sent to the model (after redaction):")
        for m in redacted.messages:
            c = m.content
            print(f"   - {type(m).__name__}: {c!r}" if isinstance(c, str) else f"   - {type(m).__name__}: <non-str>")
        if redacted.system_message is not None and redacted.system_message.text:
            t = redacted.system_message.text
            tail = " …" if len(t) > 160 else ""
            print(f"   - system_prompt (truncated): {t[:160]!r}{tail}")
        print("4) Model raw reply (placeholders still present):")
        for m in raw.result:
            if isinstance(m, AIMessage):
                c = m.content
                print(f"   - AIMessage: {c!r}" if isinstance(c, str) else "   - AIMessage: <non-str>")
            else:
                print(f"   - {type(m).__name__}: (skipped)")
        print("5) Reply after restoring real names (what is merged into agent state):")
        for m in restored.result:
            if isinstance(m, AIMessage):
                c = m.content
                print(f"   - AIMessage: {c!r}" if isinstance(c, str) else "   - AIMessage: <non-str>")
            else:
                print(f"   - {type(m).__name__}: (skipped)")
        print("=== end intermediate trace ===\n")

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        redacted = self._redact_request(request)
        raw = handler(redacted)
        restored = self._restore_response(raw)
        self._print_intermediate(request, redacted, raw, restored)
        return restored

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        redacted = self._redact_request(request)
        raw = await handler(redacted)
        restored = self._restore_response(raw)
        self._print_intermediate(request, redacted, raw, restored)
        return restored


## ⬇️ Structured discovery output (local agent → middleware)
class EntityGroup(BaseModel):
    """One logical entity with category and every surface form that appears in the text."""

    category: str = Field(description="类别：人名、公司、组织代码、金额大写、金额小写、日期等")
    canonical_name: str = Field(
        description="具体专名或数值（如公司全称、18 位代码、某日期全文），不得填字段标签如「日期」「统一社会信用代码」「金额」",
    )
    surface_forms: list[str] = Field(
        default_factory=list,
        description="文中出现的所有需替换字面量（简称、别名、第二处写法）；组织代码填数字本体，勿填标签文字",
    )


class SensitiveDiscovery(BaseModel):
    """Discovery model output: groups plus flat list for the middleware."""

    groups: list[EntityGroup] = Field(default_factory=list)
    redact_literals: list[str] = Field(
        description="待匿名化的字面量完整列表，须覆盖文中出现的每一种写法",
    )


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


## ⬅️ Field labels must never be redacted alone (would break phrases like 签署日期)
_DISCOVERY_SKIP_LITERALS: frozenset[str] = frozenset(
    {
        "日期",
        "时间",
        "金额",
        "姓名",
        "电话",
        "地址",
        "甲方",
        "乙方",
        "统一社会信用代码",
        "法定代表人",
        "合同编号",
        "签订地点",
        "签署日期",
    }
)


def _normalize_discovered_literal(lit: str, category: str) -> str:
    """Strip common field labels from discovery noise so labels stay visible in the document."""
    s = lit.strip()
    slug = _normalize_category(category)
    if slug == "组织代码":
        for prefix in ("统一社会信用代码：", "统一社会信用代码:", "组织机构代码：", "组织机构代码:"):
            if s.startswith(prefix):
                return s[len(prefix) :].strip()
    if slug == "人名" and "：" in s and len(s) <= 32:
        tail = s.split("：", 1)[1].strip()
        if tail and len(tail) <= 12:
            return tail
    return s


def _entries_from_discovery(discovery: SensitiveDiscovery) -> list[tuple[str, str]]:
    """Build (literal, category) pairs from groups; `redact_literals` only if not already seen."""
    entries: list[tuple[str, str]] = []
    seen: set[str] = set()
    for g in discovery.groups:
        cat = g.category
        for s in [g.canonical_name, *g.surface_forms]:
            s = s.strip()
            if not s or s in _DISCOVERY_SKIP_LITERALS:
                continue
            s = _normalize_discovered_literal(s, cat)
            if not s or s in _DISCOVERY_SKIP_LITERALS:
                continue
            if s in seen:
                continue
            seen.add(s)
            entries.append((s, cat))
    for s in discovery.redact_literals:
        s = s.strip()
        if not s or s in _DISCOVERY_SKIP_LITERALS:
            continue
        s = _normalize_discovered_literal(s, "其他")
        if not s or s in seen:
            continue
        seen.add(s)
        entries.append((s, "其他"))
    return entries


def run_discovery_agent(contract_text: str, system_prompt: str) -> SensitiveDiscovery:
    """Local discovery agent: structured extraction only (no tool loop)."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured = llm.with_structured_output(SensitiveDiscovery)
    return structured.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=(
                    "请根据系统指令，从下列合同全文中抽取所有需要匿名化的字面量。\n\n"
                    "--- 合同全文开始 ---\n"
                    f"{contract_text}\n"
                    "--- 合同全文结束 ---"
                )
            ),
        ]
    )


async def main_contract_pipeline_test() -> None:
    """Load contract + prompt, discover literals, anonymize, translate, write numbered artifacts."""
    contract_path = DATA_DIR / "1_原始采购合同.md"
    prompt_path = DATA_DIR / "00_敏感信息匿名化抽取_系统提示词.md"
    if not contract_path.is_file():
        raise FileNotFoundError(f"Missing {contract_path}")
    if not prompt_path.is_file():
        raise FileNotFoundError(f"Missing {prompt_path}")

    contract_text = _load_text(contract_path)
    system_prompt = _load_text(prompt_path)

    print("Running discovery agent (structured output)…")
    discovery = run_discovery_agent(contract_text, system_prompt)
    (DATA_DIR / "2_发现的敏感实体.json").write_text(
        json.dumps(discovery.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    entries = _entries_from_discovery(discovery)
    if not entries:
        raise RuntimeError("Discovery returned no entities; aborting.")

    middleware = CustomerNameRedactionMiddleware(
        sensitive_entries=entries,
        artifacts_dir=DATA_DIR,
        debug_print=False,
    )
    anonymized = middleware.redact_document(contract_text)
    (DATA_DIR / "3_匿名化采购合同.md").write_text(anonymized, encoding="utf-8")

    translator_agent = create_agent(
        # model="openai:gpt-4o-mini",
        model="openai:gpt-5.1",
        system_prompt=(
            "You translate the user's Chinese contract text into clear English. "
            "Preserve typed placeholder tokens exactly as written, e.g. {人名_A}, {公司_B}, "
            "{日期_A}, {组织代码_A}, {金额大写_A}; do not translate, reorder, drop, or alter them."
        ),
        middleware=[middleware],
    )

    print("Running translator agent (with redaction middleware)…")
    result = await translator_agent.ainvoke({
        "messages": [
            HumanMessage(
                "请将下列合同全文翻译为英文，保持条款结构清晰；不要省略占位符。\n\n" + contract_text
            )
        ],
    })
    last = result.get("messages", [])[-1]
    content = last.content if hasattr(last, "content") else str(last)
    print("\nDone. Artifacts under:", DATA_DIR)
    print("Final assistant message (first 400 chars):", (content[:400] + "…") if len(str(content)) > 400 else content)


async def main() -> None:
    await main_contract_pipeline_test()


if __name__ == "__main__":
    asyncio.run(main())
