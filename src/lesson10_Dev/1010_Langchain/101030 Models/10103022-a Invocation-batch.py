# Demonstrates batch processing with batch() method

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Initialize a basic model
model = init_chat_model("openai:gpt-4o-mini")

# ============================================================================
# Batch - Multiple requests in parallel
# ============================================================================
print("=" * 80)
print("Example: Batch - Multiple requests in parallel")
print("=" * 80)

responses = model.batch([ ## ⬅️ Batch multiple requests in parallel
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
])
for response in responses:
    pprint(response)
    print()
print()

