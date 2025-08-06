# 1. 演示一个最简单的无记忆、无工具的智能体。

from dotenv import load_dotenv, find_dotenv
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt.chat_agent_executor import AgentState

load_dotenv(find_dotenv())

def get_weather(city: str) -> str:  
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

model = init_chat_model("openai:gpt-4o-mini", temperature=0.0)

# 基于用户的自定义提示词 ====================================
def prompt(state: AgentState, config: RunnableConfig) -> list[AnyMessage]:  
    user_name = config["configurable"].get("user_name")
    system_msg = f"You are a helpful assistant. Always warmly address the user as {user_name}."
    return [{"role": "system", "content": system_msg}] + state["messages"]

configurable = {"user_name": "Martin"}
# ---------------------------------------------

agent = create_react_agent(
    model=model,
    tools=[get_weather],  
    prompt=prompt
)

# Run the agent
response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]},
    config=configurable
)

print("Full Response: ===============")
import json
print(json.dumps(response, indent=2, ensure_ascii=False, default=str))
print("\n" + "="*50 + "\n")
