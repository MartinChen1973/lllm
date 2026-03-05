# Demonstrates basic text streaming with stream() method

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)


# Initialize a basic model
model = init_chat_model("openai:gpt-4o-mini")

# ============================================================================
# Basic Text Streaming
# ============================================================================
print("=" * 80)
print("Example: Basic Text Streaming")
print("=" * 80)

print("Streaming response: ", end="")
for chunk in model.stream("Why do parrots have colorful feathers?"):  # ⬅️ Stream the model with a single message
    print(chunk.text, end="|", flush=True)
print("\n")

