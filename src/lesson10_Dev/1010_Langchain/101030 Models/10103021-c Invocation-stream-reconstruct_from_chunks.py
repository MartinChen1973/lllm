# Demonstrates reconstructing a complete AIMessage from streaming chunks

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Initialize a basic model
model = init_chat_model("openai:gpt-4o-mini")

# ============================================================================
# Reconstructing Complete Message from Stream Chunks
# ============================================================================
print("=" * 80)
print("Example: Reconstructing Complete AIMessage from Streaming Chunks")
print("=" * 80)

full = None  # None | AIMessageChunk
print("Building full message from chunks:")
for chunk in model.stream("What color is the sky?"):
    full = chunk if full is None else full + chunk
    print(full.text)

print()
print("Final full message content_blocks:")
pprint(full.content_blocks)
print()

