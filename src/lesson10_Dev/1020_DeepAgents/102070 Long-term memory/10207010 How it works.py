"""
How it works - Long-term memory example

This example demonstrates how CompositeBackend maintains two separate filesystems:
1. Short-term (transient) filesystem - stored in agent state, lost when thread ends
2. Long-term (persistent) filesystem - stored in LangGraph Store, persists across threads

It shows:
- Writing to transient files (lost after thread ends)
- Writing to persistent files (survives across threads)
- Cross-thread persistence (reading from different threads)

Based on the documentation from:
src/lesson10_Dev/1020_DeepAgents/102070 Long-term memory/102070 Long-term memory.md
"""

import uuid
from dotenv import load_dotenv, find_dotenv
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

# Load environment variables from .env file
load_dotenv(find_dotenv())


# Create agent with CompositeBackend for long-term memory
def make_backend(runtime):
    """Create a CompositeBackend with both transient and persistent storage."""
    return CompositeBackend(
        default=StateBackend(runtime),  # ⬅️ Ephemeral storage
        routes={
            "/memories/": StoreBackend(runtime)  # ⬅️ Persistent storage
        }
    )

agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    store=InMemoryStore(),  # ⬅️ Required for StoreBackend
    backend=make_backend  # ⬅️ Pass function that receives runtime
)

print("=" * 70)
print("LONG-TERM MEMORY DEMONSTRATION")
print("=" * 70)

# ============================================================================
# Example 1: Transient file (lost after thread ends)
# ============================================================================
print("\n[Example 1] Writing to transient file (will be lost after thread ends)")
print("-" * 70)

config1 = {"configurable": {"thread_id": str(uuid.uuid4())}}
result1 = agent.invoke({
    "messages": [{"role": "user", "content": "Write a draft note to /draft.txt saying 'This is a temporary draft'"}]
}, config=config1)

print(f"Thread 1 result: {result1['messages'][-1].content[:200]}...")

# Try to read it in the same thread
result1_read = agent.invoke({
    "messages": [{"role": "user", "content": "Read the file /draft.txt"}]
}, config=config1)

print(f"Reading /draft.txt in same thread: {result1_read['messages'][-1].content[:200]}...")

# Try to read it in a different thread (should fail - transient file)
config2 = {"configurable": {"thread_id": str(uuid.uuid4())}}
result2_read = agent.invoke({
    "messages": [{"role": "user", "content": "Read the file /draft.txt"}]
}, config=config2)

print(f"Reading /draft.txt in different thread: {result2_read['messages'][-1].content[:200]}...")

# ============================================================================
# Example 2: Persistent file (survives across threads)
# ============================================================================
print("\n[Example 2] Writing to persistent file (survives across threads)")
print("-" * 70)

# Write to persistent memory in thread 1
result3 = agent.invoke({
    "messages": [{"role": "user", "content": "Save my preferences to /memories/preferences.txt. My preferences are: I like Python programming, prefer dark mode, and enjoy reading technical documentation."}]
}, config=config1)

print(f"Thread 1 - Saved preferences: {result3['messages'][-1].content[:200]}...")

# Read from persistent memory in the same thread
result3_read = agent.invoke({
    "messages": [{"role": "user", "content": "What are my preferences?"}]
}, config=config1)

print(f"Thread 1 - Reading preferences: {result3_read['messages'][-1].content[:200]}...")

# ============================================================================
# Example 3: Cross-thread persistence
# ============================================================================
print("\n[Example 3] Cross-thread persistence (reading from different thread)")
print("-" * 70)

# Read from persistent memory in a completely different thread
result4 = agent.invoke({
    "messages": [{"role": "user", "content": "What are my preferences?"}]
}, config=config2)

print(f"Thread 2 - Reading preferences from different thread: {result4['messages'][-1].content[:200]}...")

# ============================================================================
# Example 4: List files to see the difference
# ============================================================================
print("\n[Example 4] Listing files to see transient vs persistent")
print("-" * 70)

result5 = agent.invoke({
    "messages": [{"role": "user", "content": "List all files in the root directory and in /memories/"}]
}, config=config2)

print(f"File listing: {result5['messages'][-1].content[:300]}...")

print("\n" + "=" * 70)
print("DEMONSTRATION COMPLETE")
print("=" * 70)
print("\nKey takeaways:")
print("  • Files without /memories/ prefix are transient (lost after thread ends)")
print("  • Files with /memories/ prefix are persistent (survive across threads)")
print("  • Persistent files can be accessed from any thread")
print("=" * 70)

