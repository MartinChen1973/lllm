"""
Tavily web search as a local tool (same pattern as lesson Quickstart).

See: src/lesson10_Dev/1020_DeepAgents/102010 Quickstart/10201010 Quickstart.py
"""

from __future__ import annotations

import os
from typing import Any, Literal

from tavily import TavilyClient


def _tavily_client() -> TavilyClient | None:
    ## ⬇️ Key is loaded in main via repo-root .env before lifespan builds the agent
    key = (os.environ.get("TAVILY_API_KEY") or "").strip()
    if not key:
        return None
    return TavilyClient(api_key=key)


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> dict[str, Any]:
    """Run a web search for the given query (Tavily). Use for current facts, news, or topics outside internal docs."""
    client = _tavily_client()
    if client is None:
        return {"error": "TAVILY_API_KEY is not set; internet_search is unavailable."}
    return client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


def get_local_tools() -> list[Any]:
    ## ⬇️ Omit the tool if no API key so the agent does not advertise a broken tool
    if _tavily_client() is None:
        return []
    return [internet_search]
