# Demonstrates how to create a basic AI agent using LangChain 1.0

import os
from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.agents import create_agent

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)



def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


# Create a basic agent with a simple tool
agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

# Run the agent
response = agent.invoke({
    "messages": [
        {"role": "user", "content": "what is the weather in sf"}
    ]
})



# Print the response with pretty print
pprint(response)
