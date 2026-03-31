from langchain_community.embeddings import DashScopeEmbeddings
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness
)
import json
import pandas as pd

import os
from dotenv import load_dotenv, find_dotenv

# 从当前文件夹或父文件夹中加载.env文件的配置（成为全局可访问的静态变量）。
load_dotenv(find_dotenv(), override=True)


# ===================================
# Load data from JSON (supports per-row contexts for context_precision/recall demo)
# Ragas expects: question, answer, contexts (list of retrieved docs), ground_truth
data_dir = os.path.dirname(__file__)
json_path = os.path.join(data_dir, "data_samples.json")
with open(json_path, "r", encoding="utf-8") as f:
    records = json.load(f)
data_samples = {
    "question": [r["question"] for r in records],
    "answer": [r["answer"] for r in records],
    "ground_truth": [r["ground_truth"] for r in records],
    "contexts": [r["contexts"] for r in records],
}

print("Loading dataset for evaluation...")
print(f"Dataset shape: {len(data_samples['question'])} questions")

dataset = Dataset.from_dict(data_samples)

print("Evaluating with Ragas...")
score = evaluate(
    dataset = dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall, answer_correctness],
    llm=ChatOpenAI(model="gpt-5-nano"),
    embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    # embeddings=DashScopeEmbeddings(model="text-embedding-v3")
)

# Output results to CSV
output_dir = os.path.dirname(__file__)
result_df = score.to_pandas().rename(columns={"reference": "ground_truth"})
csv_path = os.path.join(output_dir, "evaluation_results.csv")
result_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"Results saved to {csv_path}")