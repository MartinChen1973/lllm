from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_swarm, create_handoff_tool

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

model = ChatOpenAI(model="gpt-4o-mini")

# book_hotel tool ==========================================
def book_hotel(hotel_name: str):
    """Book a hotel"""
    print(f"TOOL CALLED: book_hotel with hotel_name={hotel_name}")
    return f"Successfully booked a stay at {hotel_name}."

transfer_to_hotel_assistant = create_handoff_tool(
    agent_name="hotel_assistant",
    description="Transfer user to the hotel-booking assistant.",
)

# book_flight tool ==========================================
def book_flight(from_airport: str, to_airport: str):
    """Book a flight"""
    print(f"TOOL CALLED: book_flight with from_airport={from_airport}, to_airport={to_airport}")
    return f"Successfully booked a flight from {from_airport} to {to_airport}."


transfer_to_flight_assistant = create_handoff_tool(
    agent_name="flight_assistant",
    description="Transfer user to the flight-booking assistant.",
)

# hotel_assistant agent ==========================================
tools=[book_hotel, transfer_to_flight_assistant]
llm_with_tools = model.bind_tools(tools, parallel_tool_calls=False)
hotel_assistant = create_react_agent(
    model=llm_with_tools,
    tools=[book_hotel, transfer_to_flight_assistant],
    prompt="You are a hotel booking assistant",
    name="hotel_assistant"
)

# flight_assistant agent ==========================================
tools=[book_flight, transfer_to_hotel_assistant]
llm_with_tools = model.bind_tools(tools, parallel_tool_calls=False)
flight_assistant = create_react_agent(
    model=llm_with_tools,
    tools=[book_flight, transfer_to_hotel_assistant],
    prompt="You are a flight booking assistant",
    name="flight_assistant"
)

swarm = create_swarm(
    agents=[flight_assistant, hotel_assistant],
    default_active_agent="flight_assistant"
).compile()

for chunk in swarm.stream(
    {
        "messages": [
            {
                "role": "user",
                "content": "book a flight from BOS to JFK and a stay at McKittrick Hotel"
            }
        ]
    }
):
    print(chunk)
    print("\n")