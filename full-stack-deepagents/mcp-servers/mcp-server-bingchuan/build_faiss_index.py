"""
Build FAISS vector store from documents in docs/ (Bingchuan ice cream corpus).

Embeds with OpenAI and writes faiss/faiss_index/ plus index_manifest.json.
"""

import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_STACK_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_STACK_ROOT))

from dotenv import find_dotenv, load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv(_STACK_ROOT / ".env", override=True)
load_dotenv(find_dotenv(), override=True)

from utilities.rag_faiss.faiss_sync import full_rebuild
from utilities.rag_faiss.manifest import manifest_path_default

DOCS_PATH = _SCRIPT_DIR / "docs"
FAISS_INDEX_PATH = _SCRIPT_DIR / "faiss" / "faiss_index"
MANIFEST_PATH = manifest_path_default(FAISS_INDEX_PATH)

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_API_BASE") or os.getenv("OPENAI_BASE_URL"),
    openai_organization=os.getenv("OPENAI_ORG_ID"),
)
summary = full_rebuild(DOCS_PATH, FAISS_INDEX_PATH, MANIFEST_PATH, embeddings)
print(f"FAISS index saved to {FAISS_INDEX_PATH} ({summary})")
