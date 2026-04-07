## ⬇️ Shared FAISS RAG: splitting, manifest, incremental sync.

from .faiss_sync import full_rebuild, index_dir_has_faiss, sync_faiss_index
from .splitting import iter_markdown_paths, split_markdown_documents

__all__ = [
    "full_rebuild",
    "index_dir_has_faiss",
    "sync_faiss_index",
    "iter_markdown_paths",
    "split_markdown_documents",
]
