# Demonstrates structured output using JSON Schema
# For maximum control or interoperability, you can provide a raw JSON Schema

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Initialize a basic model
model = init_chat_model("openai:gpt-4o-mini")

# ============================================================================
# Structured output with JSON Schema
# ============================================================================
print("=" * 80)
print("Example: Structured output using JSON Schema")
print("=" * 80)

# Define JSON Schema for movie information
json_schema = { ## ⬅️ JSON Schema for movie information
    "title": "Movie",
    "description": "A movie with details",
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "The title of the movie"
        },
        "year": {
            "type": "integer",
            "description": "The year the movie was released"
        },
        "director": {
            "type": "string",
            "description": "The director of the movie"
        },
        "rating": {
            "type": "number",
            "description": "The movie's rating out of 10"
        }
    },
    "required": ["title", "year", "director", "rating"]
}

# Create a model with structured output using JSON Schema
model_with_structure = model.with_structured_output(
    json_schema,
    method="json_schema",
)

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