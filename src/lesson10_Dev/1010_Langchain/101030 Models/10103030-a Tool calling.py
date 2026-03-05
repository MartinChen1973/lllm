# Demonstrates tool calling with model binding and tool invocation

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model
from langchain.tools import tool

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)


# Initialize a basic model
model = init_chat_model("openai:gpt-4o-mini")

# ============================================================================
# Tool Calling - Define and bind tools to model
# ============================================================================
print("=" * 80)
print("Example: Tool Calling")
print("=" * 80)

# Define a tool using the @tool decorator
@tool
def get_weather(location: str) -> str:
    """Get the weather at a location.""" ## ⬅️ Tool description
    return f"It's sunny in {location}."

# Bind tools to the model
model_with_tools = model.bind_tools([get_weather])  ## ⬅️ Bind tools to enable tool calling

# Invoke the model with a query that should trigger tool usage
response = model_with_tools.invoke("What's the weather like in Boston?")  ## ⬅️ Invoke model with tool-enabled query

# Print the response
print("\nResponse:")
pprint(response)

# Iterate through tool calls made by the model
print("\nTool Calls:")
for tool_call in response.tool_calls:  ## ⬅️ Access tool calls from the response
    print(f"Tool: {tool_call['name']}")
    print(f"Args: {tool_call['args']}")

