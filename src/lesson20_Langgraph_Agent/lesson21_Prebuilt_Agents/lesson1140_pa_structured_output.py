# 1. 演示一个最简单的无记忆、无工具的智能体。

from dotenv import load_dotenv, find_dotenv
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

load_dotenv(find_dotenv())

def get_weather(_city: str) -> str:
    """Get weather for a given city."""
    return "It's always sunny!"

# 增加一个结构化输出 =============================================
class WeatherResponse(BaseModel):
    """Weather information response."""
    city: str
    conditions: str

agent = create_react_agent(
    model="openai:gpt-4o-mini",  
    tools=[get_weather],  
    response_format=WeatherResponse
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

# Extract structured output if available
if "output" in response and hasattr(response["output"], "city") and hasattr(response["output"], "conditions"):
    weather_info = response["output"]
    print("Structured Weather Info:")
    print(f"City: {weather_info.city}")
    print(f"Conditions: {weather_info.conditions}")
else:
    print("No structured output found in response")
