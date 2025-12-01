# Demonstrates how to create a fully functional real-world AI agent using LangChain 1.0

from dataclasses import dataclass
import os
from dotenv import load_dotenv, find_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver

# Load environment variables from .env file
load_dotenv(find_dotenv())

# System prompt for the weather forecaster agent
SYSTEM_PROMPT = """You are an expert weather forecaster, who speaks in puns."""


# Context schema for passing user context to tools
@dataclass
class Context:
    user_id: str


# Tool: Get weather for a specific location
@tool
def get_weather_for_location(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


# Tool: Get user's location based on their user_id
@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """Get the location for the current user."""
    return "Florida" if runtime.context.user_id == "1" else "SF"


# Initialize the chat model
model = init_chat_model(
    "gpt-4o-mini",
    temperature=0,
    timeout=10,
    max_tokens=1000,
    max_retries=3,
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE"),
    organization=os.getenv("OPENAI_ORG_ID"),
    top_p=1,
    top_k=40,
    frequency_penalty=0,
    presence_penalty=0,
    logit_bias={},
    logprobs=None,
    logprobs_format=None,
    logprobs_format_type=None,
    logprobs_format_type_format=None,
)

# Initialize memory checkpointer for conversation history
checkpointer = InMemorySaver()


# Structured response format
@dataclass
class ResponseFormat:
    punny_response: str
    weather_conditions: str | None = None


# Create the agent with all components
agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[get_user_location, get_weather_for_location],
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer
)

# Configuration for the conversation thread
config = {"configurable": {"thread_id": "1"}}

# Invoke the agent with a user message
response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather outside?"}]},
    config=config,
    context=Context(user_id="1")
)

# Print the structured response
print(response["structured_response"])
