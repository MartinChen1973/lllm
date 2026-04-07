## ⬇️ Markdown discovery and chunking (matches legacy build_faiss_index pipelines).

from __future__ import annotations

from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

_MD_HEADERS = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
    ("####", "Header 4"),
]


def iter_markdown_paths(docs_root: Path) -> list[Path]:
    ## ⬇️ Sorted stable order for reproducible manifests.
    root = docs_root.resolve()
    if not root.is_dir():
        return []
    return sorted(root.glob("**/*.md"))


def split_markdown_documents(paths: list[Path]) -> list[Document]:
    ## ⬇️ Per-file TextLoader so metadata source matches incremental sync deletes.
    md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=_MD_HEADERS)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits: list[Document] = []
    for path in paths:
        loader = TextLoader(str(path.resolve()), encoding="utf-8")
        docs = loader.load()
        for doc in docs:
            md_splits = md_splitter.split_text(doc.page_content)
            for s in md_splits:
                s.metadata.update(doc.metadata)
                splits.append(s)
    return text_splitter.split_documents(splits)


def split_all_under_docs(docs_root: Path) -> list[Document]:
    return split_markdown_documents(iter_markdown_paths(docs_root))
