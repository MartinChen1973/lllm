from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load the API key from the .env file 从.env文件中加载API密钥
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Prompt: create a prompt 创建提示词
prompt = ChatPromptTemplate.from_messages([ 
    ("system", "You are a warm-hearted AI assistant. You can only answer questions related to Scrum. If a question is not related to Scrum, politely refuse to answer."),
    ("user", "{input}")
])

# Model: Create the OpenAI chatbot 创建聊天机器人
model = ChatOpenAI(model="gpt-4o-mini")

# OutputParser: Create an output parser 创建输出解析器
output_parser = StrOutputParser() # "Output Parser"是指用于解析和处理模型输出的工具或系统。它通常用于将模型输出转换为可读的文本、结构化数据或其他形式，以便用户或其他系统能够理解和使用。

# Chain: Create and invoke a chain 创建并调用链
chain = prompt | model | output_parser # “|” 是链的连接符，用于将多个模型或系统连接成一个调用链。这种链式调用的方式可以将多个模型或系统组合成一个复杂的处理流程，以实现更复杂的任务或功能。

# Get user input 获取用户输入
user_input = input("Please enter your question: ")

# Invoke the chain 调用链
result = chain.invoke({"input": user_input})

# Print the response 打印回复
print(result)

