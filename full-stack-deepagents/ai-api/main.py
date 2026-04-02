"""
FastAPI chat endpoint backed by a deep agent with subagents and optional MCP tools.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from langchain.tools import ToolRuntime

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend

from tools.internet_search import get_local_tools

## ⬇️ Repo-root .env (full-stack-deepagents/.env)
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
## ⬇️ LangChain OpenAI reads OPENAI_BASE_URL; this project’s .env may use OPENAI_API_BASE
if os.environ.get("OPENAI_API_BASE") and not os.environ.get("OPENAI_BASE_URL"):
    os.environ["OPENAI_BASE_URL"] = os.environ["OPENAI_API_BASE"].rstrip("/")

## ⬇️ Default model string; override with DEEP_AGENT_MODEL
DEFAULT_MODEL = os.environ.get("DEEP_AGENT_MODEL", "openai:gpt-4o-mini")
## ⬇️ Origins allowed if the browser calls this API directly (proxy uses server-side fetch)
DEFAULT_CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3500,http://127.0.0.1:3500,http://localhost:3501,http://127.0.0.1:3501",
).split(",")

## ⬇️ Persistent long-term memory on disk (one global profile + preferences for all sessions)
STORAGE_DIR = Path(__file__).resolve().parent / "storage"
GLOBAL_MEMORIES_DIR = STORAGE_DIR / "memories"


def _ensure_memories_dir(memories_dir: Path) -> None:
    ## ⬇️ Only create the folder — do not seed profile/preferences: `write_file` refuses to overwrite existing files
    memories_dir.mkdir(parents=True, exist_ok=True)


def make_memory_backend(runtime: ToolRuntime) -> CompositeBackend:
    ## ⬇️ Ephemeral workspace + /memories/* persisted under storage/memories/ (shared globally)
    _ensure_memories_dir(GLOBAL_MEMORIES_DIR)
    return CompositeBackend(
        default=StateBackend(runtime),
        routes={
            "/memories/": FilesystemBackend(
                root_dir=str(GLOBAL_MEMORIES_DIR),
                virtual_mode=True,
            )
        },
    )


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


logger = logging.getLogger(__name__)


def _mcp_connections_from_env() -> dict[str, dict[str, str]]:
    ## ⬇️ Comma-separated Streamable HTTP URLs; if set, replaces the two defaults
    raw = (os.environ.get("MCP_SERVER_URLS") or "").strip()
    if raw:
        urls = [u.strip() for u in raw.split(",") if u.strip()]
        return {
            f"mcp_{i}": {"transport": "http", "url": url}
            for i, url in enumerate(urls)
        }
    if os.environ.get("MCP_ENABLED", "true").strip().lower() in ("0", "false", "no", "off"):
        return {}
    u1 = (os.environ.get("MCP_RAG_URL") or "http://127.0.0.1:8501/mcp").strip()
    u2 = (os.environ.get("MCP_AUX_URL") or "http://127.0.0.1:8502/mcp").strip()
    out: dict[str, dict[str, str]] = {}
    if u1:
        out["rag"] = {"transport": "http", "url": u1}
    if u2:
        out["aux"] = {"transport": "http", "url": u2}
    return out


async def _load_mcp_tools_per_server(
    connections: dict[str, dict[str, str]],
) -> list[Any]:
    ## ⬇️ Load each MCP server separately so one offline server does not block the other
    if not connections:
        return []
    client = MultiServerMCPClient(connections)
    all_tools: list[Any] = []
    for name in connections:
        try:
            tools = await client.get_tools(server_name=name)
            all_tools.extend(tools)
            logger.info("MCP server %r: loaded %s tool(s)", name, len(tools))
        except Exception:
            logger.warning("MCP server %r: failed to load tools", name, exc_info=True)
    return all_tools


async def _load_mcp_tools_with_retry(
    connections: dict[str, dict[str, str]],
    *,
    attempts: int = 10,
    delay_sec: float = 1.25,
) -> list[Any]:
    ## ⬇️ MCP may start after uvicorn; avoid a single failed handshake leaving the agent tool-less for the whole process
    if not connections:
        return []
    last: list[Any] = []
    for i in range(attempts):
        last = await _load_mcp_tools_per_server(connections)
        if last:
            return last
        if i < attempts - 1:
            logger.warning(
                "MCP: no tools loaded yet (attempt %s/%s); retrying in %ss",
                i + 1,
                attempts,
                delay_sec,
            )
            await asyncio.sleep(delay_sec)
    return last


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


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    model = init_chat_model(DEFAULT_MODEL)
    checkpointer = MemorySaver()
    connections = _mcp_connections_from_env()
    mcp_tools = await _load_mcp_tools_with_retry(connections)
    if connections and not mcp_tools:
        logger.warning(
            "No MCP tools loaded (%s server(s) configured); agent runs without MCP tools",
            len(connections),
        )
    local_tools = get_local_tools()
    if local_tools:
        logger.info("Local tools: registered %s (Tavily internet_search)", len(local_tools))
    else:
        logger.info("Local tools: none (set TAVILY_API_KEY for internet_search)")
    all_tools = [*local_tools, *mcp_tools]
    system_prompt = LONG_TERM_MEMORY_SYSTEM_PROMPT + "\n\n"
    system_prompt += (
        "You are a helpful assistant. You may delegate to subagents using the task tool "
        "when their expertise fits the user request. "
    )
    if local_tools:
        system_prompt += (
            "You have a local Python tool `internet_search`: use it for web search, current events, "
            "or facts not covered by internal docs. Pass query, optional max_results (default 5), "
            "topic (general|news|finance), and include_raw_content as needed. "
        )
    system_prompt += (
        "When MCP tools are available: use `lookup_docs` for organization and leave-policy questions; "
        "use `bingchuan` for 冰雪川 / Bingchuan ice cream or product-knowledge questions; "
        "use `inspect_faiss` only for debugging the document index."
    )
    agent = create_deep_agent(
        model=model,
        tools=all_tools,
        system_prompt=system_prompt,
        subagents=_build_subagents(),
        checkpointer=checkpointer,
        backend=make_memory_backend,
    )
    logger.info("Long-term memory directory (global): %s", GLOBAL_MEMORIES_DIR)
    fastapi_app.state.agent = agent
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
    raw_messages = result.get("messages") or []
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
    return ChatResponse(reply=reply)
