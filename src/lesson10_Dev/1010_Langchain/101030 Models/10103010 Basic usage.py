# Demonstrates basic model initialization with temperature, top_p, and top_k parameters

from pprint import pprint

from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Example 1: Initialize OpenAI model using init_chat_model
from langchain.chat_models import init_chat_model

model_openai = init_chat_model(
    model="openai:gpt-4o-mini", ## ⬅️ The model to use
    temperature=1.9,      ## ⬅️ Controls randomness in the model's output
    max_tokens=1000,      ## ⬅️ Limits the number of tokens in the response
    timeout=30,           ## ⬅️ Timeout for the model's output
    max_retries=3,        ## ⬅️ Maximum retry attempts on failure
    top_p=0.9,            ## ⬅️ Nucleus sampling: consider only the smallest set of tokens whose cumulative probability ≥ top_p
    top_k=50,             ## ⬅️ Limits sampling to the top_k highest-probability tokens
    stop=["\n\n"],        ## ⬅️ Stops generation when encountering these tokens
)

# Print the model
print(model_openai)

# Example 2: Basic model initialization with only model name (no additional parameters)
basic_model = init_chat_model("openai:gpt-4o-mini")

# Invoke the model with a simple query
response = basic_model.invoke("Why do parrots talk?") ## ⬅️ Invoke the model with a single message

# Print the response with pretty print
pprint(response)
