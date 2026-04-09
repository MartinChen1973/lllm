"""
FastAPI chat endpoint backed by a deep agent with subagents and optional MCP tools.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pydantic import BaseModel, Field, field_validator, model_validator

from langchain.tools import ToolRuntime

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, LocalShellBackend

from tools.internet_search import get_local_tools
from tools.skill_tools import get_skill_tools

## ⬇️ Repo-root .env (full-stack-deepagents/.env)
from dotenv import find_dotenv
load_dotenv(find_dotenv(), override=True)
## ⬇️ LangChain OpenAI reads OPENAI_BASE_URL; this project’s .env may use OPENAI_API_BASE
if os.environ.get("OPENAI_API_BASE") and not os.environ.get("OPENAI_BASE_URL"):
    os.environ["OPENAI_BASE_URL"] = os.environ["OPENAI_API_BASE"].rstrip("/")

## ⬇️ Origins allowed if the browser calls this API directly (proxy uses server-side fetch)
DEFAULT_CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3500,http://127.0.0.1:3500,http://localhost:3501,http://127.0.0.1:3501",
).split(",")

## ⬇️ Persistent long-term memory on disk (one global profile + preferences for all sessions)
STORAGE_DIR = Path(__file__).resolve().parent / "storage"
GLOBAL_MEMORIES_DIR = STORAGE_DIR / "memories"
## ⬇️ Agent Skills (SKILL.md trees); see https://docs.langchain.com/oss/python/deepagents/skills
SKILLS_DIR = Path(__file__).resolve().parent / "skills"
SKILL_SOURCES: list[str] = ["/skills/"]
## ⬇️ LangGraph thread checkpoints (conversation state per session_id); override with CHECKPOINT_DB_PATH
CHECKPOINT_DB_PATH = Path(
    os.environ.get("CHECKPOINT_DB_PATH", str(STORAGE_DIR / "checkpoints.sqlite"))
)
## ⬇️ Optional JSON list of MCP servers; when present and non-empty, overrides env-based URLs until cleared via API
MCP_CONFIG_PATH = STORAGE_DIR / "mcp_config.json"
## ⬇️ Chat model id list + selection; persisted under `storage/model_settings.json` (not `DEEP_AGENT_MODEL`)
MODEL_SETTINGS_PATH = STORAGE_DIR / "model_settings.json"
MODEL_DEFAULT_PRESETS: tuple[str, ...] = (
    "openai:gpt-5.1-mini",
    "openai:gpt-5.1",
    "openai:gpt-5-nano",
)

_MCP_SERVER_ID_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")
## ⬇️ Skill package folder names under `skills/` (same character rules as MCP server ids)
_SKILL_ID_RE = _MCP_SERVER_ID_RE
## ⬇️ Strip prior server/model attribution lines before re-inserting from ToolMessages / tool_calls
_ATTRIBUTION_LEADING_LINE_RE = re.compile(
    r"^\s*To answer this question, I used the following tool\(s\):\s*[^\n]+\n*",
    re.IGNORECASE,
)
_ATTRIBUTION_SKILL_LINE_RE = re.compile(
    r"^\s*I followed the skill package\(s\):\s*[^\n]+\n*",
    re.IGNORECASE,
)
## ⬇️ Skill dir segment in virtual paths or Windows paths (`.../skills/<id>/...` or `...\skills\<id>\...`)
_SKILL_DIR_FROM_PATH_RE = re.compile(r"skills[/\\]([^/\\]+)")
## ⬇️ When only the parent graph sees `task`, infer action-finder from prompts + typical CRUD output
_ACTION_FINDER_DELEGATION_HINT_RE = re.compile(
    r"action[-_\s]?finder|actionfinder|实体|CRUD|拆分|camelCase|CIDED|CIDRA|\bCID\b",
    re.IGNORECASE,
)
_CRUD_ACTION_METHOD_RE = re.compile(
    r"\b(create|read|update|delete)[A-Z][a-zA-Z0-9_]*\s*\(",
)
_CRUD_CAMEL_ACTION_RE = re.compile(
    r"\b(create|read|update|delete)[A-Z][a-zA-Z0-9_]+\b",
)
## ⬇️ Prefix before each tool name in the server-built attribution line (UI)
_TOOL_ATTRIBUTION_ICON = "🛠️ "


def _ensure_memories_dir(memories_dir: Path) -> None:
    ## ⬇️ Only create the folder — do not seed profile/preferences: `write_file` refuses to overwrite existing files
    memories_dir.mkdir(parents=True, exist_ok=True)


def _ensure_storage_dir_for_db(db_path: Path) -> None:
    ## ⬇️ SQLite file path must live in an existing directory
    db_path.parent.mkdir(parents=True, exist_ok=True)


def _agent_workspace_dir(runtime: ToolRuntime) -> Path:
    ## ⬇️ Per LangGraph thread_id so `execute` cwd and default filesystem stay isolated on disk
    cfg = getattr(runtime, "config", None) or {}
    conf: dict[str, Any] = {}
    if isinstance(cfg, dict):
        raw_conf = cfg.get("configurable")
        if isinstance(raw_conf, dict):
            conf = raw_conf
    raw_tid = conf.get("thread_id")
    if raw_tid is None or str(raw_tid).strip() == "":
        safe = "_default"
    else:
        safe = "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in str(raw_tid).strip())
        safe = (safe[:240] or "thread").strip(".") or "thread"
    root = STORAGE_DIR / "agent_workspace" / safe
    root.mkdir(parents=True, exist_ok=True)
    return root


def make_memory_backend(runtime: ToolRuntime) -> CompositeBackend:
    ## ⬇️ Default = LocalShellBackend so `execute` works (`SandboxBackendProtocol` on composite.default per Deep Agents)
    ## ⬅️ Virtual /memories and /skills routes unchanged; agent scratch files + shell cwd live under storage/agent_workspace/<thread>/
    _ensure_memories_dir(GLOBAL_MEMORIES_DIR)
    workspace = _agent_workspace_dir(runtime)
    skills_resolved = str(SKILLS_DIR.resolve())
    exe_env = {"AI_API_SKILLS_ROOT": skills_resolved}
    default_backend = LocalShellBackend(
        root_dir=str(workspace),
        virtual_mode=True,
        inherit_env=True,
        env=exe_env,
    )
    routes: dict[str, FilesystemBackend] = {
        "/memories/": FilesystemBackend(
            root_dir=str(GLOBAL_MEMORIES_DIR),
            virtual_mode=True,
        )
    }
    if SKILLS_DIR.is_dir():
        routes["/skills/"] = FilesystemBackend(
            root_dir=str(SKILLS_DIR),
            virtual_mode=True,
        )
    return CompositeBackend(default=default_backend, routes=routes)


## ⬇️ Reuses the lesson list+disk rules; split into profile vs preferences files
LONG_TERM_MEMORY_SYSTEM_PROMPT = """
## Long-term memory (disk)

You have two persistent files under `/memories/` (survive restarts; **shared across every chat session and thread** — the same files for all users of this API instance):

1. **`/memories/profile.txt`** — stable facts about the user: name, age, gender, job, employer, location, timezone, contact hints they volunteered, etc.
   Use lines like `Key: value` (one fact per line). Comment lines may start with `#`.

2. **`/memories/preferences.txt`** — hobbies, language preferences, coding preferences, explanation depth, tone, tools they like, etc.
   Store these as an **unordered bullet list** (`-` or `*`), one preference per line.

### Tools: `write_file` vs `edit_file` (required)

The filesystem backend **does not allow `write_file` on a path that already exists**. If `read_file` succeeds, you **must** use `edit_file` (after reading) to change that file. Use `write_file` **only** when `read_file` reports that the file does not exist (first-time creation). Trying `write_file` on an existing `/memories/profile.txt` or `/memories/preferences.txt` will fail — that is not a system outage; switch to `read_file` + `edit_file`.

### CRITICAL RULES for `/memories/preferences.txt`

1. **FORMAT:** Each preference is its own bullet on its own line.

2. **MANDATORY UPDATE PROCEDURE** when adding a preference:
   - **STEP 1:** Read the current file with `read_file`.
   - **STEP 2:** Copy **ALL** existing bullet lines. Do **not** skip any.
   - **STEP 3:** Append the new preference as a **new** bullet at the end.
   - **STEP 4:** When using `edit_file`, include **ALL** existing bullets **plus** the new one. `edit_file` replaces the whole file — never write only the new bullet.

   **CORRECT:** previous bullets unchanged + one new bullet at the end.  
   **WRONG:** replacing the file with only the new bullet (drops history).

3. **NEVER REMOVE** bullet items unless the user explicitly contradicts an older item; then replace only the conflicting line and keep everything else.

4. **ENHANCEMENT:** If the user elaborates on one preference, you may rewrite that single bullet; preserve all other bullets.

5. **VERIFICATION:** After adding one preference, bullet count should increase by one unless you resolved a conflict.

### CRITICAL RULES for `/memories/profile.txt`

1. **READ FIRST** before answering questions that depend on who the user is.

2. **UPDATES:** Read the file first. If it is missing, create it once with `write_file` (full desired content). If it exists, merge new or corrected `Key: value` lines using `edit_file` only. Update a line when the user gives a new value for the same key (e.g. age, job). Do **not** drop unrelated keys.

3. **REMOVAL:** Remove or change a field only when the user corrects it or asks to forget that field.

### When to read memory

At the start of substantive replies, if the question is personal, stylistic, or ongoing work, read `/memories/profile.txt` and `/memories/preferences.txt` so you stay consistent across sessions. If the user shares new profile facts or preferences, update the appropriate file using the rules above.
""".strip()


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str


class DeleteSessionResponse(BaseModel):
    ok: bool = True


class UiChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class SessionPayload(BaseModel):
    session_id: str
    title: str
    messages: list[UiChatMessage]


class SessionsListResponse(BaseModel):
    sessions: list[SessionPayload]


class McpServerEntryIn(BaseModel):
    ## ⬇️ Unique id for MultiServerMCPClient (letters, digits, hyphen, underscore)
    id: str = Field(..., min_length=1, max_length=64)
    url: str = Field(..., min_length=1)
    headers: dict[str, str] = Field(default_factory=dict)
    ## ⬇️ Soft-removed servers stay in mcp_config.json and can be restored from the settings UI
    deleted: bool = False

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not _MCP_SERVER_ID_RE.match(v.strip()):
            raise ValueError(
                "id must start with a letter and contain only letters, digits, hyphen, underscore (max 64 chars)"
            )
        return v.strip()

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        u = v.strip()
        if not (u.startswith("http://") or u.startswith("https://")):
            raise ValueError("url must be an http(s) MCP Streamable HTTP endpoint")
        return u


class McpSettingsPutBody(BaseModel):
    servers: list[McpServerEntryIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_server_ids(self) -> McpSettingsPutBody:
        ids = [s.id for s in self.servers]
        if len(ids) != len(set(ids)):
            raise ValueError("Each MCP server must have a unique id")
        return self


class McpServerStatusOut(BaseModel):
    id: str
    url: str
    connected: bool
    tool_count: int
    ## ⬇️ Tool names exposed by this MCP server when connected (empty if not loaded)
    tool_names: list[str] = Field(default_factory=list)
    error: str | None = None
    ## ⬇️ Declared HTTP headers for Streamable HTTP (empty when the active config comes from environment variables only)
    headers: dict[str, str] = Field(default_factory=dict)
    ## ⬇️ Deleted entries are kept on disk only; they are not connected to the MCP client
    status: Literal["active", "deleted"] = "active"


class SkillInfoOut(BaseModel):
    ## ⬇️ Immediate child of `skills/` with a `SKILL.md` (agent deep-skills layout)
    id: str
    skill_md_path: str


class SkillDetailOut(BaseModel):
    ## ⬇️ `SKILL.md` body for create/update/get responses
    id: str
    skill_md_path: str
    content: str


class SkillCreateBody(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    content: str = Field(..., min_length=1, max_length=800_000)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not _SKILL_ID_RE.match(v.strip()):
            raise ValueError(
                "id must start with a letter and contain only letters, digits, hyphen, underscore (max 64 chars)"
            )
        return v.strip()


class SkillUpdateBody(BaseModel):
    content: str | None = Field(None, max_length=800_000)
    new_id: str | None = Field(None, min_length=1, max_length=64)

    @field_validator("new_id")
    @classmethod
    def validate_new_id(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not _SKILL_ID_RE.match(v.strip()):
            raise ValueError(
                "new_id must start with a letter and contain only letters, digits, hyphen, underscore (max 64 chars)"
            )
        return v.strip()

    @model_validator(mode="after")
    def at_least_one(self) -> SkillUpdateBody:
        if self.content is None and self.new_id is None:
            raise ValueError("Provide content and/or new_id")
        return self


class McpSettingsResponse(BaseModel):
    source: Literal["file", "environment"]
    servers: list[McpServerStatusOut]
    total_tools: int
    configured_servers: int
    connected_servers: int
    ## ⬇️ Names of tools loaded from MCP servers (after last startup or PUT /settings/mcp)
    mcp_tool_names: list[str] = Field(default_factory=list)
    ## ⬇️ Skill packages discovered on disk (`skills/<id>/SKILL.md`)
    skills: list[SkillInfoOut] = Field(default_factory=list)


class ModelSettingsOut(BaseModel):
    ## ⬇️ LangChain `init_chat_model` string, e.g. `openai:gpt-5.1-mini`
    current_model: str
    models: list[str] = Field(default_factory=list)


class ModelSettingsPutBody(BaseModel):
    current_model: str = Field(..., min_length=1, max_length=512)
    models: list[str] = Field(default_factory=list)

    @field_validator("current_model")
    @classmethod
    def strip_current(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("current_model cannot be empty")
        return s


@dataclass(frozen=True)
class McpServerLoadDetail:
    tool_count: int
    connected: bool
    error: str | None


@dataclass
class McpToolsLoadOutcome:
    tools: list[Any]
    per_server: dict[str, McpServerLoadDetail]
    ## ⬇️ Raw LangChain tools per server id (only servers that completed `get_tools`)
    tools_by_server: dict[str, list[Any]] = field(default_factory=dict)


logger = logging.getLogger(__name__)


def _default_model_settings_dict() -> dict[str, Any]:
    return {
        "current_model": MODEL_DEFAULT_PRESETS[0],
        "models": list(MODEL_DEFAULT_PRESETS),
    }


def _coerce_model_settings(raw: dict[str, Any]) -> ModelSettingsOut:
    defaults = _default_model_settings_dict()
    cm = str(raw.get("current_model", "")).strip() or str(defaults["current_model"])
    models_raw = raw.get("models")
    models: list[str] = []
    if isinstance(models_raw, list):
        seen: set[str] = set()
        for x in models_raw:
            t = str(x).strip()
            if t and t not in seen:
                seen.add(t)
                models.append(t)
    if not models:
        models = list(defaults["models"])
    if cm not in models:
        models.insert(0, cm)
    return ModelSettingsOut(current_model=cm, models=models)


def _read_model_settings_from_disk() -> ModelSettingsOut:
    ## ⬇️ Create or repair `model_settings.json`; keeps file and in-memory agent in sync after manual edits
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not MODEL_SETTINGS_PATH.is_file():
        out = ModelSettingsOut.model_validate(_default_model_settings_dict())
        MODEL_SETTINGS_PATH.write_text(out.model_dump_json(indent=2), encoding="utf-8")
        return out
    try:
        raw = json.loads(MODEL_SETTINGS_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("model_settings root must be a JSON object")
        coerced = _coerce_model_settings(raw)
        MODEL_SETTINGS_PATH.write_text(coerced.model_dump_json(indent=2), encoding="utf-8")
        return coerced
    except (OSError, json.JSONDecodeError, ValueError) as e:
        logger.warning("Invalid model_settings.json (%s), resetting defaults", e)
        out = ModelSettingsOut.model_validate(_default_model_settings_dict())
        MODEL_SETTINGS_PATH.write_text(out.model_dump_json(indent=2), encoding="utf-8")
        return out


def _normalize_model_put(body: ModelSettingsPutBody) -> ModelSettingsOut:
    cm = body.current_model.strip()
    seen: set[str] = set()
    models: list[str] = []
    for x in body.models:
        t = str(x).strip()
        if t and t not in seen:
            seen.add(t)
            models.append(t)
    if not models:
        models = list(MODEL_DEFAULT_PRESETS)
    if cm not in models:
        models.insert(0, cm)
    return ModelSettingsOut(current_model=cm, models=models)


def _persist_model_settings(out: ModelSettingsOut) -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_SETTINGS_PATH.write_text(out.model_dump_json(indent=2), encoding="utf-8")


async def _reload_chat_model_and_agent(fastapi_app: FastAPI, model_str: str) -> None:
    new_model = init_chat_model(model_str)
    fastapi_app.state.chat_model = new_model
    await _build_agent_and_mcp_status(fastapi_app)


def _mcp_connections_from_env() -> dict[str, dict[str, Any]]:
    ## ⬇️ Comma-separated Streamable HTTP URLs; if set, replaces the defaults below
    raw = (os.environ.get("MCP_SERVER_URLS") or "").strip()
    if raw:
        urls = [u.strip() for u in raw.split(",") if u.strip()]
        return {
            f"mcp_{i}": {"transport": "http", "url": url}
            for i, url in enumerate(urls)
        }
    if os.environ.get("MCP_ENABLED", "true").strip().lower() in ("0", "false", "no", "off"):
        return {}
    ## ⬇️ mcp-servers/mcp-server-oa (8501), mcp-servers/mcp-server-bingchuan (8503), optional mcp-servers/mcp-server aux (8502); mcp-server-rag is not used
    u_oa = (os.environ.get("MCP_OA_URL") or "http://127.0.0.1:8501/mcp").strip()
    u_bc = (os.environ.get("MCP_BINGCHUAN_URL") or "http://127.0.0.1:8503/mcp").strip()
    u_aux = (os.environ.get("MCP_AUX_URL") or "http://127.0.0.1:8502/mcp").strip()
    out: dict[str, dict[str, Any]] = {}
    if u_oa:
        out["oa"] = {"transport": "http", "url": u_oa}
    if u_bc:
        out["bingchuan"] = {"transport": "http", "url": u_bc}
    if u_aux:
        out["aux"] = {"transport": "http", "url": u_aux}
    return out


def _http_mcp_connection(url: str, headers: dict[str, str] | None) -> dict[str, Any]:
    ## ⬇️ LangChain accepts transport "http" as an alias for Streamable HTTP
    conn: dict[str, Any] = {"transport": "http", "url": url.strip()}
    if headers:
        conn["headers"] = headers
    return conn


def _read_mcp_config_servers_from_disk() -> list[McpServerEntryIn] | None:
    if not MCP_CONFIG_PATH.is_file():
        return None
    try:
        raw = json.loads(MCP_CONFIG_PATH.read_text(encoding="utf-8"))
        body = McpSettingsPutBody.model_validate(raw)
        return body.servers
    except Exception as e:
        logger.warning("Ignoring invalid %s: %s", MCP_CONFIG_PATH, e)
        return None


def _resolve_mcp_catalog_and_connections() -> tuple[
    list[McpServerEntryIn] | None,
    dict[str, dict[str, Any]],
    Literal["file", "environment"],
]:
    ## ⬇️ Non-empty saved list overrides environment; empty/missing file uses .env defaults; deleted rows stay in file but are omitted from connections
    entries = _read_mcp_config_servers_from_disk()
    if entries:
        conns: dict[str, dict[str, Any]] = {}
        for s in entries:
            if s.deleted:
                continue
            conns[s.id] = _http_mcp_connection(s.url, s.headers or None)
        return entries, conns, "file"
    return None, _mcp_connections_from_env(), "environment"


async def _load_mcp_tools_round(
    connections: dict[str, dict[str, Any]],
    loaded: dict[str, list[Any]],
    last_errors: dict[str, BaseException],
) -> set[str]:
    ## ⬇️ Load only servers not yet in loaded; returns names that failed this round (caller may retry)
    pending = {k: v for k, v in connections.items() if k not in loaded}
    if not pending:
        return set()
    client = MultiServerMCPClient(pending)
    failed: set[str] = set()
    for name in pending:
        try:
            tools = await client.get_tools(server_name=name)
            loaded[name] = tools
            last_errors.pop(name, None)
            logger.info("MCP server %r: loaded %s tool(s)", name, len(tools))
        except Exception as e:  ## ⬅️ expected while peers start; details at DEBUG only
            failed.add(name)
            last_errors[name] = e
            logger.debug("MCP server %r: handshake not ready yet", name, exc_info=True)
            logger.info("MCP server %r: not ready yet; will retry if attempts remain", name)
    return failed


async def _load_mcp_tools_with_retry(
    connections: dict[str, dict[str, Any]],
    *,
    attempts: int = 10,
    delay_sec: float = 1.25,
) -> McpToolsLoadOutcome:
    ## ⬇️ MCP processes may start after uvicorn; retry until every server loads or attempts exhausted — not "any tools"
    if not connections:
        return McpToolsLoadOutcome(tools=[], per_server={}, tools_by_server={})
    loaded: dict[str, list[Any]] = {}
    last_errors: dict[str, BaseException] = {}
    for i in range(attempts):
        failed = await _load_mcp_tools_round(connections, loaded, last_errors)
        if not failed:
            break
        if i < attempts - 1:
            logger.info(
                "MCP: waiting for %s server(s) [%s]; attempt %s/%s, next retry in %ss",
                len(failed),
                ", ".join(sorted(failed)),
                i + 1,
                attempts,
                delay_sec,
            )
            await asyncio.sleep(delay_sec)
    per: dict[str, McpServerLoadDetail] = {}
    for name in connections:
        if name in loaded:
            per[name] = McpServerLoadDetail(len(loaded[name]), True, None)
            continue
        err = last_errors.get(name)
        logger.warning(
            "MCP server %r: no tools after %s attempts%s",
            name,
            attempts,
            f" — {err}" if err else "",
        )
        err_s = str(err) if err else None
        per[name] = McpServerLoadDetail(0, False, err_s)
    out: list[Any] = []
    for name in connections:
        out.extend(loaded.get(name, []))
    return McpToolsLoadOutcome(tools=out, per_server=per, tools_by_server=dict(loaded))


def _content_to_text(content: Any) -> str:
    ## ⬇️ AIMessage.content may be str or a list of blocks (e.g. OpenAI / Responses API)
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text" and block.get("text") is not None:
                    parts.append(str(block["text"]))
                elif "text" in block:
                    parts.append(str(block["text"]))
        return "".join(parts)
    return str(content)


def _last_assistant_reply(messages: list[Any]) -> str:
    ## ⬇️ After tool/subagent turns the last message may be ToolMessage, not AIMessage
    for m in reversed(messages):
        if isinstance(m, AIMessage):
            raw = _content_to_text(m.content)
            if raw.strip():
                return raw
    for m in reversed(messages):
        if isinstance(m, AIMessage):
            return _content_to_text(m.content)
    return ""


def _transcript_for_ui(messages: list[Any]) -> list[UiChatMessage]:
    ## ⬇️ Skip system/tool/internal turns; only show user + assistant text the UI can render
    out: list[UiChatMessage] = []
    for m in messages:
        if isinstance(m, (SystemMessage, ToolMessage)):
            continue
        if isinstance(m, HumanMessage):
            text = _content_to_text(m.content).strip()
            if text:
                out.append(UiChatMessage(role="user", content=text))
        elif isinstance(m, AIMessage):
            text = _content_to_text(m.content).strip()
            if text:
                out.append(UiChatMessage(role="assistant", content=text))
    return out


def _session_title_from_transcript(rows: list[UiChatMessage]) -> str:
    ## ⬇️ Match sidebar behaviour: first user line, truncated
    for row in rows:
        if row.role == "user" and row.content.strip():
            t = row.content.strip()
            return t[:48] + ("…" if len(t) > 48 else "")
    return "New chat"


async def _ordered_thread_ids(checkpointer: AsyncSqliteSaver, *, limit: int) -> list[str]:
    ## ⬇️ Root graph only (checkpoint_ns ''); one row per conversation thread
    async with checkpointer.conn.execute(
        """
        SELECT thread_id
        FROM checkpoints
        WHERE checkpoint_ns = ''
        GROUP BY thread_id
        ORDER BY MAX(checkpoint_id) DESC
        LIMIT ?
        """,
        (limit,),
    ) as cur:
        fetched = await cur.fetchall()
    return [str(r[0]) for r in fetched if r and r[0]]


def _build_subagents() -> list[dict[str, Any]]:
    ## ⬇️ Two lightweight subagents (no extra tools); main agent may delegate via built-in task tool
    return [
        {
            "name": "concise-agent",
            "description": "Use for short, direct answers and summaries.",
            "system_prompt": "You give brief, clear answers without unnecessary detail.",
            "tools": [],
        },
        {
            "name": "detailed-agent",
            "description": "Use when the user asks for step-by-step or in-depth explanation.",
            "system_prompt": "You explain thoroughly with structure and examples when helpful.",
            "tools": [],
        },
    ]


def _connection_url(conn: dict[str, Any]) -> str:
    return str(conn.get("url") or "")


def _langchain_tool_name(t: Any) -> str | None:
    ## ⬇️ StructuredTool, dict, or callable — same rules as local tools in the system prompt
    if isinstance(t, dict):
        x = t.get("name")
        return str(x).strip() if x else None
    n = getattr(t, "name", None)
    if isinstance(n, str) and n.strip():
        return n.strip()
    if callable(t):
        fn = getattr(t, "func", None)
        if callable(fn):
            x = getattr(fn, "__name__", None)
            return str(x) if x else None
        x = getattr(t, "__name__", None)
        return str(x) if x else None
    return None


def _sorted_unique_mcp_tool_names(tools: list[Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in tools:
        name = _langchain_tool_name(t)
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
    out.sort(key=str.lower)
    return out


def _discover_skills(skills_dir: Path) -> list[SkillInfoOut]:
    ## ⬇️ One entry per subfolder that contains `SKILL.md` (virtual path prefix `/skills/`)
    found: list[SkillInfoOut] = []
    if not skills_dir.is_dir():
        return found
    for child in sorted(skills_dir.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        if (child / "SKILL.md").is_file():
            sid = child.name
            found.append(SkillInfoOut(id=sid, skill_md_path=f"/skills/{sid}/SKILL.md"))
    return found


def _ensure_skills_root() -> None:
    ## ⬇️ Persisted skill packages live here; created on first POST if missing
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)


def _skill_package_dir(skill_id: str) -> Path:
    return SKILLS_DIR / skill_id


def _parse_skill_id_param(raw: str) -> str:
    s = raw.strip()
    if not _SKILL_ID_RE.match(s):
        raise HTTPException(
            status_code=422,
            detail="skill id must start with a letter and contain only letters, digits, hyphen, underscore (max 64 chars)",
        )
    return s


def _read_skill_detail(skill_id: str) -> SkillDetailOut:
    sid = _parse_skill_id_param(skill_id)
    md = _skill_package_dir(sid) / "SKILL.md"
    if not md.is_file():
        raise HTTPException(status_code=404, detail=f"Skill not found: {sid}")
    return SkillDetailOut(
        id=sid,
        skill_md_path=f"/skills/{sid}/SKILL.md",
        content=md.read_text(encoding="utf-8"),
    )


def _tool_message_name(m: ToolMessage) -> str | None:
    n = getattr(m, "name", None)
    if isinstance(n, str) and n.strip():
        return n.strip()
    return None


def _tool_call_name_from_obj(tc: Any) -> str | None:
    if isinstance(tc, dict):
        x = tc.get("name")
        return str(x).strip() if x else None
    x = getattr(tc, "name", None)
    if isinstance(x, str) and x.strip():
        return x.strip()
    return None


def _tool_call_args_from_obj(tc: Any) -> dict[str, Any]:
    if isinstance(tc, dict):
        a = tc.get("args")
        return a if isinstance(a, dict) else {}
    a = getattr(tc, "args", None)
    return a if isinstance(a, dict) else {}


def _ordered_tool_uses(messages: list[Any]) -> list[str]:
    ## ⬇️ Prefer ToolMessage (execution record); fallback to AIMessage.tool_calls if messages were trimmed
    seen: set[str] = set()
    out: list[str] = []
    for m in messages:
        if not isinstance(m, ToolMessage):
            continue
        name = _tool_message_name(m)
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
    if out:
        return out
    for m in messages:
        if not isinstance(m, AIMessage):
            continue
        for tc in getattr(m, "tool_calls", None) or []:
            name = _tool_call_name_from_obj(tc)
            if not name or name in seen:
                continue
            seen.add(name)
            out.append(name)
    return out


def _skill_ids_from_tool_call_paths(messages: list[Any]) -> list[str]:
    ## ⬇️ Any tool call whose args reference `/skills/<id>/...` (read_file, write_file, execute, etc.)
    seen: set[str] = set()
    out: list[str] = []
    for m in messages:
        if not isinstance(m, AIMessage):
            continue
        for tc in getattr(m, "tool_calls", None) or []:
            args = _tool_call_args_from_obj(tc)
            for key in ("path", "file_path", "command"):
                val = args.get(key)
                if not isinstance(val, str):
                    continue
                norm = val.replace("\\", "/")
                for mo in _SKILL_DIR_FROM_PATH_RE.finditer(norm):
                    sid = mo.group(1)
                    if sid and sid not in seen:
                        seen.add(sid)
                        out.append(sid)
    return out


def _merge_skill_hints(
    tools_used: list[str],
    from_read_file: list[str],
) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for s in from_read_file:
        if s not in seen:
            seen.add(s)
            out.append(s)
    if "action_finder_log" in tools_used and "action-finder" not in seen:
        out.append("action-finder")
    return out


def _rewrite_task_delegation_to_action_finder_skill(
    tools_used: list[str],
    skills_used: list[str],
    reply: str,
    delta_messages: list[Any],
) -> tuple[list[str], list[str]]:
    ## ⬇️ Subagent runs hide `action_finder_log`; parent only shows `task` — map to skill action-finder when evidence matches
    if "task" not in tools_used:
        return tools_used, skills_used
    if "action-finder" in skills_used:
        return [t for t in tools_used if t != "task"], skills_used
    blobs: list[str] = [reply or ""]
    for m in delta_messages:
        if isinstance(m, ToolMessage) and _tool_message_name(m) == "task":
            blobs.append(_content_to_text(m.content))
        if isinstance(m, AIMessage):
            for tc in getattr(m, "tool_calls", None) or []:
                if _tool_call_name_from_obj(tc) != "task":
                    continue
                args = _tool_call_args_from_obj(tc)
                for key in ("description", "subagent_type", "task_description"):
                    v = args.get(key)
                    if isinstance(v, str) and v.strip():
                        blobs.append(v)
    combined = "\n".join(blobs)
    inferred = (
        bool(_ACTION_FINDER_DELEGATION_HINT_RE.search(combined))
        or bool(_CRUD_ACTION_METHOD_RE.search(combined))
        or bool(_CRUD_CAMEL_ACTION_RE.search(combined))
    )
    if not inferred:
        return tools_used, skills_used
    new_tools = [t for t in tools_used if t != "task"]
    new_skills = [*skills_used]
    if "action-finder" not in new_skills:
        new_skills.append("action-finder")
    return new_tools, new_skills


def _strip_prior_attribution(reply: str) -> str:
    t = (reply or "").lstrip()
    while True:
        m1 = _ATTRIBUTION_LEADING_LINE_RE.match(t)
        if m1:
            t = t[m1.end() :].lstrip()
            continue
        m2 = _ATTRIBUTION_SKILL_LINE_RE.match(t)
        if m2:
            t = t[m2.end() :].lstrip()
            continue
        break
    return t


def _tool_attribution_display_names(names: list[str]) -> list[str]:
    ## ⬇️ Clarify Tavily-backed search; icon before each name for the UI
    out: list[str] = []
    for n in names:
        label = "internet_search (Tavily)" if n == "internet_search" else n
        out.append(f"{_TOOL_ATTRIBUTION_ICON}{label}")
    return out


def _ensure_tool_attribution(reply: str, tools_used: list[str], skills_used: list[str]) -> str:
    ## ⬇️ Prefix from ToolMessages / tool_calls + skill hints; strip any prior attribution from the model
    if not tools_used and not skills_used:
        return reply
    blocks: list[str] = []
    if tools_used:
        listed = ", ".join(_tool_attribution_display_names(tools_used))
        blocks.append(f"To answer this question, I used the following tool(s): {listed}.")
    if skills_used:
        sk = ", ".join(f"📚 {s}" for s in skills_used)
        blocks.append(f"I followed the skill package(s): {sk}.")
    prefix = "\n\n".join(blocks) + "\n\n"
    body = _strip_prior_attribution(reply)
    return prefix + body


def _compose_agent_system_prompt(
    local_tools: list[Any],
    mcp_tools: list[Any],
    *,
    skills_enabled: bool,
) -> str:
    ## ⬇️ Matches prior behaviour: OA / Bingchuan hints only when any MCP tool is registered
    system_prompt = LONG_TERM_MEMORY_SYSTEM_PROMPT + "\n\n"
    system_prompt += (
        "You are a helpful assistant. You may delegate to subagents using the task tool "
        "when their expertise fits the user request. "
    )
    system_prompt += (
        "**Whenever you call any tool** (built-in filesystem tools, `execute`, `task`, `internet_search`, MCP tools, etc.), "
        "start your final answer with exactly: "
        '"To answer this question, I used the following tool(s): " followed by a comma-separated list of the '
        "exact tool names you invoked (Tavily web search is the tool `internet_search`). "
        "Use that line only once per reply; omit it only if you used no tools for that answer."
    )
    if local_tools:
        tool_names = [_langchain_tool_name(t) for t in local_tools]
        tool_names_s = ", ".join(n for n in tool_names if n)
        if tool_names_s:
            system_prompt += f"You have local Python tool(s): {tool_names_s}. "
        if any(n == "internet_search" for n in tool_names):
            system_prompt += (
                "For `internet_search`: use it for web search, current events, or facts not covered "
                "by internal docs. Pass query, optional max_results (default 5), topic (general|news|finance), "
                "and include_raw_content as needed. "
            )
        if any(n == "action_finder_log" for n in tool_names):
            system_prompt += (
                "For `action_finder_log`: call it once per action-finder skill run to append history "
                "(entity name, template_selected must be exactly CIDED or CIDRA or CID — never CRUD, "
                "list of camelCase actions). In the user-facing reply, state the same template explicitly "
                "(e.g. **Template:** CIDED (Create, Index, Details, Edit, Delete)) before listing actions. "
            )
    system_prompt += (
        "The `execute` tool runs shell commands on the API host (not sandboxed). The shell working directory is a "
        "per-session folder under the API storage directory. The environment variable `AI_API_SKILLS_ROOT` points "
        "at the bundled skills directory on disk; run scripts with real paths, for example "
        '`python \"%AI_API_SKILLS_ROOT%\\action-finder\\scripts\\log.py\"` in Windows cmd (with arguments after the path), '
        "or use equivalent quoting on other shells. **Do not expose this service to untrusted users.** "
    )
    if skills_enabled:
        system_prompt += (
            "Bundled **skills** live under `/skills/`; when a skill applies, read its `SKILL.md` with "
            "`read_file` using the path shown in the Skills System list, then follow it. "
            "Supporting files use paths such as `/skills/<skill-dir>/references/...`. "
            "For shell execution, script paths must use real filesystem paths (e.g. under `AI_API_SKILLS_ROOT`), "
            "not only virtual `/skills/...` paths. "
            "The API may add a line to your reply listing which skill package(s) were followed when you read "
            "under `/skills/...` or call `action_finder_log`. "
        )
    if mcp_tools:
        system_prompt += (
            "When MCP tools are available: use `lookup_docs` for organization and leave-policy questions "
            "(OA corpus); use `bingchuan` for 冰雪川 / Bingchuan ice cream or product-knowledge questions; "
            "use `inspect_faiss_oa` or `inspect_faiss_bingchuan` only for debugging the respective FAISS indexes."
        )
    return system_prompt


def _mcp_settings_response_from_load(
    catalog: list[McpServerEntryIn] | None,
    connections: dict[str, dict[str, Any]],
    source: Literal["file", "environment"],
    outcome: McpToolsLoadOutcome,
    *,
    mcp_tool_names: list[str],
    skills: list[SkillInfoOut],
) -> McpSettingsResponse:
    servers: list[McpServerStatusOut] = []
    if catalog is not None:
        for entry in catalog:
            if entry.deleted:
                servers.append(
                    McpServerStatusOut(
                        id=entry.id,
                        url=entry.url,
                        connected=False,
                        tool_count=0,
                        tool_names=[],
                        error=None,
                        headers=dict(entry.headers or {}),
                        status="deleted",
                    )
                )
                continue
            conn = connections.get(entry.id)
            if conn is None:
                continue
            d = outcome.per_server.get(entry.id) or McpServerLoadDetail(0, False, "unknown")
            raw_h = conn.get("headers")
            hdrs: dict[str, str] = {}
            if isinstance(raw_h, dict):
                hdrs = {str(k): str(v) for k, v in raw_h.items()}
            servers.append(
                McpServerStatusOut(
                    id=entry.id,
                    url=_connection_url(conn),
                    connected=d.connected,
                    tool_count=d.tool_count,
                    tool_names=_sorted_unique_mcp_tool_names(
                        outcome.tools_by_server.get(entry.id, [])
                    ),
                    error=d.error,
                    headers=hdrs,
                    status="active",
                )
            )
    else:
        for name in connections:
            conn = connections[name]
            d = outcome.per_server.get(name) or McpServerLoadDetail(0, False, "unknown")
            raw_h = conn.get("headers")
            hdrs: dict[str, str] = {}
            if isinstance(raw_h, dict):
                hdrs = {str(k): str(v) for k, v in raw_h.items()}
            servers.append(
                McpServerStatusOut(
                    id=name,
                    url=_connection_url(conn),
                    connected=d.connected,
                    tool_count=d.tool_count,
                    tool_names=_sorted_unique_mcp_tool_names(outcome.tools_by_server.get(name, [])),
                    error=d.error,
                    headers=hdrs,
                    status="active",
                )
            )
    total_tools = sum(s.tool_count for s in servers if s.status == "active")
    connected_servers = sum(1 for s in servers if s.status == "active" and s.connected)
    configured_servers = sum(1 for s in servers if s.status == "active")
    return McpSettingsResponse(
        source=source,
        servers=servers,
        total_tools=total_tools,
        configured_servers=configured_servers,
        connected_servers=connected_servers,
        mcp_tool_names=mcp_tool_names,
        skills=skills,
    )


def _persist_mcp_settings(body: McpSettingsPutBody) -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not body.servers:
        if MCP_CONFIG_PATH.exists():
            MCP_CONFIG_PATH.unlink()
        return
    MCP_CONFIG_PATH.write_text(body.model_dump_json(indent=2), encoding="utf-8")


async def _build_agent_and_mcp_status(fastapi_app: FastAPI) -> McpSettingsResponse:
    model = fastapi_app.state.chat_model
    checkpointer = fastapi_app.state.checkpointer
    catalog, connections, source = _resolve_mcp_catalog_and_connections()
    outcome = await _load_mcp_tools_with_retry(connections)
    mcp_tools = outcome.tools
    if connections and not mcp_tools:
        logger.warning(
            "No MCP tools loaded (%s server(s) configured); agent runs without MCP tools",
            len(connections),
        )
    local_tools = [*get_local_tools(), *get_skill_tools()]
    skills_arg = SKILL_SOURCES if SKILLS_DIR.is_dir() else None
    if local_tools:
        logger.info("Local tools: registered %s", len(local_tools))
    else:
        logger.info(
            "Local tools: none (set TAVILY_API_KEY for internet_search; action_finder_log requires skills tree)"
        )
    if skills_arg:
        logger.info("Agent skills: loading from %s (virtual path /skills/)", SKILLS_DIR.resolve())
    else:
        logger.info("Agent skills: directory missing (%s); skills= omitted", SKILLS_DIR.resolve())
    all_tools = [*local_tools, *mcp_tools]
    system_prompt = _compose_agent_system_prompt(
        local_tools,
        mcp_tools,
        skills_enabled=bool(skills_arg),
    )
    agent = create_deep_agent(
        model=model,
        tools=all_tools,
        system_prompt=system_prompt,
        subagents=_build_subagents(),
        checkpointer=checkpointer,
        backend=make_memory_backend,
        skills=skills_arg,
    )
    fastapi_app.state.agent = agent
    mcp_names = _sorted_unique_mcp_tool_names(mcp_tools)
    skill_rows = _discover_skills(SKILLS_DIR)
    resp = _mcp_settings_response_from_load(
        catalog,
        connections,
        source,
        outcome,
        mcp_tool_names=mcp_names,
        skills=skill_rows,
    )
    fastapi_app.state.mcp_settings_response = resp
    logger.info(
        "MCP summary: source=%s total_tools=%s connected_servers=%s/%s tool_names=%s skills=%s",
        source,
        resp.total_tools,
        resp.connected_servers,
        resp.configured_servers,
        len(mcp_names),
        len(skill_rows),
    )
    logger.info(
        "Agent backend: LocalShellBackend default (execute enabled); skills root env AI_API_SKILLS_ROOT=%s",
        str(SKILLS_DIR.resolve()),
    )
    return resp


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    ms = _read_model_settings_from_disk()
    model = init_chat_model(ms.current_model)
    logger.info("Chat model (from %s): %s", MODEL_SETTINGS_PATH.name, ms.current_model)
    _ensure_storage_dir_for_db(CHECKPOINT_DB_PATH)
    async with AsyncSqliteSaver.from_conn_string(str(CHECKPOINT_DB_PATH)) as checkpointer:
        await checkpointer.setup()
        fastapi_app.state.chat_model = model
        fastapi_app.state.checkpointer = checkpointer
        await _build_agent_and_mcp_status(fastapi_app)
        logger.info("Long-term memory directory (global): %s", GLOBAL_MEMORIES_DIR)
        logger.info("Checkpoint database: %s", CHECKPOINT_DB_PATH.resolve())
        yield


app = FastAPI(title="DeepAgents AI API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in DEFAULT_CORS_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _preview(text: str, max_len: int = 80) -> str:
    t = " ".join(text.split())
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


@app.get("/settings/mcp", response_model=McpSettingsResponse)
async def get_mcp_settings() -> McpSettingsResponse:
    ## ⬇️ Last MCP load outcome (startup or after PUT /settings/mcp)
    snap = getattr(app.state, "mcp_settings_response", None)
    if snap is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return snap


@app.put("/settings/mcp", response_model=McpSettingsResponse)
async def put_mcp_settings(body: McpSettingsPutBody) -> McpSettingsResponse:
    ## ⬇️ Persist Streamable HTTP MCP servers and rebuild the deep agent with fresh tool bindings
    if getattr(app.state, "checkpointer", None) is None or getattr(app.state, "chat_model", None) is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    try:
        _persist_mcp_settings(body)
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    try:
        return await _build_agent_and_mcp_status(app)
    except Exception as e:
        logger.exception("MCP settings reload failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/settings/models", response_model=ModelSettingsOut)
async def get_model_settings() -> ModelSettingsOut:
    ## ⬇️ Persisted LangChain model id and dropdown list (`storage/model_settings.json`)
    if getattr(app.state, "checkpointer", None) is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return _read_model_settings_from_disk()


@app.put("/settings/models", response_model=ModelSettingsOut)
async def put_model_settings(body: ModelSettingsPutBody) -> ModelSettingsOut:
    ## ⬇️ Save model list and active id, then re-init the chat model and rebuild the agent
    if getattr(app.state, "checkpointer", None) is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    try:
        out = _normalize_model_put(body)
        _persist_model_settings(out)
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    try:
        await _reload_chat_model_and_agent(app, out.current_model)
    except Exception as e:
        logger.exception("Model settings reload failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return out


@app.get("/settings/skills", response_model=list[SkillInfoOut])
async def list_skills_settings() -> list[SkillInfoOut]:
    ## ⬇️ Skill packages discovered on disk; the Node proxy exposes `/settings/skills` for auth and policy later
    if getattr(app.state, "checkpointer", None) is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return _discover_skills(SKILLS_DIR)


@app.get("/settings/skills/{skill_id}", response_model=SkillDetailOut)
async def get_skill(skill_id: str) -> SkillDetailOut:
    if getattr(app.state, "checkpointer", None) is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return _read_skill_detail(skill_id)


@app.post("/settings/skills", response_model=SkillDetailOut)
async def create_skill(body: SkillCreateBody) -> SkillDetailOut:
    if getattr(app.state, "checkpointer", None) is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    _ensure_skills_root()
    dest = _skill_package_dir(body.id)
    if dest.exists():
        raise HTTPException(status_code=409, detail=f"Skill already exists: {body.id}")
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text(body.content, encoding="utf-8")
    try:
        await _build_agent_and_mcp_status(app)
    except Exception as e:
        logger.exception("Agent rebuild after skill create failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return _read_skill_detail(body.id)


@app.put("/settings/skills/{skill_id}", response_model=SkillDetailOut)
async def update_skill(skill_id: str, body: SkillUpdateBody) -> SkillDetailOut:
    if getattr(app.state, "checkpointer", None) is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    sid = _parse_skill_id_param(skill_id)
    d = _skill_package_dir(sid)
    md_path = d / "SKILL.md"
    if not md_path.is_file():
        raise HTTPException(status_code=404, detail=f"Skill not found: {sid}")
    new_id = body.new_id
    if new_id is not None and new_id != sid:
        target = _skill_package_dir(new_id)
        if target.exists():
            raise HTTPException(status_code=409, detail=f"Skill already exists: {new_id}")
        shutil.move(str(d), str(target))
        sid = new_id
        d = target
        md_path = d / "SKILL.md"
    if body.content is not None:
        md_path.write_text(body.content, encoding="utf-8")
    try:
        await _build_agent_and_mcp_status(app)
    except Exception as e:
        logger.exception("Agent rebuild after skill update failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return _read_skill_detail(sid)


@app.delete("/settings/skills/{skill_id}", response_model=DeleteSessionResponse)
async def delete_skill(skill_id: str) -> DeleteSessionResponse:
    if getattr(app.state, "checkpointer", None) is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    sid = _parse_skill_id_param(skill_id)
    d = _skill_package_dir(sid)
    if not (d / "SKILL.md").is_file():
        raise HTTPException(status_code=404, detail=f"Skill not found: {sid}")
    shutil.rmtree(d)
    try:
        await _build_agent_and_mcp_status(app)
    except Exception as e:
        logger.exception("Agent rebuild after skill delete failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return DeleteSessionResponse()


@app.get("/sessions", response_model=SessionsListResponse)
async def list_sessions(
    limit: int = Query(50, ge=1, le=200, description="Max conversations to return, newest first"),
) -> SessionsListResponse:
    ## ⬇️ Hydrate the UI from LangGraph SQLite (same threads as POST /chat uses)
    agent = getattr(app.state, "agent", None)
    checkpointer = getattr(app.state, "checkpointer", None)
    if agent is None or checkpointer is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    thread_ids = await _ordered_thread_ids(checkpointer, limit=limit)
    payloads: list[SessionPayload] = []
    for tid in thread_ids:
        config = {"configurable": {"thread_id": tid}}
        snap = await agent.aget_state(config)
        raw = (snap.values or {}).get("messages") or []
        transcript = _transcript_for_ui(raw)
        if not transcript:
            continue
        payloads.append(
            SessionPayload(
                session_id=tid,
                title=_session_title_from_transcript(transcript),
                messages=transcript,
            )
        )
    logger.info("GET /sessions count=%s (limit=%s)", len(payloads), limit)
    return SessionsListResponse(sessions=payloads)


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    agent = app.state.agent
    config = {"configurable": {"thread_id": body.session_id}}
    logger.info(
        "POST /chat session_id=%s message_len=%s preview=%r",
        body.session_id[:48] + ("…" if len(body.session_id) > 48 else ""),
        len(body.message),
        _preview(body.message),
    )

    n_before = 0
    try:
        snap_before = await agent.aget_state(config)
        prev_msgs = (
            (snap_before.values or {}).get("messages")
            if snap_before and snap_before.values
            else None
        )
        n_before = len(prev_msgs or [])
    except Exception:
        logger.debug("aget_state before /chat failed; tool attribution may span full thread", exc_info=True)

    t0 = time.perf_counter()
    try:
        ## ⬇️ MCP tools from langchain-mcp-adapters are async-only; sync agent.invoke hits StructuredTool sync path and fails
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": body.message}]},
            config,
        )
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        logger.exception("Agent invoke failed after %sms", elapsed_ms)
        raise HTTPException(status_code=500, detail=str(e)) from e

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    raw_messages = list(result.get("messages") or [])
    try:
        snap_after = await agent.aget_state(config)
        state_msgs = list((snap_after.values or {}).get("messages") or [])
        if state_msgs:
            raw_messages = state_msgs
    except Exception:
        logger.debug("aget_state after /chat failed; using invoke result messages", exc_info=True)

    if len(raw_messages) < n_before:
        delta_messages = raw_messages
    else:
        delta_messages = raw_messages[n_before:]
    reply = _last_assistant_reply(raw_messages)
    if not reply and raw_messages:
        logger.warning(
            "No AIMessage text in result (elapsed_ms=%s); tail message types: %s",
            elapsed_ms,
            [type(m).__name__ for m in raw_messages[-5:]],
        )
    else:
        logger.info(
            "POST /chat ok elapsed_ms=%s reply_len=%s preview=%r",
            elapsed_ms,
            len(reply),
            _preview(reply, 120),
        )
    used = _ordered_tool_uses(delta_messages)
    skill_from_paths = _skill_ids_from_tool_call_paths(delta_messages)
    skills_used = _merge_skill_hints(used, skill_from_paths)
    used, skills_used = _rewrite_task_delegation_to_action_finder_skill(
        used, skills_used, reply, delta_messages
    )
    reply = _ensure_tool_attribution(reply, used, skills_used)
    return ChatResponse(reply=reply)


@app.delete("/sessions/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(session_id: str) -> DeleteSessionResponse:
    ## ⬇️ Remove all LangGraph checkpoints for this thread (sidebar "delete conversation")
    tid = session_id.strip()
    if not tid:
        raise HTTPException(status_code=422, detail="session_id must not be empty")
    if len(tid) > 512:
        raise HTTPException(status_code=422, detail="session_id too long")
    checkpointer = getattr(app.state, "checkpointer", None)
    if checkpointer is None:
        raise HTTPException(status_code=503, detail="checkpointer not initialized")
    await checkpointer.adelete_thread(tid)
    logger.info("DELETE /sessions thread_id=%s", tid[:48] + ("…" if len(tid) > 48 else ""))
    return DeleteSessionResponse()
