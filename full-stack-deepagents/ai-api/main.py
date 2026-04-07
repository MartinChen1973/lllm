"""
FastAPI chat endpoint backed by a deep agent with subagents and optional MCP tools.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
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
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend

from tools.internet_search import get_local_tools

## ⬇️ Repo-root .env (full-stack-deepagents/.env)
from dotenv import find_dotenv
load_dotenv(find_dotenv(), override=True)
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
## ⬇️ LangGraph thread checkpoints (conversation state per session_id); override with CHECKPOINT_DB_PATH
CHECKPOINT_DB_PATH = Path(
    os.environ.get("CHECKPOINT_DB_PATH", str(STORAGE_DIR / "checkpoints.sqlite"))
)
## ⬇️ Optional JSON list of MCP servers; when present and non-empty, overrides env-based URLs until cleared via API
MCP_CONFIG_PATH = STORAGE_DIR / "mcp_config.json"

_MCP_SERVER_ID_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")


def _ensure_memories_dir(memories_dir: Path) -> None:
    ## ⬇️ Only create the folder — do not seed profile/preferences: `write_file` refuses to overwrite existing files
    memories_dir.mkdir(parents=True, exist_ok=True)


def _ensure_storage_dir_for_db(db_path: Path) -> None:
    ## ⬇️ SQLite file path must live in an existing directory
    db_path.parent.mkdir(parents=True, exist_ok=True)


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
    error: str | None = None
    ## ⬇️ Declared HTTP headers for Streamable HTTP (empty when the active config comes from environment variables only)
    headers: dict[str, str] = Field(default_factory=dict)


class McpSettingsResponse(BaseModel):
    source: Literal["file", "environment"]
    servers: list[McpServerStatusOut]
    total_tools: int
    configured_servers: int
    connected_servers: int


@dataclass(frozen=True)
class McpServerLoadDetail:
    tool_count: int
    connected: bool
    error: str | None


@dataclass
class McpToolsLoadOutcome:
    tools: list[Any]
    per_server: dict[str, McpServerLoadDetail]


logger = logging.getLogger(__name__)


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


def _resolve_mcp_connections() -> tuple[dict[str, dict[str, Any]], Literal["file", "environment"]]:
    ## ⬇️ Non-empty saved list overrides environment; empty/missing file uses .env defaults
    entries = _read_mcp_config_servers_from_disk()
    if entries:
        conns: dict[str, dict[str, Any]] = {}
        for s in entries:
            conns[s.id] = _http_mcp_connection(s.url, s.headers or None)
        return conns, "file"
    return _mcp_connections_from_env(), "environment"


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
        return McpToolsLoadOutcome(tools=[], per_server={})
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
    return McpToolsLoadOutcome(tools=out, per_server=per)


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


def _compose_agent_system_prompt(local_tools: list[Any], mcp_tools: list[Any]) -> str:
    ## ⬇️ Matches prior behaviour: OA / Bingchuan hints only when any MCP tool is registered
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
    if mcp_tools:
        system_prompt += (
            "When MCP tools are available: use `lookup_docs` for organization and leave-policy questions "
            "(OA corpus); use `bingchuan` for 冰雪川 / Bingchuan ice cream or product-knowledge questions; "
            "use `inspect_faiss_oa` or `inspect_faiss_bingchuan` only for debugging the respective FAISS indexes."
        )
    return system_prompt


def _mcp_settings_response_from_load(
    connections: dict[str, dict[str, Any]],
    source: Literal["file", "environment"],
    outcome: McpToolsLoadOutcome,
) -> McpSettingsResponse:
    servers: list[McpServerStatusOut] = []
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
                error=d.error,
                headers=hdrs,
            )
        )
    total_tools = sum(s.tool_count for s in servers)
    connected_servers = sum(1 for s in servers if s.connected)
    return McpSettingsResponse(
        source=source,
        servers=servers,
        total_tools=total_tools,
        configured_servers=len(servers),
        connected_servers=connected_servers,
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
    connections, source = _resolve_mcp_connections()
    outcome = await _load_mcp_tools_with_retry(connections)
    mcp_tools = outcome.tools
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
    system_prompt = _compose_agent_system_prompt(local_tools, mcp_tools)
    agent = create_deep_agent(
        model=model,
        tools=all_tools,
        system_prompt=system_prompt,
        subagents=_build_subagents(),
        checkpointer=checkpointer,
        backend=make_memory_backend,
    )
    fastapi_app.state.agent = agent
    resp = _mcp_settings_response_from_load(connections, source, outcome)
    fastapi_app.state.mcp_settings_response = resp
    logger.info(
        "MCP summary: source=%s total_tools=%s connected_servers=%s/%s",
        source,
        resp.total_tools,
        resp.connected_servers,
        resp.configured_servers,
    )
    return resp


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    model = init_chat_model(DEFAULT_MODEL)
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
