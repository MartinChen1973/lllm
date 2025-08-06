# 1. 演示如何让智能体自动使用工具（如Tavily搜索引擎）来回答问题

import sys
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utilities.image_saver.image_saver import save_graph_image    
from src.utilities.datetime.datetime import get_datetime_info

# Load environment variables
load_dotenv(find_dotenv())

# Define the structure of the chatbot's state
class State(TypedDict):
    messages: Annotated[list, add_messages]

# =============================================
# Initialize tools
tavily = TavilySearchResults(max_results=10)
tools = [tavily, get_datetime_info]
model = ChatOpenAI(model="gpt-4o-mini")

model_knows_tools = model.bind_tools(tools)
# ---------------------------------------------

# Define the chatbot function that takes the current state and updates it with a new message
def chatbot(state: State):
    # The LLM with tools bound to it can now invoke the search engine if needed
    return {"messages": [model_knows_tools.invoke(state["messages"])]}

# Set up the StateGraph with our defined state structure
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)  # Add the chatbot node

# =============================================
# Add a ToolNode for managing tool usage (like Tavily search)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)
# ---------------------------------------------

# Define conditional edges to invoke tools when needed
graph_builder.add_conditional_edges("chatbot", tools_condition)
# graph_builder.add_edge("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")  # Return to chatbot after using a tool

# Set the entry point for the conversation flow
graph_builder.set_entry_point("chatbot")

# Compile the graph to make it runnable
graph = graph_builder.compile()

# Function to handle conversation updates
def stream_graph_updates(user_input: str):
    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        stream_mode="values",
    )
    
    for event in events:
        if "messages" in event:
            event["messages"][-1].pretty_print()

if __name__ == "__main__":
    # Optional: Visualize the graph structure
    save_graph_image(graph, os.path.basename(__file__))

    # Chatbot loop
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        stream_graph_updates(user_input)
