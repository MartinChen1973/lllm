# 1. 演示一个最简单的无记忆、无工具的智能体。

from dotenv import load_dotenv, find_dotenv
from langgraph.prebuilt import create_react_agent

load_dotenv(find_dotenv())


def get_weather(city: str) -> str:  
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_react_agent(
    model="openai:gpt-4o-mini",  
    tools=[get_weather],  
    prompt="You are a helpful assistant"  
)

# Run the agent
response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)

agent.get_graph().draw_mermaid_png()

print("Full Response: ===============")
import json
print(json.dumps(response, indent=2, ensure_ascii=False, default=str))
print("\n" + "="*50 + "\n")
