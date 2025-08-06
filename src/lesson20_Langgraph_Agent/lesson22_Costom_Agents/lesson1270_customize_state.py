# 1. 演示如何让智能体记住对话历史
# 2. 演示如何利用thread_id来区分不同的会话

from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langgraph.graph.state import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import InjectedToolCallId, tool
from pydantic import BaseModel, Field, field_validator, ValidationError, ValidationInfo
import os
import sys
import re

# Add the project root to sys.path (cleaner than the old approach)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utilities.image_saver.image_saver import save_graph_image    

# Load environment variables
load_dotenv(find_dotenv())

# =============================================
# Define the data structure for the couplet response using Pydantic
class Couplet(BaseModel):
    """Data model for Chinese couplet with validation rules."""
    
    upper_part: str = Field(
        description="对联的上联，字数必须在7-15个字之间",
        # description="对联的上联，字数必须在10-15个字之间",
        min_length=5,
        max_length=15
    )
    lower_part: str = Field(
        description="对联的下联，字数必须与上联相同，且字数在7-15个字之间",
        # description="对联的下联，字数必须与上联相同，且字数在10-15个字之间",
        min_length=5,
        max_length=15
    )
    horizontal_part: str = Field(
        description="对联的横批，必须是4个字",
        min_length=4,
        max_length=4
    )

    # Field validator for the lower part of the couplet - check if it matches upper part length
    @field_validator("lower_part", mode="before")
    @classmethod
    def lower_part_must_match_upper_length(cls, value, info: ValidationInfo):
        """Ensure lower part length matches upper part length."""
        upper_part = info.data.get("upper_part")
        if upper_part and len(value) != len(upper_part):
            raise ValueError(f"下联的长度必须和上联相同。当前上联：{upper_part}（{len(upper_part)}字），下联：{value}（{len(value)}字）")
        return value
# ---------------------------------------------

# Define the system prompt （### 注意 ### 如果此处的要求与Couplet类的要求不一致，则会导致Pydantic验证失败）
SYSTEM_PROMPT = """你是一个对联助手，专门帮助用户创作对联。
1. 你的主要任务是根据用户提供的主题，帮他们写出一副对联（上联、下联和横批）。
**重要！** 上联为5~15个字，下联为5~15个字，横批为4个字。
2. 每次与用户对话时，你都要以"Hi，我可以帮你写对联，请提供主题。"开头。
3. 每次回复用户时，都要展示当前生成的对联内容（包括上联、下联和横批）。
4. 请始终友好、简洁且准确地帮助用户完成对联创作。

**重要格式要求：**
请严格按照以下JSON格式输出对联内容：
```json
{
  "upper_part": "上联内容",
  "lower_part": "下联内容", 
  "horizontal_part": "横批内容"
}
```

请确保JSON格式正确，且内容符合字数要求。"""

# Define the structure of the chatbot's state
class State(TypedDict):
    messages: Annotated[list, add_messages]
    couplet: Couplet | None

def extract_couplet_parts(content: str) -> Couplet:
    """
    Extracts the couplet parts from the message content using JSON parsing.
    Includes comprehensive error handling for Pydantic validation.
    """
    import json
    
    json_str = None  # Initialize json_str variable
    
    try:
        # Try to find JSON structure in the content
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # If no code block, try to find JSON directly
            json_match = re.search(r'\{.*?\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No JSON structure found in the response")
        
        # Parse JSON
        couplet_data = json.loads(json_str)
        
        # Create and return a Couplet object
        return Couplet(
            upper_part=couplet_data.get("upper_part", ""),
            lower_part=couplet_data.get("lower_part", ""),
            horizontal_part=couplet_data.get("horizontal_part", "")
        )
        
    except Exception as e:
        # Handle all errors with detailed error messages
        print(f"\n=== Error in Couplet Extraction ===")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print(f"Raw content: {content}")
        
        if json_str:
            try:
                couplet_data = json.loads(json_str)
                print(f"Extracted values:")
                print(f"  上联: '{couplet_data.get('upper_part', '')}' (长度: {len(couplet_data.get('upper_part', ''))})")
                print(f"  下联: '{couplet_data.get('lower_part', '')}' (长度: {len(couplet_data.get('lower_part', ''))})")
                print(f"  横批: '{couplet_data.get('horizontal_part', '')}' (长度: {len(couplet_data.get('horizontal_part', ''))})")
            except:
                print(f"  Could not extract values from JSON")
        
        if isinstance(e, ValidationError):
            print(f"Validation errors:")
            for error in e.errors():
                field_name = error['loc'][0] if error['loc'] else 'unknown'
                error_type = error['type']
                error_msg = error['msg']
                print(f"  - {field_name}: {error_type} - {error_msg}")
        
        print(f"=== End Error ===\n")
        raise

# Initialize Tavily search tool and bind it to the LLM
tavily = TavilySearchResults(max_results=10)
tools = [tavily]
llm = ChatOpenAI(model="gpt-4o-mini")
# llm = ChatOpenAI(model="gpt-4o")
llm_knows_tools = llm.bind_tools(tools)

# Define the chatbot function that takes the current state and updates it with a new message
def chatbot(state: State):
    # Check if the first message is not a SystemMessage
    if not state["messages"] or not isinstance(state["messages"][0], SystemMessage):
        # Insert system message as the first message
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    else:
        messages = state["messages"]
    
    # Get response from LLM
    response = llm_knows_tools.invoke(messages)
    
    # Extract couplet parts from the response and create Couplet object
    try:
        couplet = extract_couplet_parts(response.content)
    except Exception as e:
        # If extraction fails, create error feedback message
        error_feedback = f"""系统提示：对联格式验证失败，请重新生成。

错误信息：{str(e)}

请确保对联格式符合以下要求：
- 上联：5-15个字符
- 下联：5-15个字符，且与上联长度相同  
- 横批：4个字符

请严格按照以下JSON格式输出：
```json
{{
  "upper_part": "上联内容",
  "lower_part": "下联内容", 
  "horizontal_part": "横批内容"
}}
```"""
        
        # Create an error message to inform the user
        error_message = SystemMessage(content=error_feedback)
        
        # Return the error message and an empty couplet to continue the conversation
        return {
            "messages": [error_message],
            "couplet": None  # No couplet when there's an error
        }
    
    # Return both the message and the couplet object
    return {
        "messages": [response],
        "couplet": couplet
    }

# Set up the StateGraph with our defined state structure
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)

# Add a ToolNode for managing tool usage (like Tavily search)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# Define conditional edges to invoke tools when needed
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")  # Return to chatbot after using a tool

# Set the entry point for the conversation flow
graph_builder.set_entry_point("chatbot")

# =============================================
# Add memory to the chatbot
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)
# --------------------------------------------

# Function to handle conversation updates with thread_id for memory
def stream_graph_updates(user_input: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    # The config is the **second positional argument** to stream() or invoke()!
    events = graph.stream(
        {"messages": [("user", user_input)]}, config, stream_mode="values"
    )
    for event in events:
        message = event["messages"][-1] # Get the last message in the event
        # 1. print the last message in the event no matter what, or...
        message.pretty_print()
        print(event)
        # Also print the extracted couplet parts if they exist
        if event.get("couplet") is not None:
            couplet = event["couplet"]
            print(f"\nExtracted Couplet Parts:")
            print(f"上联: {couplet.upper_part}")
            print(f"下联: {couplet.lower_part}")
            print(f"横批: {couplet.horizontal_part}")
        else:
            print(f"\nNo couplet extracted - validation error occurred.")

if __name__ == "__main__":
    # Optional: Visualize the graph structure
    save_graph_image(graph, os.path.basename(__file__))

    # =============================================
    # Chatbot loop with memory enabled using thread_id
    while True:
        print("==================================== Users can input 'quit' to quit.")
        thread_id = input("Enter a thread ID for this session: ")
        user_input = input("User: ")
        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        stream_graph_updates(user_input, thread_id)
    # --------------------------------------------