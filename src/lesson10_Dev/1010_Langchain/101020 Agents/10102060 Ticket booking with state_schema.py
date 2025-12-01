# Demonstrates defining custom state via state_schema for ticket booking

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentState, create_agent
from langchain.tools import tool

# Load environment variables from .env file
load_dotenv(find_dotenv())


# Define custom state schema for ticket booking
class TicketBookingState(AgentState):
    """Custom state schema for tracking ticket booking information."""
    booking_info: dict


@tool
def check_flight_availability(flight_number: str, date: str) -> str:
    """Check if a flight is available on a given date."""
    # Simulated flight availability check
    available_flights = {
        "CA123": ["2024-12-25", "2024-12-26", "2024-12-27"],
        "MU456": ["2024-12-25", "2024-12-28"],
        "CZ789": ["2024-12-26", "2024-12-27", "2024-12-29"],
    }
    
    if flight_number in available_flights and date in available_flights[flight_number]:
        return f"Flight {flight_number} is available on {date}"
    else:
        return f"Flight {flight_number} is not available on {date}"


@tool
def check_seat_availability(flight_number: str, date: str, seat_preference: str) -> str:
    """Check if preferred seat is available for a flight."""
    # Simulated seat availability check
    seat_map = {
        "window": "Window seats available: A1, A2, F1, F2",
        "aisle": "Aisle seats available: C1, C2, D1, D2",
        "middle": "Middle seats available: B1, B2, E1, E2",
    }
    
    if seat_preference.lower() in seat_map:
        return f"For flight {flight_number} on {date}: {seat_map[seat_preference.lower()]}"
    else:
        return f"Seat preference '{seat_preference}' not recognized. Available options: window, aisle, middle"


@tool
def book_ticket(flight_number: str, date: str, seat_preference: str) -> str:
    """Book a ticket with the specified flight number, date, and seat preference."""
    return f"Ticket booked successfully! Flight: {flight_number}, Date: {date}, Seat Preference: {seat_preference}"


# Create the model
model = ChatOpenAI(model="gpt-4o-mini")

# Create agent with custom state schema
agent = create_agent(
    model=model,
    tools=[check_flight_availability, check_seat_availability, book_ticket],
    state_schema=TicketBookingState,  ## ⬅️ Define custom state via state_schema
)

# Example: User wants to buy a ticket by Date, Flight No. and Seat Preference
print("=" * 60)
print("Ticket Booking Example")
print("=" * 60)

result = agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": "I want to book a ticket for flight CA123 on December 25, 2024 with a window seat preference",
        }
    ],
    "booking_info": {
        "date": "2024-12-25",
        "flight_number": "CA123",
        "seat_preference": "window",
    },
})

pprint(result)

