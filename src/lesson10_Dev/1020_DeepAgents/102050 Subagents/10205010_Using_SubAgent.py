import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv())

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

research_subagent = { ## ⬅️ Define a subagent as a dictionary
    "name": "research-agent",
    "description": "Used to research more in depth questions with the internet search tool",
    "system_prompt": "You are a great researcher and you are using the internet search tool to research more in depth questions",
    "tools": [internet_search],
    # Model defaults to main agent model (gpt-4o-mini)
}

subagents = [research_subagent]

agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    subagents=subagents
)

# Run the agent
# result = agent.invoke({"messages": [{"role": "user", "content": "What is the weather in Beijing?"}]})
result = agent.invoke({
    "messages": [
        {"role": "user", "content": "Hey, what's up in the world of AI for November 2025? Any interesting news?"}
    ]
})

# Print the agent's response
print("Agent Response:")
print("-" * 60)
print(result["messages"][-1].content)
print("-" * 60)