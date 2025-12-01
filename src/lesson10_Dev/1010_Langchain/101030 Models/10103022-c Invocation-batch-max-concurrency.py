# Demonstrates model invocation with batch() method and max_concurrency control

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Initialize a basic model
model = init_chat_model("openai:gpt-4o-mini")

# ============================================================================
# Batch with max concurrency - Control parallel calls
# ============================================================================
print("=" * 80)
print("Batch with max concurrency")
print("=" * 80)

list_of_inputs = [
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
]

responses = model.batch(
    list_of_inputs,
    config={
        'max_concurrency': 2,  ## ⬅️ Limit to 2 parallel calls
    }
)

for response in responses:
    pprint(response)
    print()

