"""
FastAPI chat endpoint backed by a deep agent with subagents (no external MCP tools).
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
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from deepagents import create_deep_agent

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


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str


logger = logging.getLogger(__name__)


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
    ## ⬇️ Deep agent with no external tools (MCP can be added later)
    model = init_chat_model(DEFAULT_MODEL)
    checkpointer = MemorySaver()
    system_prompt = (
        "You are a helpful assistant. You may delegate to subagents using the task tool "
        "when their expertise fits the user request."
    )
    agent = create_deep_agent(
        model=model,
        tools=[],
        system_prompt=system_prompt,
        subagents=_build_subagents(),
        checkpointer=checkpointer,
    )
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

    def _invoke() -> dict[str, Any]:
        return agent.invoke(
            {"messages": [{"role": "user", "content": body.message}]},
            config,
        )

    t0 = time.perf_counter()
    try:
        result = await asyncio.to_thread(_invoke)
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
