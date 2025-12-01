# Demonstrates how to use tool error handling middleware

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.tools import tool
from langchain_core.messages import ToolMessage

# Load environment variables from .env file
load_dotenv(find_dotenv())


@tool
def divide_numbers(a: float, b: float) -> float:
    """Divide two numbers. This tool can fail if b is zero."""
    if b == 0:
        raise ValueError("division by zero")
    return a / b


@wrap_tool_call
def handle_tool_errors(request, handler):
    """Handle tool execution errors with custom messages."""
    try:
        return handler(request)
    except Exception as e:
        # Return a custom error message to the model
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"],
        )


# Create agent with tool error handling middleware
agent = create_agent(
    model="gpt-4o-mini",
    tools=[divide_numbers],
    middleware=[handle_tool_errors],  ## ⬅️ Tool error handling middleware
)

# Run the agent with a query that will trigger a tool error
response = agent.invoke({
    "messages": [
        {"role": "user", "content": "Divide 10 by 0"},  ## ⬅️ This will trigger a division by zero error
    ]
})

# Print the response with pretty print
pprint(response)

