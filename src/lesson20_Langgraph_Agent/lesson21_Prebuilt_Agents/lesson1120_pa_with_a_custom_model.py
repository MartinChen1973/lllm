# 1. 演示一个最简单的无记忆、无工具的智能体。

from dotenv import load_dotenv, find_dotenv
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model

load_dotenv(find_dotenv())


def get_weather(city: str) -> str:  
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

# =============================================
model = init_chat_model("openai:gpt-4o-mini", temperature=0.0)

agent = create_react_agent(
    model=model,  
    tools=[get_weather],  
    prompt="You are a helpful assistant"  
)
# ---------------------------------------------

# Run the agent
response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)

print("Full Response: ===============")
import json
print(json.dumps(response, indent=2, ensure_ascii=False, default=str))
print("\n" + "="*50 + "\n")
