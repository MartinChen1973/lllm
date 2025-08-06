# 演示如何使用OpenAI API创建一个简单的聊天机器人，以便在控制台中打印"hello world!"。

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model

# 从当前文件夹或父文件夹中加载.env文件的配置（成为全局可访问的静态变量）。
load_dotenv(find_dotenv())

# model或llm是大语言模型Large Language Model的缩写。init_chat_model是一个用于初始化聊天模型的函数。
llm = init_chat_model("openai:gpt-4o-mini")

# Start the chatbot and get the response 启动聊天机器人并获得回复
response = llm.invoke("Please say 'Hello world!'")

# Print the response 打印回复
print(response.content)
