# Demonstrates how to create an agent with dynamic model selection

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.tools import tool

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)



@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"


@tool
def get_weather(location: str) -> str:
    """Get weather information for a location."""
    return f"Weather in {location}: Sunny, 72°F"


# Define basic and advanced models
basic_model = ChatOpenAI(model="gpt-4o-mini")
advanced_model = ChatOpenAI(model="gpt-4o")


@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    """Choose model based on conversation complexity."""
    message_count = len(request.state["messages"])

    if message_count > 2:
        # Use an advanced model for longer conversations
        model = advanced_model
    else:
        model = basic_model

    request.model = model
    return handler(request)


# Create agent with dynamic model selection middleware
agent = create_agent(
    model=basic_model,  # Default model
    tools=[search, get_weather],
    middleware=[dynamic_model_selection],  ## ⬅️ Dynamic model selection middleware
)

# Run the agent
response = agent.invoke({
    "messages": [
        {"role": "user", "content": "Hello?"},  ## ⬅️ Only one message, use basic model
        {"role": "assistant", "content": "Hello! How can I help you today?"},
        {"role": "user", "content": "What's the weather in San Francisco?"},  ## ⬅️ > 2 messages, use advanced model
    ]
})

# Print the response with pretty print
pprint(response)

