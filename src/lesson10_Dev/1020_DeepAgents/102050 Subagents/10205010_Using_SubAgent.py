import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)


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

def get_weather_for_location(location: str) -> str:
    """Get the weather for a given location (always returns '此地晴天。')."""
    return "此地晴天。"


research_subagent = { ## ⬅️ Define a subagent as a dictionary
    "name": "research-agent",
    "description": "Used to research more in depth questions with the internet search tool",
    "system_prompt": "You are a great researcher and you are using the internet search tool to research more in depth questions",
    "tools": [internet_search, get_weather_for_location],
    # Model defaults to main agent model (gpt-4o-mini)
}

weather_subagent = {  # 定义一个可以 getWeather 的子智能体
    "name": "weather-agent",
    "description": "用于获取指定地点天气信息的子智能体",
    "system_prompt": "你是一名天气助手，请准确地为用户查询和解答有关天气的问题。",
    "tools": [get_weather_for_location],
    # Model 默认为主智能体的模型 (gpt-4o-mini)
}

subagents = [research_subagent, weather_subagent]

# subagents = load_subagents(subagents)
# subagents = find_subagents(subagents, "http://192.168.1.100:8000/subagents/list")  ## ⬅️ Requires custom implementation


agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    subagents=subagents
)

# Run the agent
# result = agent.invoke({"messages": [{"role": "user", "content": "What is the weather in Beijing?"}]})
result = agent.invoke({
    "messages": [
        # {"role": "user", "content": "Hey, what's up in the world of AI for March 2026? Any interesting news?"},
        {"role": "user", "content": "What is the weather in Beijing today?"}
    ]
})

# Print the agent's response
print("Agent Response:")
print("-" * 60)
print(result["messages"][-1].content)
print("-" * 60)