# Demonstrates structured output with ToolStrategy and ProviderStrategy

from pprint import pprint
from pydantic import BaseModel

from dotenv import load_dotenv, find_dotenv
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy, ProviderStrategy

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)



# Define the structured output schema
class ContactInfo(BaseModel):
    """Contact information schema."""
    name: str
    email: str
    phone: str


# Create agent with structured output
# Swap between ToolStrategy and ProviderStrategy by commenting/uncommenting the response_format lines below
agent = create_agent(
    model="gpt-4o-mini",
    tools=[],
    # ToolStrategy: Uses artificial tool calling to generate structured output
    # Works with any model that supports tool calling
    response_format=ToolStrategy(ContactInfo),  ## ⬅️ ToolStrategy - works with any model supporting tool calling
    # ProviderStrategy: Uses the model provider's native structured output generation
    # More reliable but only works with providers that support native structured output (e.g., OpenAI)
    # Note: ProviderStrategy typically requires a more advanced model like "gpt-4o"
    # response_format=ProviderStrategy(ContactInfo),  ## ⬅️ ProviderStrategy - uses native structured output (requires OpenAI or compatible provider)
)

# Invoke the agent with a query that should return structured output
result = agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": "Extract contact info from: John Doe, john@example.com, (555) 123-4567",
        }
    ]
})

# Print the structured response
print("=" * 40)
print("Structured Response:")
print("=" * 40)
pprint(result["structured_response"])

