"""
MCP server: Bingchuan FAISS RAG (bingchuan, inspect_faiss).

Streamable HTTP at http://<host>:<port>/mcp (defaults: 127.0.0.1:8503).
Use MCP_PORT=8503 so this does not collide with mcp-server-oa (8501) or mcp-server (8502).
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
_port = int(os.environ.get("MCP_PORT", "8503"))

mcp = FastMCP(
    "bingchuan-docs",
    instructions=(
        "Internal markdown knowledge base for 冰雪川 (Bingchuan) ice cream. "
        "For flavors, allergens, retail or cold-chain policy, and product facts, call `bingchuan`. "
        "Use `inspect_faiss_bingchuan` only for debugging the Bingchuan document index. "
        "For organization or leave policy, use the separate OA MCP server."
    ),
    host=_host,
    port=_port,
)

_OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "MCP Bingchuan RAG server",
        "version": "1.0.0",
        "description": (
            "RAG-backed Bingchuan tools over local FAISS. MCP session at POST /mcp (Streamable HTTP). "
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
<html lang="en"><head><meta charset="utf-8"/><title>MCP Bingchuan server — OpenAPI</title>
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
def bingchuan(query: str) -> str:
    """Answer questions about 冰雪川 (Bingchuan) ice cream: flavors, ingredients, allergens, retail or cold-chain policy, and product facts from the knowledge base.

    Use this tool whenever the user mentions Bingchuan, 冰雪川, or ice cream product details covered by that brand corpus. Do not invent flavors; retrieve via this tool.
    """
    try:
        return answer_from_docs(query)
    except Exception as e:
        return _rag_error(e)


@mcp.tool()
def inspect_faiss_bingchuan(max_chunks: int = 80) -> str:
    """List stored FAISS chunks for the Bingchuan index (sources and text). Debugging only; not for end-user answers."""
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
