"""
Subagent interrupts - Handle interrupts from subagents example

This example demonstrates how subagents can have their own interrupt_on 
configuration that overrides the main agent's settings. When a subagent 
triggers an interrupt, the handling is the same as main agent interrupts.

Based on the documentation from: 
src/lesson10_Dev/1020_DeepAgents/102060 Human-in-the-loop/102060 Human-in-the-loop.md
"""

from langchain.tools import tool
from dotenv import load_dotenv, find_dotenv
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)



@tool
def delete_file(path: str) -> str:
    """Delete a file from the filesystem."""
    return f"Deleted {path}"


@tool
def read_file(path: str) -> str:
    """Read a file from the filesystem."""
    return f"Contents of {path}"


# Checkpointer is REQUIRED for human-in-the-loop
checkpointer = MemorySaver()

# Configure agent with subagent that has different interrupt_on settings
# Main agent: read_file is NOT available (only through subagent)
# Subagent: read_file DOES require approval (override)
agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[delete_file],  # Main agent doesn't have read_file - only subagent does
    interrupt_on={
        "delete_file": True,  # Default: approve, edit, reject
        "read_file": False,   ## ⬅️ No interrupts needed in main agent
    },
    subagents=[{
        "name": "file-manager",
        "description": "Manages file operations",
        "system_prompt": "You are a file management assistant.",
        "tools": [delete_file, read_file],
        "interrupt_on": {
            # Override: require approval for reads in this subagent
            "delete_file": True,
            "read_file": True,  ## ⬅️ Different from main agent!
        }
    }],
    checkpointer=checkpointer  # Required!
)

print("This example is just a demo configuration for a DeepAgent system and cannot be run as standalone code.")
