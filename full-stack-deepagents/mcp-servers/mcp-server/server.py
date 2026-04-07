"""
Minimal MCP server: no custom tools; tools/list returns an empty list.
Streamable HTTP at http://<host>:<port>/mcp (defaults: 127.0.0.1:8502; mcp-server-oa uses 8501, mcp-server-bingchuan 8503).
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

## ⬇️ Repo-root .env (full-stack-deepagents/.env), same as backend and ai-api
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)
from starlette.responses import HTMLResponse, JSONResponse, Response

## ⬇️ Port/host from environment so the AI API can point MCP_SERVER_URL consistently
_host = os.environ.get("MCP_HOST", "127.0.0.1")
_port = int(os.environ.get("MCP_PORT", "8502"))

mcp = FastMCP(
    "empty-tools-demo",
    instructions="Demonstration MCP server with no registered tools.",
    host=_host,
    port=_port,
)

## ⬇️ Minimal OpenAPI + Swagger UI for operators (MCP itself is POST /mcp, not fully described here)
_OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "MCP demo server",
        "version": "1.0.0",
        "description": (
            "Auxiliary documentation for this process. "
            "The Model Context Protocol is exposed at POST /mcp (Streamable HTTP); "
            "use an MCP client to call tools/list and related methods."
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
<html lang="en"><head><meta charset="utf-8"/><title>MCP server — OpenAPI</title>
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
    asyncio.run(mcp.run_streamable_http_async())
