# 1. 演示使用参数化模板，限制用户输入的问题，以便更好地引导用户输入。

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load the API key from the .env file 从.env文件中加载API密钥
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Prompt: create a prompt 创建提示词
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个热心的AI作文助手。你写的作文总是不低于300字，不超过1000字。"),
    ("user", "请用{grade}的水平给我写一个关于{subject}的{type}，长度大约{size}字。") # 使用参数化模板，限制用户输入的问题，以便更好地引导用户输入。
])

# Model: Create the OpenAI chatbot 创建聊天机器人
llm = ChatOpenAI(model="gpt-4o-mini")

# OutputParser: Create an output parser 创建输出解析器
output_parser = StrOutputParser()

# Chain: Create and invoke a chain 创建并调用链
chain = prompt | llm | output_parser

# Invoke the chain 调用链
print(chain.invoke({"grade" : "小学三年级", "subject": "雪花", "type":"记叙文", "size":"500"}))
print(chain.invoke({"grade" : "初中三年级", "subject": "春节", "type":"说明文", "size":"600"}))
print(chain.invoke({"grade" : "高中三年级", "subject": "是否应该废除死刑", "type":"议论文", "size":"800"}))
