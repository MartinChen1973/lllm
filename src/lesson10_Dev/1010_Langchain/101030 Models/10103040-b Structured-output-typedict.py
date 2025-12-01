# Demonstrates structured output using TypedDict
# TypedDict provides a simpler alternative using Python's built-in typing, ideal when you don't need runtime validation

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict, Annotated

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Initialize a basic model
model = init_chat_model("openai:gpt-4o-mini")

# ============================================================================
# Structured output with TypedDict
# ============================================================================
print("=" * 80)
print("Example: Structured output using TypedDict")
print("=" * 80)

# Define a TypedDict for movie information
class MovieDict(TypedDict): ## ⬅️ TypedDict for movie information
    """A movie with details."""
    title: Annotated[str, ..., "The title of the movie"]
    year: Annotated[int, ..., "The year the movie was released"]
    director: Annotated[str, ..., "The director of the movie"]
    rating: Annotated[float, ..., "The movie's rating out of 10"]

# Create a model with structured output
model_with_structure = model.with_structured_output(MovieDict)

# Invoke the model to get structured output about Inception
response = model_with_structure.invoke("Provide details about the movie Inception")

# Print the structured response
print("\nStructured Response:")
pprint(response)
print(f"\nType: {type(response)}")
print(f"Title: {response['title']}")
print(f"Year: {response['year']}")
print(f"Director: {response['director']}")
print(f"Rating: {response['rating']}")

