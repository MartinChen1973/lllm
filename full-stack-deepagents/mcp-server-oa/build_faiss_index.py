"""
Build FAISS vector store from documents in docs/ (OA: org, leave policy).

Embeds with OpenAI and writes faiss/faiss_index/ for mcp-server-oa.
Run whenever markdown under docs/ changes.
"""

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

## ⬇️ Env from repo root .env
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env", override=True)
load_dotenv(find_dotenv(), override=True)

_SCRIPT_DIR = Path(__file__).resolve().parent
DOCS_PATH = _SCRIPT_DIR / "docs"
FAISS_INDEX_PATH = _SCRIPT_DIR / "faiss" / "faiss_index"

loader = DirectoryLoader(
    str(DOCS_PATH),
    glob="**/*.md",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
    show_progress=True,
)
docs = loader.load()

md_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ],
)
splits = []
for doc in docs:
    md_splits = md_splitter.split_text(doc.page_content)
    for s in md_splits:
        s.metadata.update(doc.metadata)
        splits.append(s)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(splits)

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_API_BASE") or os.getenv("OPENAI_BASE_URL"),
    openai_organization=os.getenv("OPENAI_ORG_ID"),
)
vectorstore = FAISS.from_documents(splits, embeddings)

FAISS_INDEX_PATH.mkdir(parents=True, exist_ok=True)
vectorstore.save_local(str(FAISS_INDEX_PATH))
print(f"FAISS index saved to {FAISS_INDEX_PATH} ({len(splits)} chunks)")
