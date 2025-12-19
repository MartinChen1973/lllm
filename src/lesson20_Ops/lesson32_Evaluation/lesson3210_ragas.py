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
    llm=OpenAI(model="gpt-5-nano"),
    embeddings=DashScopeEmbeddings(model="text-embedding-v3")
)

print("Evaluation results:")
print(score.to_pandas())