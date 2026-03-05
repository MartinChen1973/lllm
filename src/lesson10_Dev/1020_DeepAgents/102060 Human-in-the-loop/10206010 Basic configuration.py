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

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)


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
checkpointer = MemorySaver() ## ⬅️ Attention: Checkpointer is required for human-in-the-loop

# Basic configuration: Set up agent with interrupt_on parameter
agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[delete_file, read_file, send_email],
    interrupt_on={ ## ⬅️ Define which tools require human-in-the-loop
        "delete_file": True,  ## ⬅️ Default: approve, edit, reject
        "read_file": False,   ## ⬅️ No interrupts needed
        "send_email": {"allowed_decisions": ["approve", "reject"]},  ## ⬅️ No editing
    },
    checkpointer=checkpointer  # Required!
)

# Handle interrupts example
# Create config with thread_id for state persistence
config = {"configurable": {"thread_id": str(uuid.uuid4())}}

# Invoke the agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "Delete the file temp.txt"}] ## ⬅️ Requires human-in-the-loop
    # "messages": [{"role": "user", "content": "Read the file temp.txt"}] ## ⬅️ Requires NO human-in-the-loop
}, config=config)

# Check if execution was interrupted
if result.get("__interrupt__"):
    # Extract interrupt information
    interrupts = result["__interrupt__"][0].value
    action_requests = interrupts["action_requests"]
    review_configs = interrupts["review_configs"]

    # Create a lookup map from tool name to review config
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}

    # Display the pending actions to the user
    for action in action_requests:
        review_config = config_map[action["name"]]
        print(f"Tool: {action['name']}")
        print(f"Arguments: {action['args']}")
        print(f"Allowed decisions: {review_config['allowed_decisions']}")

    # Get user decisions (one per action_request, in order)
    decisions = [ 
        {"type": "approve"}  ## ⬅️ Simulate user decision to approve the deletion
    ]

    # Resume execution with decisions
    result = agent.invoke(
        Command(resume={"decisions": decisions}),
        config=config  # Must use the same config!
    )

# Process final result
print(result["messages"][-1].content)
