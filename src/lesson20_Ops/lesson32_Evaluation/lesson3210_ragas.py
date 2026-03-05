from langchain_community.embeddings import DashScopeEmbeddings
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_correctness
import pandas as pd

import os
from dotenv import load_dotenv, find_dotenv

# 从当前文件夹或父文件夹中加载.env文件的配置（成为全局可访问的静态变量）。
load_dotenv(find_dotenv(), override=True)


# ===================================
# Load data from CSV file
csv_file_path = os.path.join(os.path.dirname(__file__), 'data_samples.csv')
df = pd.read_csv(csv_file_path)
data_samples = df.to_dict('list')

print("Loading dataset for evaluation...")
print(f"Dataset shape: {len(data_samples['question'])} questions")

dataset = Dataset.from_dict(data_samples)

print("Evaluating with Ragas...")
score = evaluate(
    dataset = dataset,
    metrics=[answer_correctness],
    llm=ChatOpenAI(model="gpt-5-nano"),
    embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    # embeddings=DashScopeEmbeddings(model="text-embedding-v3")
)

print("Evaluation results:")
print(score.to_pandas())