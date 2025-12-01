# Demonstrates model invocation with invoke() method

from pprint import pprint

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Initialize a basic model
model = init_chat_model("openai:gpt-4o-mini")

# ============================================================================
# Invoke - Single message
# ============================================================================
print("=" * 80)
print("Example 1: Invoke with single message")
print("=" * 80)

response = model.invoke("Why do parrots have colorful feathers?") ## ⬅️ Invoke the model with a single message
pprint(response)
print()

# ============================================================================
# Invoke - Dictionary format (conversation history)
# ============================================================================
print("=" * 80)
print("Example 2: Invoke with conversation history (dictionary format)")
print("=" * 80)

conversation = [ ## ⬅️ Invoke the model with a conversation history (dictionary format)
    {"role": "system",  "content": "You are a helpful assistant that translates English to French."},
    {"role": "user",    "content": "Translate: I love programming."},
    {"role": "assistant", "content": "J'adore la programmation."},
    {"role": "user",    "content": "Translate: I love building applications."}
]

response = model.invoke(conversation)
pprint(response)  # AIMessage("J'adore créer des applications.")
print()

# ============================================================================
# Invoke - Message objects
# ============================================================================
print("=" * 80)
print("Example 3: Invoke with message objects")
print("=" * 80)

conversation = [ ## ⬅️ Invoke the model with a conversation history (message objects)
    SystemMessage("You are a helpful assistant that translates English to French."),
    HumanMessage("Translate: I love programming."),
    AIMessage("J'adore la programmation."),
    HumanMessage("Translate: I love building applications.")
]

response = model.invoke(conversation)
pprint(response)  

