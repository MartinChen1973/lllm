import os
from typing import Literal
from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
from tavily import TavilyClient

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)



# Customize Model ## ⬅️ Use a custom model
custom_model = init_chat_model(model="openai:gpt-4o-mini") 

# Customize System Prompt ## ⬅️ Use a custom system prompt
custom_system_prompt = """You are an expert researcher. Your job is to conduct thorough research, and then write a polished report."""  ## ⬅️

# Customize Tools
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

custom_tools = [internet_search]  ## ⬅️ Use custom tools

# Create the customized agent
agent = create_deep_agent(
    model=custom_model,  ## ⬅️ Use a custom model
    system_prompt=custom_system_prompt,  ## ⬅️ Use a custom system prompt
    tools=custom_tools,  ## ⬅️ Use custom tools
)

# Display graph structure
print("=" * 60)
print("Graph Nodes:")
print("=" * 60)
graph = agent.get_graph()
for node_name in graph.nodes.keys():
    print(f"  - {node_name}")
print("=" * 60)
print()

# Find tools
print("=" * 60)
print("Tools:")
print("=" * 60)
tools = []

# Get tools from tools node
if 'tools' in graph.nodes:
    tools_node = graph.nodes['tools']
    if hasattr(tools_node, 'tools'):
        node_tools = tools_node.tools
        if isinstance(node_tools, list):
            tools.extend(node_tools)
    elif hasattr(tools_node, '_tools'):
        node_tools = tools_node._tools
        if isinstance(node_tools, list):
            tools.extend(node_tools)

# Add custom tools
tools.extend(custom_tools)

# Remove duplicates and display
seen = set()
unique_tools = []
for tool in tools:
    if id(tool) not in seen:
        seen.add(id(tool))
        unique_tools.append(tool)

print(f"\nFound {len(unique_tools)} tool(s):")
for i, tool in enumerate(unique_tools, 1):
    tool_name = getattr(tool, 'name', getattr(tool, '__name__', 'Unknown'))
    tool_desc = getattr(tool, 'description', getattr(tool, '__doc__', '')) or ''
    print(f"\n{i}. {tool_name}")
    if tool_desc:
        print(f"   {tool_desc[:100]}...")

print("=" * 60 + "\n")

result = agent.invoke({
    "messages": [{"role": "user", "content": "What is deepagents?"}]
})

print("Agent Response:")
print("-" * 60)
print(result["messages"][-1].content)
print("-" * 60)
