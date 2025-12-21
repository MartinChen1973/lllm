"""
Use case: Self-improving instructions

This example demonstrates how an agent can update its own instructions based on user feedback.
The agent maintains a persistent instructions file at /memories/instructions.txt that accumulates
user preferences and feedback over time, helping the agent improve its behavior across conversations.

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
load_dotenv(find_dotenv())

# Checkpointer is required for state persistence
checkpointer = MemorySaver()

# Create agent with CompositeBackend for long-term memory
def make_backend(runtime):
    """Create a CompositeBackend with both transient and persistent storage."""
    return CompositeBackend(
        default=StateBackend(runtime),  # ⬅️ Ephemeral storage
        routes={
            "/memories/": StoreBackend(runtime)  # ⬅️ Persistent storage (across all threads)
        }
    )

# Create agent with system prompt that instructs it to read and update instructions
agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    store=InMemoryStore(),  # ⬅️ Required for StoreBackend
    backend=make_backend,
    checkpointer=checkpointer,
    system_prompt="""You have a file at /memories/instructions.txt with additional
    instructions and preferences.

    Read this file at the start of conversations to understand user preferences.

    When users provide feedback like "please always do X" or "I prefer Y",
    update /memories/instructions.txt using the edit_file tool to add these preferences.
    
    Accumulate all user preferences and instructions in this file so you can remember
    them in future conversations."""
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
print("  • Agent reads /memories/instructions.txt at the start of conversations")
print("  • Agent updates /memories/instructions.txt when users provide feedback")
print("  • Instructions persist across different conversation threads")
print("  • Instructions accumulate over time, helping the agent improve")
print("=" * 70)
