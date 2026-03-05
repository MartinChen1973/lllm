# Demonstrates structured output with include_raw=True
# Returns both the parsed output and the raw AI message to access response metadata such as token counts

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)


# Initialize a basic model
model = init_chat_model("openai:gpt-4o-mini")

# ============================================================================
# Structured output with include_raw=True
# ============================================================================
print("=" * 80)
print("Example: Structured output with include_raw to get both parsed and raw response")
print("=" * 80)

# Define a Pydantic model for movie information
class Movie(BaseModel):
    """A movie with details."""
    title: str = Field(..., description="The title of the movie")
    year: int = Field(..., description="The year the movie was released")
    director: str = Field(..., description="The director of the movie")
    rating: float = Field(..., description="The movie's rating out of 10")

# Create a model with structured output and include_raw=True
model_with_structure = model.with_structured_output(Movie, include_raw=True)

# Invoke the model to get structured output about Inception
response = model_with_structure.invoke("Provide details about the movie Inception")

# Print the response structure
print("\nResponse Structure:")
print(f"Type: {type(response)}")
print(f"Keys: {response.keys() if hasattr(response, 'keys') else 'N/A'}")

# Access the parsed output
print("\n" + "=" * 80)
print("Parsed Output:")
print("=" * 80)
pprint(response["parsed"])
print(f"\nParsed Type: {type(response['parsed'])}")

# Access the raw AIMessage
print("\n" + "=" * 80)
print("Raw AIMessage:")
print("=" * 80)
pprint(response["raw"])

# Access parsing error (if any)
print("\n" + "=" * 80)
print("Parsing Error:")
print("=" * 80)
print(f"Parsing Error: {response.get('parsing_error', None)}")

# Access token usage from raw message if available
print("\n" + "=" * 80)
print("Token Usage (from raw message):")
print("=" * 80)
if hasattr(response["raw"], "response_metadata"):
    usage = response["raw"].response_metadata.get("token_usage", {})
    if usage:
        pprint(usage)
    else:
        print("Token usage not available in response metadata")

