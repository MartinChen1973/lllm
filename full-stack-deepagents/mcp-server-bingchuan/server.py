"""
## ⬇️ Standalone stub — not used by full-stack-deepagents. The AI API (ai-api/main.py) never
## ⬇️ registers this process: Bingchuan answers come from the `bingchuan` tool on **mcp-server-rag**
## ⬇️ (port 8501, same stack as lookup_docs). Do not run this on 8501 while mcp-server-rag is up.
## ⬇️ Minimal MCP: no @mcp.tool(); tools/list is empty. Streamable HTTP at http://<host>:<port>/mcp.
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

## ⬇️ Repo-root .env (full-stack-deepagents/.env), same as backend and ai-api
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
from starlette.responses import HTMLResponse, JSONResponse

## ⬇️ Port/host from environment so the AI API can point MCP_SERVER_URL consistently
_host = os.environ.get("MCP_HOST", "127.0.0.1")
_port = int(os.environ.get("MCP_PORT", "8501"))

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


@mcp.custom_route("/openapi.json", methods=["GET"], include_in_schema=False)
async def _openapi_json(_request):
    return JSONResponse(_OPENAPI_SPEC)


@mcp.custom_route("/docs", methods=["GET"], include_in_schema=False)
async def _swagger_docs(_request):
    return HTMLResponse(_DOCS_HTML)


if __name__ == "__main__":
    asyncio.run(mcp.run_streamable_http_async())
