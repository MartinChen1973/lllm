"""
Basic configuration - Handle interrupts example

This example demonstrates how to configure human-in-the-loop workflows
using the interrupt_on parameter and handle interrupts when they occur.
"""

import uuid
from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
from langgraph.types import Command
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
from human_in_the_loop_utils import get_user_decisions

# Load environment variables from .env file
load_dotenv(find_dotenv())


# Define tools
@tool
def delete_file(path: str) -> str:
    """Delete a file from the filesystem."""
    return f"Deleted {path}"


@tool
def read_file(path: str) -> str:
    """Read a file from the filesystem."""
    return f"Contents of {path}"


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    return f"Sent email to {to} with subject '{subject}': {body[:50]}..."


# Checkpointer is REQUIRED for human-in-the-loop
checkpointer = MemorySaver()

# Basic configuration: Set up agent with interrupt_on parameter
agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[delete_file, read_file, send_email],
    interrupt_on={
        "delete_file": True,  # Default: approve, edit, reject
        "read_file": False,   # No interrupts needed
        "send_email": {"allowed_decisions": ["approve", "reject"]},  # No editing
    },
    checkpointer=checkpointer  # Required!
)

# Handle interrupts example
# Create config with thread_id for state persistence
config = {"configurable": {"thread_id": str(uuid.uuid4())}}

# Invoke the agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "Delete the file temp.txt"}]
}, config=config)

# Check if execution was interrupted
if result.get("__interrupt__"):
    # Extract interrupt information
    interrupts = result["__interrupt__"][0].value
    action_requests = interrupts["action_requests"]
    review_configs = interrupts["review_configs"]

    # Create a lookup map from tool name to review config
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}

    # Get user decisions (one per action_request, in order)
    decisions = get_user_decisions(action_requests, config_map)

    # Resume execution with decisions
    result = agent.invoke(
        Command(resume={"decisions": decisions}),
        config=config  # Must use the same config!
    )

# Process final result
print(result["messages"][-1].content)

