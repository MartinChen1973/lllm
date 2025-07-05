# 1. 演示.env文件中的API密钥使用
# 2. 演示model创建的参数差异
# 3. 查看response的详细内容
 
# Load the API key from the .env file (#010) 从.env文件中加载API密钥
from dotenv import load_dotenv, find_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 从当前文件夹或父文件夹中加载.env文件的配置（成为全局可访问的静态变量）。
load_dotenv(find_dotenv())

# Define the state structure 定义状态结构
class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    # 消息具有"list"类型。注释中的`add_messages`函数定义了如何更新此状态键
    # （在这种情况下，它将消息附加到列表中，而不是覆盖它们）
    messages: Annotated[list, add_messages]

# Create the graph builder 创建图构建器
graph_builder = StateGraph(State)

# Create the OpenAI chatbot 创建聊天机器人
# model或llm是大语言模型Large Language Model的缩写。ChatOpenAI是一个用于与OpenAI或与之兼容的其他模型交互的类。
model = ChatOpenAI(model="gpt-4o-mini")  # Better and cheaper.
# llm = ChatOpenAI(model="gpt-4o")  # Better but expensive.
# llm = ChatOpenAI(model="gemma-7b-it")
print("model:" + "-"*30)
print(model)

# Define the chatbot node function 定义聊天机器人节点函数
# Define the chatbot node function 定义聊天机器人节点函数
def chatbot(state: State):
    return {"messages": [model.invoke(state["messages"])]}

# Add the START/chatbot/END nodeS to the graph 将聊天机器人节点添加到图中
graph_builder.add_node("chatbot", chatbot)

# Add edges to define the flow 添加边来定义流程
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Compile the graph 编译图
graph = graph_builder.compile()
print("graph:" + "-"*30)

# For demonstration, let's use the regular invoke method
result = graph.invoke({
    "messages": [HumanMessage(content="Please say 'Hello world!'")]
})

# Print the response 打印回复
print("result:" + "-"*30)
print(result) 
