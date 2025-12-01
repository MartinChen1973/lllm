# Demonstrates structured output with nested structures
# Schemas can be nested to represent complex data structures

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Initialize a basic model
model = init_chat_model("openai:gpt-4o-mini")

# ============================================================================
# Structured output with nested structures
# ============================================================================
print("=" * 80)
print("Example: Structured output with nested structures")
print("=" * 80)

# Define nested Pydantic models for movie information
class Actor(BaseModel):
    """An actor in a movie."""
    name: str = Field(..., description="The actor's name")
    role: str = Field(..., description="The character role played by the actor")

class MovieDetails(BaseModel):
    """Detailed information about a movie."""
    title: str = Field(..., description="The title of the movie")
    year: int = Field(..., description="The year the movie was released")
    director: str = Field(..., description="The director of the movie")
    cast: list[Actor] = Field(..., description="List of main actors and their roles")
    genres: list[str] = Field(..., description="List of movie genres")
    rating: float = Field(..., description="The movie's rating out of 10")
    budget: float | None = Field(None, description="Budget in millions USD")

# Create a model with structured output
model_with_structure = model.with_structured_output(MovieDetails)

# Invoke the model to get structured output about Inception
response = model_with_structure.invoke(
    "Provide detailed information about the movie Inception, including main cast members, genres, and budget if available"
)

# Print the structured response
print("\nStructured Response:")
pprint(response)

# Access nested fields
print("\n" + "=" * 80)
print("Accessing Nested Fields:")
print("=" * 80)
print(f"Title: {response.title}")
print(f"Year: {response.year}")
print(f"Director: {response.director}")
print(f"Genres: {', '.join(response.genres)}")
print(f"Rating: {response.rating}")
print(f"Budget: {response.budget} million USD" if response.budget else "Budget: Not available")

print("\nMain Cast:")
for actor in response.cast:
    print(f"  - {actor.name} as {actor.role}")

