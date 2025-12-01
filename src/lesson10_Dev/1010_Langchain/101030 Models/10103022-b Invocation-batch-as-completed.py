# Demonstrates batch processing with batch_as_completed() method
# Yields responses as they finish, potentially out of order

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Initialize a basic model
model = init_chat_model("openai:gpt-4o-mini")

# ============================================================================
# Batch as completed - Yield responses as they finish
# ============================================================================
print("=" * 80)
print("Example: Batch as completed - Yield responses as they finish")
print("=" * 80)

for response in model.batch_as_completed([ ## 
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
]):
    pprint(response)
    print()
print()

