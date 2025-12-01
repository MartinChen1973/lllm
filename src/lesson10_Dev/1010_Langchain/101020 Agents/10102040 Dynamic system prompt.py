# Demonstrates how to use dynamic system prompts

from pprint import pprint
from typing import TypedDict

from dotenv import load_dotenv, find_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

# Load environment variables from .env file within the current working directory or parent directories
load_dotenv(find_dotenv())


class Context(TypedDict):
    """Context schema for runtime context."""
    user_role: str


@dynamic_prompt
def user_role_prompt(request: ModelRequest) -> str:
    """Generate system prompt based on user role."""
    # Get user_role from runtime context
    user_role = request.runtime.context.get("user_role", "user")
    base_prompt = "You are a helpful assistant."

    if user_role == "expert":
        return f"{base_prompt} Provide detailed technical responses."
    elif user_role == "beginner":
        return f"{base_prompt} Explain concepts simply and avoid jargon."

    return base_prompt


# Create agent with dynamic system prompt middleware
agent = create_agent(
    model="gpt-4o-mini",
    tools=[],  # Empty tool list - agent will only use LLM
    middleware=[user_role_prompt],  # Dynamic system prompt middleware
    context_schema=Context,
)

# The system prompt will be set dynamically based on context
# Swap between "expert" and "beginner" by commenting/uncommenting the context lines below
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Explain machine learning"}]},
    # context={"user_role": "expert"},  # user_role is set to "expert" here
    context={"user_role": "beginner"},  # user_role is set to "beginner" here
)

# Print the response with pretty print
pprint(result)
