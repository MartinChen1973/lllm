# 1. 演示一个最简单的无记忆、无工具的智能体。

from dotenv import load_dotenv, find_dotenv
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(find_dotenv())

def get_weather(city: str) -> str:  
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

# =============================================
checkpointer = MemorySaver()

agent = create_react_agent(
    model="openai:gpt-4o-mini",  
    tools=[get_weather],  
    prompt="You are a helpful assistant",
    checkpointer=checkpointer
)
# --------------------------------------------

# Run the agent
config = {"configurable": {"thread_id": "1"}}
sf_response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]},
    config
)
ny_response = agent.invoke(
    {"messages": [{"role": "user", "content": "what about new york?"}]},
    config
)

print("SF Response: ===============")
import json
print(json.dumps(sf_response, indent=2, ensure_ascii=False, default=str))
print("\n" + "="*50 + "\n")

print("NY Response: ===============")
print(json.dumps(ny_response, indent=2, ensure_ascii=False, default=str))
print("\n" + "="*50 + "\n")
