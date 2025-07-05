# 1. 演示使用参数化模板，限制用户输入的问题，以便更好地引导用户输入。

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load the API key from the .env file 从.env文件中加载API密钥
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# LangGraph imports
from typing import Annotated, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage

# Define the state structure 定义状态结构
class State(TypedDict):
    messages: Annotated[list, add_messages]
    # Add a generic template_params field for any parameters
    template_params: Dict[str, Any]

# Model: Create the OpenAI chatbot 创建聊天机器人
model = ChatOpenAI(name="gpt-4o-mini")

# OutputParser: Create an output parser 创建输出解析器
parser = StrOutputParser()

# Create the graph builder 创建图构建器
graph_builder = StateGraph(State)

# Define the chatbot node function 定义聊天机器人节点函数
def chatbot(state: State):
    # Get template parameters from state
    template_params = state.get("template_params", {})
    
    # Get the prompt template from state (or use a default)
    prompt_template = state.get("prompt_template", [
        ("system", "你是一个热心的AI助手。"),
        ("user", "请用{language}给我讲一个关于{subject}的{type}。")
    ])
    
    # Create the prompt template dynamically
    prompt = ChatPromptTemplate.from_messages(prompt_template)
    
    # Create messages from the prompt template with parameters
    messages = prompt.format_messages(**template_params)
    
    # Invoke the model
    response = model.invoke(messages)
    return {"messages": [response]}

# Add the chatbot node to the graph 将聊天机器人节点添加到图中
graph_builder.add_node("chatbot", chatbot)

# Add edges 添加边
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Compile the graph 编译图
graph = graph_builder.compile()

# Helper function to make invocation as simple as chain.invoke()
def simple_invoke(**kwargs):
    """Simple invocation function that mimics chain.invoke() syntax"""
    # Extract template_params from kwargs
    template_params = {}
    prompt_template = None
    
    # Check if prompt_template is provided
    if "prompt_template" in kwargs:
        prompt_template = kwargs.pop("prompt_template")
        # All remaining kwargs become template_params
        template_params = kwargs
    else:
        # Use default template, so we need language, subject, type
        # Check if these parameters are provided
        if "language" in kwargs and "subject" in kwargs and "type" in kwargs:
            template_params = kwargs
        else:
            # Use default values for missing parameters
            template_params = {
                "language": kwargs.get("language", "Chinese"),
                "subject": kwargs.get("subject", "dogs"),
                "type": kwargs.get("type", "short poem")
            }
    
    # Prepare the state
    state = {
        "messages": [HumanMessage(content="Generate content")],
        "template_params": template_params
    }
    
    # Add prompt_template if provided
    if prompt_template:
        state["prompt_template"] = prompt_template
    
    # Invoke the graph
    result = graph.invoke(state)
    return result["messages"][-1].content

# Example 1: Simple invocation like chain.invoke()
print("Example 1: Simple invocation like chain.invoke()")
print("-" * 50)
print(simple_invoke(type="short poem", subject="dogs", language="Chinese"))
print("\n")

# Example 2: English joke about cats
print("Example 2: English joke about cats")
print("-" * 50)
print(simple_invoke(type="joke", subject="cats", language="English"))
print("\n")

# Example 3: Different template with different parameters
print("Example 3: Different template with different parameters")
print("-" * 50)
print(simple_invoke(
    name="Alice",
    age="25", 
    hobby="painting",
    prompt_template=[
        ("system", "你是一个友好的AI助手。"),
        ("user", "请介绍一下{name}，她今年{age}岁，喜欢{hobby}。")
    ]
))
print("\n")

# Example 4: Weather template
print("Example 4: Weather template")
print("-" * 50)
print(simple_invoke(
    city="Beijing",
    weather="sunny",
    temperature="25°C",
    prompt_template=[
        ("system", "你是一个天气预报员。"),
        ("user", "今天{city}的天气是{weather}，温度是{temperature}。请描述一下今天的天气情况。")
    ]
))
print("\n")

# Example 5: Direct graph invocation (original way)
print("Example 5: Direct graph invocation (original way)")
print("-" * 50)
result = graph.invoke({
    "messages": [HumanMessage(content="Generate content")],
    "template_params": {
        "language": "English",
        "subject": "space",
        "type": "story"
    }
})
print(result["messages"][-1].content) 