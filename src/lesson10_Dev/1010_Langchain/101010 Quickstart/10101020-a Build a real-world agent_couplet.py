# Demonstrates how to create a fully functional real-world AI agent using LangChain 1.0
# Example: Couplet (对联) Generator Agent

from dataclasses import dataclass
import os
from dotenv import load_dotenv, find_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

# Load environment variables from .env file
load_dotenv(find_dotenv())

# System prompt for the couplet generator agent
SYSTEM_PROMPT = """You are an expert Chinese couplet (对联) writer. You create traditional Chinese couplets with matching upper line (上联), lower line (下联), and horizontal scroll (横批). Ensure proper tonal patterns, parallelism, and thematic coherence."""


# Context schema for passing user context to tools
@dataclass
class Context:
    user_id: str


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
    frequency_penalty=0,
    presence_penalty=0,
)

# Initialize memory checkpointer for conversation history
checkpointer = InMemorySaver()


# Structured response format
@dataclass
class ResponseFormat:
    upper_line: str  # 上联
    lower_line: str  # 下联
    horizontal_scroll: str  # 横批


# Create the agent with all components
agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[],  # No tools needed for couplet generation
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer
)

# Configuration for the conversation thread
config = {"configurable": {"thread_id": "1"}}

# Invoke the agent with a user message
response = agent.invoke(
    {"messages": [{"role": "user", "content": "请写一个龙年的对联，上联9个字"}]},
    config=config,
    context=Context(user_id="1")
)

# Print the structured response
structured = response["structured_response"]
print(f"上联: {structured.upper_line}")
print(f"下联: {structured.lower_line}")
print(f"横批: {structured.horizontal_scroll}")
