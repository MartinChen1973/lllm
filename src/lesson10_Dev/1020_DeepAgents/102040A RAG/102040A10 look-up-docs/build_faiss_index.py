"""
Build FAISS vector store from documents.

Loads documents from docs/, splits them, embeds with OpenAI,
and persists the FAISS index to faiss/faiss_index/ for use by the agent script.
Run this script first whenever documents change.
"""

from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv(find_dotenv(), override=True)

## ⬇️ Resolve paths relative to this script (docs and faiss/faiss_index in look-up-docs)
_SCRIPT_DIR = Path(__file__).resolve().parent
DOCS_PATH = _SCRIPT_DIR / "docs"
FAISS_INDEX_PATH = _SCRIPT_DIR / "faiss" / "faiss_index"

## ⬇️ Load documents from docs (markdown files)
loader = DirectoryLoader(
    str(DOCS_PATH),
    glob="**/*.[mp][d]",  # 支持加载 .md 和 .pdf 文件
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
    show_progress=True,
)
docs = loader.load()

## ⬇️ Split into chunks for retrieval (markdown-aware by headers, then by size)
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
## ⬇️ Further split oversized chunks to fit retrieval context
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(splits)

## ⬇️ Embed and store with FAISS
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS.from_documents(splits, embeddings)

## ⬇️ Persist FAISS index to disk
FAISS_INDEX_PATH.mkdir(parents=True, exist_ok=True)
vectorstore.save_local(str(FAISS_INDEX_PATH))
print(f"FAISS index saved to {FAISS_INDEX_PATH} ({len(splits)} chunks)")
