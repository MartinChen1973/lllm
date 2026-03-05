# 1. 演示如何通过封装来简化代码（单个文件）

import os

# Fix OpenMP conflict: allow multiple OpenMP runtimes to coexist
# This is needed when using FAISS with other libraries that use OpenMP
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
from langchain_tools.retriever.LangChainRetriever import LangChainRetriever

# Load the API key from the .env file   从.env文件中加载API密钥
load_dotenv(find_dotenv(), override=True)


# Langchain_tools question and context  -----------------------------------
path = "src/legacy_v0.3/_lesson00_Langchain/lesson03_RAG_basic/md/leave_policy.md"
print(f"Attempting to load from path: {path}")
print(f"Path exists: {os.path.exists(path)}")
print(f"Is file: {os.path.isfile(path)}")
print(f"Is directory: {os.path.isdir(path)}")
if os.path.exists(path):
    print(f"Absolute path: {os.path.abspath(path)}")
question_and_context = LangChainRetriever.create_question_and_context_from_path(path)

# Create a prompt 创建提示词
template = """仅依赖下面的context回答用户的问题:
Context：{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)
model = ChatOpenAI(model="gpt-5-nano")
parser = StrOutputParser()

chain = question_and_context | prompt | model | parser

# Questions
questions = [
    "请问找谁请病假？",
    # "需要什么证明文件吗？",
    # "最多可以请几天呢？"
]

for question in questions:
    result = chain.invoke(question)
    print(f"Q: {question}\nA: {result}")
