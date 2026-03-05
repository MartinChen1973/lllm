# Demonstrates how to use OpenAI API to create a simple chatbot that prints "hello world!" in the console.

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model

# Load environment variables from .env file in current or parent directories (becomes globally accessible static variable).
load_dotenv(find_dotenv(), override=True)

# model or llm is an abbreviation for Large Language Model. init_chat_model is a function used to initialize a chat model.
llm = init_chat_model("openai:gpt-4o-mini")

# Start the chatbot and get the response
response = llm.invoke("Please say 'Hello world!'")

# Print the response
print(response.content)
