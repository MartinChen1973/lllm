"""
MCP server: OA FAISS RAG (lookup_docs, inspect_faiss).

Streamable HTTP at http://<host>:<port>/mcp (defaults: 127.0.0.1:8501).
Build the index first: python build_faiss_index.py
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.responses import HTMLResponse, JSONResponse, Response

from rag_engine import answer_from_docs, inspect_faiss_text

## ⬇️ Repo-root .env (full-stack-deepagents/.env)
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)

_host = os.environ.get("MCP_HOST", "127.0.0.1")
_port = int(os.environ.get("MCP_PORT", "8501"))

mcp = FastMCP(
    "oa-docs",
    instructions=(
        "Internal markdown knowledge base for organization structure and leave policy. "
        "For departments, reporting lines, sick leave approval, or HR/org topics, call `lookup_docs` first. "
        "Use `inspect_faiss_oa` only for debugging the OA document index. "
        "For 冰雪川 / Bingchuan ice cream, use the separate bingchuan MCP server."
    ),
    host=_host,
    port=_port,
)

_OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "MCP OA RAG server",
        "version": "1.0.0",
        "description": (
            "RAG-backed OA tools over local FAISS. MCP session at POST /mcp (Streamable HTTP). "
            "Run build_faiss_index.py before first use."
        ),
    },
    "paths": {
        "/mcp": {
            "post": {
                "summary": "MCP Streamable HTTP",
                "description": "Session traffic for the Model Context Protocol.",
                "responses": {"200": {"description": "Protocol response"}},
            }
        }
    },
}

_DOCS_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>MCP OA server — OpenAPI</title>
<link rel="icon" href="/favicon.ico" type="image/x-icon"/>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"/>
<style>body{margin:0}</style></head><body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
<script>
window.onload=function(){
  window.ui = SwaggerUIBundle({
    url: '/openapi.json',
    dom_id: '#swagger-ui',
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
    layout: 'StandaloneLayout'
  });
};
</script>
</body></html>"""

_FAVICON_ICO_CACHE: bytes | None = None


def _stack_assets_favicon_ico() -> bytes:
    ## ⬇️ Shared with other FastMCP stacks under full-stack-deepagents/assets/
    global _FAVICON_ICO_CACHE
    if _FAVICON_ICO_CACHE is None:
        _FAVICON_ICO_CACHE = (
            Path(__file__).resolve().parents[2] / "assets" / "favicon.ico"
        ).read_bytes()
    return _FAVICON_ICO_CACHE


def _rag_error(exc: BaseException) -> str:
    return f"[rag error] {exc!s}"


@mcp.tool()
def lookup_docs(query: str) -> str:
    """Search the OA document knowledge base for organization structure, leave policy, and other indexed internal docs.

    Use this first for questions about departments, reporting lines, sick leave approval, or general HR/org topics.
    """
    try:
        return answer_from_docs(query)
    except Exception as e:
        return _rag_error(e)


@mcp.tool()
def inspect_faiss_oa(max_chunks: int = 80) -> str:
    """List stored FAISS chunks for the OA index (sources and text). Debugging only; not for end-user answers."""
    try:
        cap = max(1, min(max_chunks, 500))
        return inspect_faiss_text(max_chunks=cap)
    except Exception as e:
        return _rag_error(e)


@mcp.custom_route("/openapi.json", methods=["GET"], include_in_schema=False)
async def _openapi_json(_request):
    return JSONResponse(_OPENAPI_SPEC)


@mcp.custom_route("/docs", methods=["GET"], include_in_schema=False)
async def _swagger_docs(_request):
    return HTMLResponse(_DOCS_HTML)


@mcp.custom_route("/favicon.ico", methods=["GET"], include_in_schema=False)
async def _favicon(_request):
    ## ⬇️ Browsers request this with /docs; serve real ICO to avoid 404 log noise
    return Response(
        content=_stack_assets_favicon_ico(),
        media_type="image/x-icon",
    )


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    from rag_engine import start_docs_watchdog_background, sync_docs_to_index_at_startup

    try:
        sync_docs_to_index_at_startup()
    except Exception:
        logging.exception("RAG startup sync failed; continuing.")
    start_docs_watchdog_background()
    asyncio.run(mcp.run_streamable_http_async())
