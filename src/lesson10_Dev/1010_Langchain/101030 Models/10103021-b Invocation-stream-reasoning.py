# Demonstrates streaming reasoning output from models that support reasoning

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Initialize a model that supports reasoning
model = init_chat_model("openai:deepseek-r1-250528")

# ============================================================================
# Stream Reasoning Output
# ============================================================================
print("=" * 80)
print("Example: Stream Reasoning Output")
print("=" * 80)

for chunk in model.stream("What color is the sky?"):
    for block in chunk.content_blocks:
        if block["type"] == "reasoning" and (reasoning := block.get("reasoning")):
            print(f"Reasoning: {reasoning}")
        elif block["type"] == "tool_call_chunk":
            print(f"Tool call chunk: {block}")
        elif block["type"] == "text":
            print(block["text"])
        else:
            ...
