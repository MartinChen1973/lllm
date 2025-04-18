# 1. 演示如何借助搜索引擎来回答用户的问题
#    搜索引擎可提供实时信息，尤其是在模型生成之后才出现的信息。

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

from dotenv import load_dotenv, find_dotenv

# Load the API key from the .env file   从.env文件中加载API密钥
load_dotenv(find_dotenv())

# Create the retriever from url 从url创建检索器
loader = WebBaseLoader("https://docs.smith.langchain.com/overview")
docs = loader.load()
embeddings = OpenAIEmbeddings()
text_splitter = RecursiveCharacterTextSplitter()
documents = text_splitter.split_documents(docs)
vector_store = FAISS.from_documents(documents, embeddings)
retriever = vector_store.as_retriever()

# Create a prompt 创建提示词
# template = """仅依赖下面的context回答用户的问题，如果前后文没有查到相关内容，请告知用户。
template = """回答用户的问题。
Context：{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)
model = ChatOpenAI(model="gpt-4o-mini")
# model = ChatOpenAI(model = "gpt-4") # 如果由于问题复杂，导致实验效果不佳，请使用gpt-4模型
output_parser = StrOutputParser()

setup_and_retrieval = RunnableParallel(  # RunnableParallel是一个并行运行多个Runnable的工具。它可以将多个Runnable组合成一个并行的处理流程，以实现更复杂的任务或功能。
    {
        "context": retriever,  # 用retriever处理输入问题，输出放入context字段
        "question": RunnablePassthrough(),
    }  # 把输入问题，不加处理传送到question字段
)
chain = setup_and_retrieval | prompt | model | output_parser

# Questions
question = "请问感冒了应该怎么办？"
result = chain.invoke(question)
print(f"Q: {question}\nA: {result}")

question = "请问特朗普赢得了2024大选吗？"
result = chain.invoke(question)
print(f"Q: {question}\nA: {result}")