"""
Use case: Self-improving instructions with list-based preference storage

This example demonstrates how an agent can update its own instructions based on user feedback.
The agent maintains a persistent instructions file at /memories/instructions.txt that accumulates
user preferences and feedback over time, helping the agent improve its behavior across conversations.

IMPROVEMENT: This version uses an unordered list format to prevent preference loss during summarization.
Preferences are stored as list items and are never removed unless they conflict with new preferences.

Based on the documentation from:
src/lesson10_Dev/1020_DeepAgents/102070 Long-term memory/102070 Long-term memory.md
"""

import uuid
from dotenv import load_dotenv, find_dotenv
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)


# Checkpointer is required for state persistence
checkpointer = MemorySaver()

## ⬇️ Key difference: Unordered list format to prevent preference loss during summarization between this file and the basic version
SYSTEM_PROMPT = """You have a file at /memories/instructions.txt that stores user preferences
    and instructions in an unordered list format.

    CRITICAL RULES FOR MANAGING /memories/instructions.txt:
    
    1. FORMAT: Always store preferences as an unordered list using bullet points (- or *).
       Each preference should be a separate list item on its own line.
    
    2. MANDATORY UPDATE PROCEDURE - Follow these steps EXACTLY when updating the file:
       
       STEP 1: FIRST, read the current contents of /memories/instructions.txt using read_file.
       
       STEP 2: Copy ALL existing list items from the file. Do NOT skip any items.
       
       STEP 3: Add the new preference as a NEW list item at the end of the list.
       
       STEP 4: When using edit_file, you MUST include ALL existing items PLUS the new item.
              NEVER write only the new item. NEVER summarize or consolidate existing items.
       
       EXAMPLE OF CORRECT UPDATE:
       If the file currently contains:
       - Always format code with proper indentation and comments
       - Prefer detailed explanations
       
       And user says "I prefer type hints", the updated file MUST be:
       - Always format code with proper indentation and comments
       - Prefer detailed explanations
       - Always use type hints in Python code examples
       
       EXAMPLE OF INCORRECT UPDATE (DO NOT DO THIS):
       - Always use type hints in Python code examples  ❌ (missing previous items)
    
    3. NEVER REMOVE: You must NEVER remove, delete, or omit existing list items during
       updates. Every single existing preference must be preserved in the updated file.
    
    4. CONFLICT RESOLUTION: Only remove a list item if a new preference explicitly
       contradicts it (e.g., "I prefer dark mode" conflicts with "I prefer light mode").
       In such cases, replace ONLY the conflicting item, but keep all other items.
    
    5. ENHANCEMENT: If a user provides more details about an existing preference, you may
       update that specific item, but you must still preserve ALL other existing items.
    
    6. READ FIRST: At the start of each conversation, read /memories/instructions.txt to
       understand existing user preferences before responding.
    
    7. VERIFICATION: After updating, verify that all previous items are still present.
       Count the items: if the file had N items before, it should have N+1 items after
       adding a new preference (unless there's a conflict).
    
    REMEMBER: The edit_file tool REPLACES the entire file content. You must include
    ALL existing items in your edit_file call, not just the new item."""

# Create agent with CompositeBackend for long-term memory
def make_backend(runtime):
    """Create a CompositeBackend with both transient and persistent storage."""
    return CompositeBackend(
        default=StateBackend(runtime),
        routes={
            "/memories/": StoreBackend(runtime)
        }
    )

# Create agent with system prompt that instructs it to read and update instructions
agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    store=InMemoryStore(), 
    backend=make_backend,
    checkpointer=checkpointer,
    system_prompt=SYSTEM_PROMPT
)

print("=" * 70)
print("SELF-IMPROVING INSTRUCTIONS DEMONSTRATION")
print("=" * 70)

# ============================================================================
# Conversation 1: Initial feedback and instruction update
# ============================================================================
print("\n[Conversation 1] User provides initial feedback")
print("-" * 70)

config1 = {"configurable": {"thread_id": str(uuid.uuid4())}}

# User provides feedback that should be saved to instructions
result1 = agent.invoke({
    "messages": [{"role": "user", "content": "Please always format code responses with proper indentation and add comments. I prefer detailed explanations."}]
}, config=config1)

print(f"Agent response: {result1['messages'][-1].content[:300]}...")

# Check if instructions file was created/updated
result1_check = agent.invoke({
    "messages": [{"role": "user", "content": "Read the file /memories/instructions.txt and show me its contents"}]
}, config=config1)

print(f"\nInstructions file content:\n{result1_check['messages'][-1].content[:500]}...")

# ============================================================================
# Conversation 2: Additional feedback in same thread
# ============================================================================
print("\n[Conversation 2] User provides additional feedback (same thread)")
print("-" * 70)

# User provides more feedback
result2 = agent.invoke({
    "messages": [{"role": "user", "content": "I also prefer that you always use type hints in Python code examples."}]
}, config=config1)

print(f"Agent response: {result2['messages'][-1].content[:300]}...")

# Check updated instructions
result2_check = agent.invoke({
    "messages": [{"role": "user", "content": "Show me the current contents of /memories/instructions.txt"}]
}, config=config1)

print(f"\nUpdated instructions file content:\n{result2_check['messages'][-1].content[:500]}...")

# ============================================================================
# Conversation 3: New thread - agent should remember previous instructions
# ============================================================================
print("\n[Conversation 3] New conversation thread - agent reads previous instructions")
print("-" * 70)

config2 = {"configurable": {"thread_id": str(uuid.uuid4())}}

# In a new thread, ask the agent to recall preferences
result3 = agent.invoke({
    "messages": [{"role": "user", "content": "What are my coding preferences? Please check /memories/instructions.txt"}]
}, config=config2)

print(f"Agent response: {result3['messages'][-1].content[:400]}...")

# ============================================================================
# Conversation 4: Agent applies remembered preferences
# ============================================================================
print("\n[Conversation 4] Agent applies remembered preferences")
print("-" * 70)

# Ask agent to write code - it should apply the remembered preferences
result4 = agent.invoke({
    "messages": [{"role": "user", "content": "Write a Python function to calculate factorial. Make sure to follow my preferences."}]
}, config=config2)

print(f"Agent response (should follow preferences):\n{result4['messages'][-1].content[:600]}...")

# ============================================================================
# Conversation 5: More feedback accumulates
# ============================================================================
print("\n[Conversation 5] Additional feedback accumulates")
print("-" * 70)

# User provides more specific feedback
result5 = agent.invoke({
    "messages": [{"role": "user", "content": "When explaining concepts, please always provide real-world examples. I learn better that way."}]
}, config=config2)

print(f"Agent response: {result5['messages'][-1].content[:300]}...")

# Final check of accumulated instructions
result5_check = agent.invoke({
    "messages": [{"role": "user", "content": "Show me all the instructions and preferences you've saved in /memories/instructions.txt"}]
}, config=config2)

print(f"\nFinal accumulated instructions:\n{result5_check['messages'][-1].content[:600]}...")

print("\n" + "=" * 70)
print("DEMONSTRATION COMPLETE")
print("=" * 70)
print("\nKey takeaways:")
print("  - Agent reads /memories/instructions.txt at the start of conversations")
print("  - Agent stores preferences as an unordered list (bullet points)")
print("  - Agent never removes list items during summarization")
print("  - Agent only removes items if they conflict with new preferences")
print("  - Agent can enhance existing list items when needed")
print("  - Instructions persist across different conversation threads")
print("  - Instructions accumulate over time, helping the agent improve")
print("=" * 70)
