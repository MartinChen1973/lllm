# Demonstrates tool use in the ReAct loop

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.agents import create_agent
from langchain.tools import tool

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)



@tool
def search_products(query: str) -> str:
    """Search for products by query. Returns top 5 matching products."""
    # Simulated product database
    products = {
        "wireless headphones": [
            "WH-1000XM5",
            "AirPods Pro",
            "Bose QuietComfort 45",
            "Sony WH-CH720N",
            "Sennheiser Momentum 4",
        ],
        "laptops": ["MacBook Pro", "Dell XPS 13", "ThinkPad X1", "Surface Laptop", "HP Spectre"],
    }

    query_lower = query.lower()
    if query_lower in products:
        results = products[query_lower]
        return f'Found 5 products matching "{query}". Top 5 results: {", ".join(results)}'
    return f'Found 5 products matching "{query}". Top 5 results: Product1, Product2, Product3, Product4, Product5'


@tool
def check_inventory(product_id: str) -> str:
    """Check inventory/stock status for a product by product ID."""
    # Simulated inventory database
    inventory = {
        "WH-1000XM5": 10,
        "AirPods Pro": 5,
        "Bose QuietComfort 45": 0,
        "Sony WH-CH720N": 15,
        "Sennheiser Momentum 4": 8,
        "MacBook Pro": 3,
        "Dell XPS 13": 7,
    }

    stock = inventory.get(product_id, 0)
    return f"Product {product_id}: {stock} units in stock"


# Create agent with tools
agent = create_agent(
    model="gpt-4o-mini",
    tools=[search_products, check_inventory],  ## ⬅️ Tool list, should be called in logical order
)

# Run the agent with a query that requires multiple tool calls (ReAct loop)
response = agent.invoke({
    "messages": [
        {"role": "user", "content": "Find the most popular wireless headphones right now and check if they're in stock"},
    ]
})

# Print the response with pretty print
print("=" * 80)
print("Final Response:")
print("=" * 80)
pprint(response)

# Print the message history to show the ReAct loop
print("\n" + "=" * 80)
print("Message History (ReAct Loop):")
print("=" * 80)
for i, msg in enumerate(response.get("messages", []), 1):
    msg_type = type(msg).__name__
    print(f"\n[{i}] {msg_type}:")
    if hasattr(msg, "content") and msg.content:
        print(f"    Content: {msg.content}")
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        print(f"    Tool Calls:")
        for tc in msg.tool_calls:
            print(f"      - {tc.get('name', 'unknown')}({tc.get('args', {})})")

