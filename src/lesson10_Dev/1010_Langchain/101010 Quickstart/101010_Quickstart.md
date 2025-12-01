# LangChain Quickstart (Refined)

This quickstart takes you from a simple setup to a fully functional AI agent.

## Basic Agent

```python
from langchain.agents import create_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

# Run the agent
agent.invoke({
    "messages": [
        {"role": "user", "content": "what is the weather in sf"}
    ]
})
```

## Real-World Agent

### 1. System Prompt

```python
SYSTEM_PROMPT = """You are an expert weather forecaster, who speaks in puns.

You have access to two tools:

- get_weather_for_location
- get_user_location

If a user asks you for the weather, ensure you know the location."""
```

### 2. Tools

```python
from dataclasses import dataclass
from langchain.tools import tool, ToolRuntime

@tool
def get_weather_for_location(city: str) -> str:
    return f"It's always sunny in {city}!"

@dataclass
class Context:
    user_id: str

@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    user_id = runtime.context.user_id
    return "Florida" if user_id == "1" else "SF"
```

### 3. Model Configuration

```python
from langchain.chat_models import init_chat_model

model = init_chat_model(
    "claude-sonnet-4-5-20250929",
    temperature=0.5,
    timeout=10,
    max_tokens=1000
)
```

### 4. Structured Response

```python
from dataclasses import dataclass

@dataclass
class ResponseFormat:
    punny_response: str
    weather_conditions: str | None = None
```

### 5. Memory

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
```

### 6. Create and Run Agent

```python
agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[get_user_location, get_weather_for_location],
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer
)

config = {"configurable": {"thread_id": "1"}}

response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather outside?"}]},
    config=config,
    context=Context(user_id="1")
)

print(response["structured_response"])
```

## Full Example

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver

SYSTEM_PROMPT = """You are an expert weather forecaster, who speaks in puns."""

@dataclass
class Context:
    user_id: str

@tool
def get_weather_for_location(city: str) -> str:
    return f"It's always sunny in {city}!"

@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    return "Florida" if runtime.context.user_id == "1" else "SF"

model = init_chat_model("claude-sonnet-4-5-20250929", temperature=0)
checkpointer = InMemorySaver()

@dataclass
class ResponseFormat:
    punny_response: str
    weather_conditions: str | None = None

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[get_user_location, get_weather_for_location],
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer
)

config = {"configurable": {"thread_id": "1"}}

response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather outside?"}]},
    config=config,
    context=Context(user_id="1")
)
print(response["structured_response"])
```

---

Congratulations! You now have a fully functional LangChain agent.
