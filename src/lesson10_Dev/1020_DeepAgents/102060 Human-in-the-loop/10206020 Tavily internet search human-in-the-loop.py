"""
Tavily web search with human-in-the-loop (approve or reject before internet access).

Each proposed call to `internet_search` pauses until the user explicitly allows or
denies it; rejected calls are not executed (no Tavily request is made).
"""

import os
import uuid
from typing import Any, Literal

from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from tavily import TavilyClient

from deepagents import create_deep_agent

from human_in_the_loop_utils import get_user_decisions

load_dotenv(find_dotenv(), override=True)


def _tavily_client() -> TavilyClient:
    ## ⬇️ Same pattern as Quickstart: key from environment
    key = (os.environ.get("TAVILY_API_KEY") or "").strip()
    if not key:
        raise RuntimeError(
            "TAVILY_API_KEY is not set. Add it to .env (see repo _example.env)."
        )
    return TavilyClient(api_key=key)


@tool
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> dict[str, Any]:
    """Search the public internet via Tavily. A human must approve each call before it runs."""
    client = _tavily_client()
    return client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


research_instructions = """You are a research assistant with optional access to the live web.

## `internet_search`

Use this tool when the user wants current or external information. Each use is gated: a human reviewer must approve or reject the search before any request is sent.
"""


checkpointer = MemorySaver()  ## ⬅️ Required for human-in-the-loop

agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[internet_search],
    system_prompt=research_instructions,
    interrupt_on={ ## ⬅️ Gate outbound internet (Tavily) on explicit user consent
        "internet_search": {
            "allowed_decisions": ["approve", "reject"],
        },
    },
    checkpointer=checkpointer,
)

config = {"configurable": {"thread_id": str(uuid.uuid4())}}

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "What is LangGraph? Use a brief web search if you can.",
            }
        ]
    },
    config=config,
)

while result.get("__interrupt__"):  ## ⬅️ Handle one or more interrupt batches in this turn
    interrupts = result["__interrupt__"][0].value
    action_requests = interrupts["action_requests"]
    review_configs = interrupts["review_configs"]
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}

    print(
        "\n--- Internet access (Tavily) ---\n"
        "The agent proposes a web search. Approve to run Tavily, or reject to skip.\n"
    )
    decisions = get_user_decisions(
        action_requests,
        config_map,
        use_interactive_email_editing=False,
    )

    result = agent.invoke(
        Command(resume={"decisions": decisions}),
        config=config,
    )

print(result["messages"][-1].content)
