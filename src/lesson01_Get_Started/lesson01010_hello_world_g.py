# 演示如何使用OpenAI API创建一个简单的聊天机器人，以便在控制台中打印"hello world!"。

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
    messages: Annotated[list, add_messages]

# Create the graph builder 创建图构建器(graph = 流程图化的智能体)
graph_builder = StateGraph(State)

# Create the OpenAI chatbot 创建聊天机器人
model = ChatOpenAI("gpt-4o-mini")  # 默认是gpt-3.5

# Define the chatbot node function 定义聊天机器人节点函数
def chatbot(state: State):
    return {"messages": [model.invoke(state["messages"])]}

# Add the START/chatbot/END nodeS to the graph 将聊天机器人节点添加到图中
graph_builder.add_node("chatbot", chatbot)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Compile the graph 编译图
graph = graph_builder.compile()

# Invoke the graph with initial message 使用初始消息调用图
result = graph.invoke({
    "messages": [HumanMessage(content="Please say 'Hello world!'")]
})

# Print the response 打印回复
print(result["messages"][-1].content)
