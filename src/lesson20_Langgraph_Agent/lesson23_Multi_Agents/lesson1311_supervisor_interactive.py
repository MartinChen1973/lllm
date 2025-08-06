from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import InMemorySaver

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Create checkpointer for memory
checkpointer = InMemorySaver()

# Flight booking tool ==========================================
def book_flight(from_airport: str, to_airport: str):
    """Book a flight"""
    print(f"[TOOL] book_flight called: {from_airport} -> {to_airport}")
    return f"Successfully booked a flight from {from_airport} to {to_airport}."

def get_flight_info(from_airport: str, to_airport: str):
    """Get flight information"""
    print(f"[TOOL] get_flight_info called: {from_airport} -> {to_airport}")
    # Use a static, prebuilt list of flights (all from Shanghai to Beijing)
    flights = [
        "MU5101 | China Eastern | Departure: 08:00 | Shanghai -> Beijing",
        "CA1502 | Air China | Departure: 10:30 | Shanghai -> Beijing",
        "CZ8888 | China Southern | Departure: 13:15 | Shanghai -> Beijing",
        "HU7609 | Hainan Airlines | Departure: 15:45 | Shanghai -> Beijing",
        "9C9999 | Spring Airlines | Departure: 18:20 | Shanghai -> Beijing",
    ]
    return "Available flights:\n" + "\n".join(flights)

flight_assistant = create_react_agent(
    model="openai:gpt-4o-mini",
    tools=[book_flight, get_flight_info],
    prompt=(
        "You are a flight booking assistant. "
        "When users ask about flights, first use get_flight_info to show available flights. "
        "When users specify a particular flight they want to book, use book_flight to complete the booking. "
        "Always provide helpful information about available flights before booking."
    ),
    name="flight_assistant",
    checkpointer=checkpointer
)

# Hotel booking tool ==========================================
def book_hotel(hotel_name: str):
    """Book a hotel"""
    print(f"[TOOL] book_hotel called: {hotel_name}")
    return f"Successfully booked a stay at {hotel_name}."

def get_hotel_info(hotel_name: str):
    """Get hotel information"""
    print(f"[TOOL] get_hotel_info called: {hotel_name}")
    # Use a static, prebuilt list of hotels (all in Beijing)
    hotels = [
        "Grand Hyatt Beijing | 5-star | Wangfujing | Price: ¥1200/night",
        "Park Plaza Beijing Wangfujing | 4-star | Dongcheng | Price: ¥800/night",
        "The Peninsula Beijing | 5-star | Dongcheng | Price: ¥1500/night",
        "Novotel Beijing Peace | 4-star | Wangfujing | Price: ¥700/night",
        "Holiday Inn Express Beijing Dongzhimen | 3-star | Dongzhimen | Price: ¥500/night",
    ]
    return "Available hotels:\n" + "\n".join(hotels)

hotel_assistant = create_react_agent(
    model="openai:gpt-4o-mini",
    tools=[book_hotel, get_hotel_info],
    prompt=(
        "You are a hotel booking assistant. "
        "When users ask about hotels, first use get_hotel_info to show available hotels. "
        "When users specify a particular hotel they want to book, use book_hotel to complete the booking. "
        "Always provide helpful information about available hotels before booking."
    ),
    name="hotel_assistant",
    checkpointer=checkpointer
)

# Create supervisor workflow ==========================================
supervisor_workflow = create_supervisor(
    agents=[flight_assistant, hotel_assistant],
    model=ChatOpenAI(model="gpt-4o-mini"),
    prompt=(
        "You are a supervisor managing specialized booking assistants. "
        "Your role is to delegate user requests to the appropriate specialist: "
        "- For flight-related requests (flights, airlines, airports, travel), delegate to flight_assistant "
        "- For hotel-related requests (hotels, accommodation, lodging), delegate to hotel_assistant "
        "Do not repeat delegation messages. Let the specialist agents handle the requests directly."
    )
)

# Add memory with checkpointer
supervisor = supervisor_workflow.compile(checkpointer=checkpointer)

# Function to handle conversation updates with thread_id for memory
def stream_supervisor_updates(user_input: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    # The config is the **second positional argument** to stream() or invoke()!
    events = supervisor.stream(
        {"messages": [{"role": "user", "content": user_input}]}, 
        config,
        stream_mode="values"
    )
    for event in events:
        message = event["messages"][-1] # Get the last message in the event
        # Print the last message in the event
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

        stream_supervisor_updates(user_input, thread_id)