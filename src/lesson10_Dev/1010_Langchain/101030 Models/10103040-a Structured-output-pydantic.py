# Demonstrates structured output using Pydantic models
# Pydantic provides the richest feature set with field validation, descriptions, and nested structures

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)


# Initialize a basic model
model = init_chat_model("openai:gpt-4o-mini")

# ============================================================================
# Structured output with Pydantic
# ============================================================================
print("=" * 80)
print("Example: Structured output using Pydantic BaseModel")
print("=" * 80)

# Define a Pydantic model for movie information
class Movie(BaseModel): ## ⬅️ Pydantic model for movie information
    """A movie with details."""
    title: str = Field(..., description="The title of the movie")
    year: int = Field(..., description="The year the movie was released")
    director: str = Field(..., description="The director of the movie")
    rating: float = Field(..., description="The movie's rating out of 10")

# Create a model with structured output
model_with_structure = model.with_structured_output(Movie)

# Invoke the model to get structured output about Inception
response = model_with_structure.invoke("Provide details about the movie Inception")

# Print the structured response
print("\nStructured Response:")
pprint(response)
print(f"\nType: {type(response)}")
print(f"Title: {response.title}")
print(f"Year: {response.year}")
print(f"Director: {response.director}")
print(f"Rating: {response.rating}")

