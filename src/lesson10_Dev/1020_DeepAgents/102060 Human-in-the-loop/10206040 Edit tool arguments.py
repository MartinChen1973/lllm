"""
Edit tool arguments - Unified approach for handling 1 to N actions with editing support

This example demonstrates how to use get_user_decisions which can:
1. Handle single or multiple action requests (1 to N)
2. Support interactive editing for email arguments when "edit" is selected
3. Use JSON-based editing for other tools

Based on the documentation from: 
src/lesson10_Dev/1020_DeepAgents/102060 Human-in-the-loop/102060 Human-in-the-loop.md
"""

import uuid
from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
from langgraph.types import Command
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
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
    """Send an email. Supports interactive editing."""
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
    checkpointer=checkpointer  # Required!
)

# Create config with thread_id for state persistence
config = {"configurable": {"thread_id": str(uuid.uuid4())}}

# Test different scenarios by uncommenting one of these:
# Scenario 1: Single action (send_email only) - can edit interactively
prompt = "Send an email to admin@example.com with subject 'Test' and body 'This is a test message.'"

# Scenario 2: Multiple actions - interactive editing for send_email, approve/reject for others
# prompt = "Delete important.txt, create a backup of data.db, and send email to admin@example.com about the cleanup"

# Invoke the agent
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": prompt
    }]
}, config=config)

# Check if execution was interrupted
if result.get("__interrupt__"):
    interrupts = result["__interrupt__"][0].value
    action_requests = interrupts["action_requests"]
    review_configs = interrupts["review_configs"]
    
    # Create lookup map for review configs
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}
    
    # Get user decisions - handles 1 to N actions with intelligent editing
    # For send_email: uses interactive UI for editing (to, subject, body)
    # For other tools: uses JSON-based editing
    decisions = get_user_decisions(action_requests, config_map)
    print(f"\nDecisions made: {decisions}")
    
    # Resume execution with decisions
    result = agent.invoke(
        Command(resume={"decisions": decisions}),
        config=config  # Must use the same config!
    )
    
    # Check if there are more interrupts (shouldn't happen, but just in case)
    if result.get("__interrupt__"):
        print("\n⚠ Warning: Execution was interrupted again after resuming!")
        print("This means the agent needs more decisions or there's an issue with the decisions format.")
        interrupts = result["__interrupt__"][0].value
        action_requests = interrupts.get("action_requests", [])
        print(f"Number of pending actions: {len(action_requests)}")
        if action_requests:
            print("Pending actions:")
            for action in action_requests:
                print(f"  - {action['name']}: {action['args']}")
    else:
        # Verify decisions were executed by checking tool results
        print("\n✓ Execution completed without further interrupts")
        if 'messages' in result:
            # Check if tool was executed with edited arguments
            for msg in result.get("messages", []):
                if hasattr(msg, 'name') and msg.name == 'send_email':
                    print("✓ Tool execution found in messages - decisions were executed")
                    break

# Display final result and verify edited arguments were applied
if result and 'messages' in result and len(result['messages']) > 0:
    # Find the tool result message to verify edited arguments were used
    tool_result = None
    for msg in result.get("messages", []):
        # Look for the tool result message (has name attribute matching the tool)
        if hasattr(msg, 'name') and msg.name == 'send_email' and hasattr(msg, 'content'):
            tool_result = msg.content
            break
    
    # Display the final result based on the actual tool execution
    if tool_result:
        print(f"\nFinal result: {tool_result}")
    else:
        # Fallback to last message if no tool result found
        last_message = result['messages'][-1]
        if hasattr(last_message, 'content') and last_message.content:
            print(f"\nFinal result: {last_message.content}")
        else:
            print("\nFinal result: (No content in last message)")
            print(f"Last message type: {type(last_message).__name__}")
            if hasattr(last_message, 'role'):
                print(f"Last message role: {last_message.role}")
else:
    print("\n⚠ Error: No messages in result")
    print(f"Result keys: {list(result.keys()) if result else 'None'}")

## ⚠️ Important!
# If you edit the "to" email address with an invalid format (e.g., just "abc" instead of a valid email like "abc@something.com"),
# the agent will be interrupted again and ask for a correct email.
# This is expected to ensure argument validation happens before sending emails.
