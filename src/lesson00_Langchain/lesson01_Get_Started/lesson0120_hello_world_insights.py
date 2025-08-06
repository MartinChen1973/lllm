# 1. 演示.env文件中的API密钥使用
# 2. 演示model创建的参数差异
# 3. 查看response的详细内容
 
# Load the API key from the .env file (#010) 从.env文件中加载API密钥
from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model

# 从当前文件夹或父文件夹中加载.env文件的配置（成为全局可访问的静态变量）。
load_dotenv(find_dotenv())
# Create the OpenAI chatbot 创建聊天机器人
# model或llm是大语言模型Large Language Model的缩写。init_chat_model是一个用于初始化聊天模型的函数。

llm = init_chat_model("openai:gpt-4o-mini") # Fast and cheap.
# llm = init_chat_model("openai:gpt-4o") # Better but expensive.
# llm = init_chat_model("gemma:gemma-7b-it")
print("========= MODEL INFO =========")
print(llm)

# Start the chatbot and get the response 启动聊天机器人并获得回复
response = llm.invoke("say 'hello worlld !'")
# response = llm.stream("say 'hello worlld !'")
# response = llm.batch(["say 'hello worlld !'", "say 'hello Bob !'",])
# print(response)

# Print the response
print("========= RESPONSE =========")
print(response)
