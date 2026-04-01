"""
FAISS-backed RAG helpers shared by MCP tools (lookup_docs, bingchuan, inspect_faiss).

Index path: faiss/faiss_index/ (run build_faiss_index.py after editing docs/).
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

## ⬇️ Load env from full-stack-deepagents/.env
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env", override=True)
load_dotenv(find_dotenv(), override=True)

_MODULE_DIR = Path(__file__).resolve().parent
FAISS_INDEX_PATH = _MODULE_DIR / "faiss" / "faiss_index"

RAG_PROMPT = """仅依赖下面的context回答用户的问题:
Context: {context}

Question: {question}
"""

_lock = threading.Lock()
_retriever = None
_rag_chain = None
_embeddings = None
_vectorstore = None


def _ensure_loaded() -> None:
    global _retriever, _rag_chain, _embeddings, _vectorstore
    with _lock:
        if _rag_chain is not None:
            return
        if not FAISS_INDEX_PATH.is_dir():
            raise FileNotFoundError(
                f"FAISS index not found at {FAISS_INDEX_PATH}. "
                "Run build_faiss_index.py from mcp-server-rag after installing dependencies."
            )
        _embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE") or os.getenv("OPENAI_BASE_URL"),
            openai_organization=os.getenv("OPENAI_ORG_ID"),
        )
        _vectorstore = FAISS.load_local(
            str(FAISS_INDEX_PATH), _embeddings, allow_dangerous_deserialization=True
        )
        _retriever = _vectorstore.as_retriever(k=7)
        prompt = ChatPromptTemplate.from_template(RAG_PROMPT)
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE") or os.getenv("OPENAI_BASE_URL"),
            openai_organization=os.getenv("OPENAI_ORG_ID"),
        )
        _rag_chain = (
            RunnablePassthrough.assign(
                context=lambda x: "\n\n".join(
                    d.page_content for d in _retriever.invoke(x["question"])
                )
            )
            | prompt
            | llm
            | StrOutputParser()
        )


def answer_from_docs(question: str) -> str:
    """Run the RAG chain on a single question (same backend for lookup_docs and bingchuan)."""
    _ensure_loaded()
    assert _rag_chain is not None
    return _rag_chain.invoke({"question": question})


def inspect_faiss_text(max_chunks: int | None = 200, max_chars_per_chunk: int = 4000) -> str:
    """Return a text dump of index chunks for operators (bounded size)."""
    _ensure_loaded()
    assert _vectorstore is not None
    lines: list[str] = [
        f"FAISS index: {FAISS_INDEX_PATH} ({len(_vectorstore.index_to_docstore_id)} chunks)\n",
        "=" * 80,
    ]
    n = 0
    for i, doc_id in sorted(
        _vectorstore.index_to_docstore_id.items(), key=lambda x: x[0]
    ):
        if max_chunks is not None and n >= max_chunks:
            lines.append(f"\n... truncated after {max_chunks} chunks ...")
            break
        doc = _vectorstore.docstore.search(doc_id)
        source = doc.metadata.get("source", "N/A")
        headers = {k: v for k, v in doc.metadata.items() if k.startswith("Header")}
        body = doc.page_content
        if len(body) > max_chars_per_chunk:
            body = body[:max_chars_per_chunk] + "\n... [truncated]"
        lines.append(f"\n--- Chunk {i + 1} ---\nSource: {source}")
        if headers:
            lines.append(f"Headers: {headers}")
        lines.append(body)
        n += 1
    return "\n".join(lines)
