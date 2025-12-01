# 1. 演示LlamaIndex的OpenAILike的使用
# 2. 演示qwen3-30b-a3b模型的使用

# Load the API key from the .env file (#010) 从.env文件中加载API密钥
import os

from dotenv import load_dotenv, find_dotenv
from llama_index.llms.openai_like import OpenAILike

# 从当前文件夹或父文件夹中加载.env文件的配置（成为全局可访问的静态变量）。
load_dotenv(find_dotenv())

# Create the OpenAI chatbot 创建聊天机器人
# model或llm是大语言模型Large Language Model的缩写。这里使用LlamaIndex的OpenAI LLM。
llm = OpenAILike(
    model="qwen3-30b-a3b",
    api_key=os.getenv("OPENAI_API_KEY"),
    api_base=os.getenv("OPENAI_API_BASE"),
    is_chat_model=True,
    context_window=32768
)  # Fast and cheap.

# llm = OpenAI(model="gpt-5-nano") # Fast and cheap.
# llm = OpenAI(model="gpt-5") # Better but expensive.
# llm = OpenAI(model="gemma-7b-it")
print("========= MODEL INFO =========")
print(llm)

# Start the chatbot and get the response 启动聊天机器人并获得回复
response = llm.complete("say 'hello worlld !'")

# LlamaIndex does not have stream or batch in the same way as LangChain, so we comment them out.
# response = llm.stream("say 'hello worlld !'")
# response = llm.batch(["say 'hello worlld !'", "say 'hello Bob !'",])
# print(response)

# Print the response
print("========= RESPONSE =========")
print(response)
