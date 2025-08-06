# 演示如何使用LlamaIndex创建一个简单的聊天机器人，以便在控制台中打印"hello world!"。

from dotenv import load_dotenv, find_dotenv
from llama_index.core.llms import ChatMessage, LLM
from llama_index.llms.openai import OpenAI

# 从当前文件夹或父文件夹中加载.env文件的配置（成为全局可访问的静态变量）。
load_dotenv(find_dotenv())

# model或llm是大语言模型Large Language Model的缩写。这里使用LlamaIndex的OpenAI LLM。
llm = OpenAI(model="gpt-4o-mini")

# Start the chatbot and get the response 启动聊天机器人并获得回复
response = llm.complete("Please say 'Hello world!'")

# Print the response 打印回复
print(response.text)
