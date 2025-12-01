"""
Edit tool arguments - Handle editing tool arguments example

This example demonstrates how to edit tool arguments when "edit" is in the
allowed decisions. It provides a simple text-based UI for modifying individual
tool arguments before execution.

Based on the documentation from: 
src/lesson10_Dev/1020_DeepAgents/102060 Human-in-the-loop/102060 Human-in-the-loop.md
"""

import uuid
from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
from langgraph.types import Command
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables from .env file
load_dotenv(find_dotenv())


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    return f"Successfully sent email to {to} with subject '{subject}' and body '{body}'."


def edit_argument(current_value: str, argument_name: str) -> str:
    """
    Simple text-based UI for editing a single argument.
    
    Args:
        current_value: The current value of the argument
        argument_name: The name of the argument being edited
    
    Returns:
        The new value (or original if user pressed Enter without changes)
    """
    print(f"Current {argument_name}: {current_value}")
    new_value = input("Modify to (press Enter to keep unchanged): ").strip()
    
    if not new_value:
        return current_value
    
    return new_value


def get_user_decision_with_editing(action_req, review_cfg):
    """
    Get user decision for a single action request, with support for editing.
    
    Args:
        action_req: The action request that needs approval
        review_cfg: The review configuration for this action
    
    Returns:
        A decision dictionary (approve, edit, or reject)
    """
    allowed_decisions = review_cfg['allowed_decisions']
    
    print(f"\n--- Tool: {action_req['name']} ---")
    print(f"Arguments: {action_req['args']}")
    print(f"\nAllowed decisions: {', '.join(allowed_decisions)}")
    
    # Display numbered options
    for idx, decision_type in enumerate(allowed_decisions, 1):
        print(f"  {idx}. {decision_type}")
    
    # Get user choice
    while True:
        try:
            choice = input(f"\nSelect decision (1-{len(allowed_decisions)}): ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(allowed_decisions):
                selected_decision = allowed_decisions[choice_num - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(allowed_decisions)}")
        except ValueError:
            print("Please enter a valid number")
    
    # Handle edit decision
    if selected_decision == "edit":
        original_args = action_req['args']
        # Create a fresh dictionary with all original arguments, then update with edited values
        edited_args = dict(original_args)
        
        # Edit each argument individually: to, subject (title), and body
        print("\n--- Editing Email Arguments ---")
        
        # Edit 'to' (recipient)
        if 'to' in original_args:
            edited_value = edit_argument(str(original_args['to']), 'to (recipient)')
            edited_args['to'] = edited_value
        
        # Edit 'subject' (title)
        if 'subject' in original_args:
            edited_value = edit_argument(str(original_args['subject']), 'subject (title)')
            edited_args['subject'] = edited_value
        
        # Edit 'body'
        if 'body' in original_args:
            edited_value = edit_argument(str(original_args['body']), 'body')
            edited_args['body'] = edited_value
        
        edit_decision = {
            "type": "edit",
            "edited_action": {
                "name": action_req["name"],
                "args": edited_args
            }
        }
        
        return edit_decision
    
    # Handle approve or reject
    return {"type": selected_decision}


# Checkpointer is REQUIRED for human-in-the-loop
checkpointer = MemorySaver()

# Configure agent with send_email tool that allows editing
agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[send_email],
    interrupt_on={
        "send_email": {"allowed_decisions": ["approve", "edit", "reject"]},  # Editing allowed
    },
    checkpointer=checkpointer  # Required!
)

# Create config with thread_id for state persistence
config = {"configurable": {"thread_id": str(uuid.uuid4())}}

# Invoke the agent
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Send an email to everyone@company.com with subject 'Important Update' and body 'Please review the new policy.'"
    }]
}, config=config)

# Check if execution was interrupted
if result.get("__interrupt__"):
    interrupts = result["__interrupt__"][0].value
    action_requests = interrupts["action_requests"]
    review_configs = interrupts["review_configs"]
    
    # Create a lookup map from tool name to review config
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}
    
    # Get user decision (with editing support)
    action_request = action_requests[0]
    review_config = config_map[action_request["name"]]
    decision = get_user_decision_with_editing(action_request, review_config)
    
    # Resume execution with decision
    try:
        result = agent.invoke(
            Command(resume={"decisions": [decision]}),
            config=config  # Must use the same config!
        )
        
        # Find and display the actual tool result
        tool_result = None
        for msg in result.get("messages", []):
            # Look for the tool result message (has name attribute matching the tool)
            if hasattr(msg, 'name') and msg.name == 'send_email' and hasattr(msg, 'content'):
                tool_result = msg.content
                break
        
        # Display the actual tool result (shows what was really executed)
        if tool_result:
            print(f"\n{'='*60}")
            print("✓ EMAIL SENT SUCCESSFULLY:")
            print(f"{'='*60}")
            print(f"  {tool_result}")
            print(f"{'='*60}")
        else:
            print(f"\nFinal result: {result['messages'][-1].content}")
    except Exception as e:
        print(f"\n⚠ Error occurred: {type(e).__name__}: {str(e)[:200]}")
else:
    # No interrupt - show final result
    print(f"\nFinal result: {result['messages'][-1].content}")

