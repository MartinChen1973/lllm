from langchain_community.llms.tongyi import Tongyi
from langchain_community.embeddings import DashScopeEmbeddings
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_correctness
import pandas as pd

import os
from dotenv import load_dotenv, find_dotenv
from llama_index.llms.openai import OpenAI

# 从当前文件夹或父文件夹中加载.env文件的配置（成为全局可访问的静态变量）。
load_dotenv(find_dotenv())

# Load the RAG system ===================================
from chatbot import rag
query_engine = rag.create_query_engine(rag.load_index())
print('提问：张伟是哪个部门的')
response = query_engine.query('张伟是哪个部门的')
print('回答：', end='')
response.print_response_stream()

# ===================================
# Load data from CSV file
csv_file_path = os.path.join(os.path.dirname(__file__), 'data_samples.csv')
df = pd.read_csv(csv_file_path)
data_samples = df.to_dict('list')

dataset = Dataset.from_dict(data_samples)
score = evaluate(
    dataset = dataset,
    metrics=[answer_correctness],
    llm=OpenAI(model="gpt-4o-mini"),
    embeddings=DashScopeEmbeddings(model="text-embedding-v3")
)
score.to_pandas()