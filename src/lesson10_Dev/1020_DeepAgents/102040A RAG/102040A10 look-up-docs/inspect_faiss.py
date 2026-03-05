"""
Inspect FAISS vector store contents.

Loads the pre-built FAISS index from faiss/faiss_index/ and prints all stored
document chunks with their metadata. Use this to verify index contents
without binary inspection.
"""

import os
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv(find_dotenv(), override=True)

## ⬇️ Resolve FAISS index path (built by build_faiss_index.py)
_SCRIPT_DIR = Path(__file__).resolve().parent
FAISS_INDEX_PATH = _SCRIPT_DIR / "faiss" / "faiss_index"

## ⬇️ Load pre-built FAISS index
embeddings = OpenAIEmbeddings(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE"),
    organization=os.getenv("OPENAI_ORG_ID"),
)
vectorstore = FAISS.load_local(
    str(FAISS_INDEX_PATH), embeddings, allow_dangerous_deserialization=True
)

## ⬇️ Print all chunks with metadata
print(f"FAISS index: {FAISS_INDEX_PATH} ({len(vectorstore.index_to_docstore_id)} chunks)\n")
print("=" * 80)

for i, doc_id in vectorstore.index_to_docstore_id.items():
    doc = vectorstore.docstore.search(doc_id)
    source = doc.metadata.get("source", "N/A")
    headers = {k: v for k, v in doc.metadata.items() if k.startswith("Header")}
    print(f"--- Chunk {i + 1} ---")
    print(f"Source: {source}")
    if headers:
        print(f"Headers: {headers}")
    print(doc.page_content)
    print()
