# 1. 演示一个最简单的无记忆、无工具的智能体。

from dotenv import load_dotenv, find_dotenv
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(find_dotenv())

def get_chinese_name(city: str) -> str:
    """Translate city names to their Chinese names. """
    mapping = {
        "sf": "旧金山",
        "San Francisco": "旧金山",
        "nyc": "纽约",
        "New York City": "纽约",
    }
    return mapping.get(city.lower(), "未知")

def get_weather(city: str) -> str:  
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

checkpointer = MemorySaver()

agent = create_react_agent(
    model="openai:gpt-4o-mini",  
    tools=[get_weather, get_chinese_name],  
    prompt="You are a helpful assistant",
    checkpointer=checkpointer
)

# =============================================
# Function to handle conversation updates with thread_id for memory
def stream_agent_updates(user_input: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    # The config is the **second positional argument** to stream() or invoke()!
    events = agent.stream(
        {"messages": [{"role": "user", "content": user_input}]}, config, stream_mode="values"
    )
    for event in events:
        message = event["messages"][-1] # Get the last message in the event
        # 1. print the last message in the event no matter what, or...
        message.pretty_print()

if __name__ == "__main__":
    # Chatbot loop with memory enabled using thread_id
    while True:
        print("=========== Users can input 'quit' to quit.")
        thread_id = input("Enter a thread ID for this session: ")
        user_input = input("User: ")
        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        stream_agent_updates(user_input, thread_id)
# --------------------------------------------
