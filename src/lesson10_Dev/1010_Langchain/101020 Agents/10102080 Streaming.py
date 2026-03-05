# Demonstrates agent streaming to show intermediate progress

from dotenv import load_dotenv, find_dotenv
from langchain.agents import create_agent
from langchain_community.tools.tavily_search import TavilySearchResults

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)



# Initialize Tavily search tool
tavily = TavilySearchResults(max_results=5)  ## ⬅️ Real-time web search using Tavily

# Create agent with tools
agent = create_agent(
    model="gpt-4o-mini",
    tools=[tavily],  ## ⬅️ Agent will use Tavily to search and handle summarization
    system_prompt="You are a helpful assistant.",
)

# Stream agent execution to show intermediate progress
print("=" * 40)
print("Streaming Agent Execution")
print("=" * 40)
print(flush=True)

step = 0
for chunk in agent.stream({
    "messages": [{"role": "user", "content": "Search for AI news and summarize the findings"}]
}, stream_mode="values"):
    # Each chunk contains the full state at that point
    latest_message = chunk["messages"][-1]
    if latest_message.content:
        step += 1
        print(f"\n[Step {step}] Agent: {latest_message.content}", flush=True)
    elif latest_message.tool_calls:
        step += 1
        print(f"[Step {step}] Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}", flush=True)

# Note: Agent streaming (stream_mode="values") shows step-by-step progress:
# - [step1] The agent is invoked
# - [step2] Tool calls when the agent decides to use a tool
# - [step3] Tool results when tools complete execution
# - [step4] Final AI responses when the agent finishes reasoning
# This is different from LLM streaming, which shows token-by-token generation.
# Agent streaming provides visibility into the agent's decision-making process
# and tool execution, not the raw token generation.
