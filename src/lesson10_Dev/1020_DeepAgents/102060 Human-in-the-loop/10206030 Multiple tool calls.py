"""
Multiple tool calls - Handle multiple interrupts example

This example demonstrates how to handle multiple tool calls that require
human approval in a single execution flow. When an agent calls multiple
tools that require approval, all interrupts are batched together and
must be processed in order.

Based on the documentation from: 
src/lesson10_Dev/1020_DeepAgents/102060 Human-in-the-loop/102060 Human-in-the-loop.md
"""

import uuid
from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
from langgraph.types import Command
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents.middleware.todo import TodoListMiddleware
from human_in_the_loop_utils import get_user_decisions

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)



@tool
def delete_file(path: str) -> str:
    """Delete a file from the filesystem. Requires human approval."""
    return f"Deleted file: {path}"


@tool
def create_backup(path: str, backup_name: str = None) -> str:
    """Create a backup of a file. Requires human approval."""
    if backup_name is None:
        backup_name = f"{path}.backup"
    return f"Created backup: {backup_name}"


@tool  
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email. Requires human approval but no editing."""
    return f"Sent email to {to} with subject '{subject}': {body[:50]}..."


# Checkpointer is REQUIRED for human-in-the-loop
checkpointer = MemorySaver()

# Configure agent with multiple tools requiring different approval levels
agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[delete_file, create_backup, send_email],
    interrupt_on={
        "delete_file": {"allowed_decisions": ["approve", "reject"]},  # Only approve/reject
        "create_backup": {"allowed_decisions": ["approve", "reject"]},  # Only approve/reject
        "send_email": True,  # Default: approve, edit, reject (editing allowed)
    },
    # middleware=[TodoListMiddleware()],
    checkpointer=checkpointer  # Required!
)


# Create config with thread_id for state persistence
config = {"configurable": {"thread_id": str(uuid.uuid4())}}

# Invoke the agent
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Delete important.txt, create a backup of data.db, and send email to admin@example.com about the cleanup"
    }]
}, config=config)

print("------------  todos ---------------")
# print(result["todos"])  ## ⬅️ Array of todo items (empty if TodoListMiddleware not used)
print("--------------------------------")

# Check if execution was interrupted
if result.get("__interrupt__"):
    interrupts = result["__interrupt__"][0].value
    action_requests = interrupts["action_requests"]
    review_configs = interrupts["review_configs"]
    
    # Create lookup map for review configs
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}
    
    # Get user decisions (one per action_request, in order)
    decisions = get_user_decisions(action_requests, config_map)
    print(f"Decisions: {decisions}")
    
    # Resume execution with decisions
    result = agent.invoke(
        Command(resume={"decisions": decisions}),
        config=config  # Must use the same config!
    )

# Display final result
print(f"\nFinal result: {result['messages'][-1].content}")

