## ⬇️ Incremental FAISS sync vs markdown under docs/ using index_manifest.json.

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any

from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

from .manifest import (
    classify_changes,
    disk_snapshot,
    load_manifest,
    manifest_path_default,
    save_manifest,
)
from .splitting import iter_markdown_paths, split_markdown_documents

logger = logging.getLogger(__name__)


def _paths_equal(a: str, b: str) -> bool:
    ## ⬇️ Match chunk metadata source to absolute file path (Windows case-insensitive).
    na = os.path.normpath(a)
    nb = os.path.normpath(b)
    if os.name == "nt":
        return os.path.normcase(na) == os.path.normcase(nb)
    return na == nb


def _rel_to_abs(docs_root: Path, rel_posix: str) -> Path:
    return (docs_root / Path(rel_posix)).resolve()


def _docstore_ids_for_absolute_source(vectorstore: FAISS, abs_path: Path) -> list[str]:
    want = str(abs_path)
    out: list[str] = []
    for doc_id in vectorstore.index_to_docstore_id.values():
        doc = vectorstore.docstore.search(doc_id)
        if doc is None:
            continue
        src = doc.metadata.get("source") or ""
        if _paths_equal(str(src), want):
            out.append(doc_id)
    return out


def index_dir_has_faiss(faiss_index_dir: Path) -> bool:
    ## ⬇️ Public helper for MCP stacks to detect a loadable LangChain FAISS folder.
    return (faiss_index_dir / "index.faiss").is_file()


def _clear_index_dir(faiss_index_dir: Path) -> None:
    if faiss_index_dir.is_dir():
        shutil.rmtree(faiss_index_dir)


def full_rebuild(
    docs_root: Path,
    faiss_index_dir: Path,
    manifest_file: Path,
    embeddings: Embeddings,
) -> dict[str, Any]:
    splits = split_markdown_documents(iter_markdown_paths(docs_root))
    if not splits:
        _clear_index_dir(faiss_index_dir)
        save_manifest(manifest_file, {})
        logger.info("RAG sync: no markdown under %s; cleared index.", docs_root)
        return {"action": "empty", "chunks": 0}

    vectorstore = FAISS.from_documents(splits, embeddings)
    faiss_index_dir.parent.mkdir(parents=True, exist_ok=True)
    _clear_index_dir(faiss_index_dir)
    faiss_index_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(faiss_index_dir))
    snap = disk_snapshot(docs_root)
    save_manifest(manifest_file, snap)
    logger.info(
        "RAG sync: full rebuild -> %s chunks, manifest %s keys.",
        len(splits),
        len(snap),
    )
    return {"action": "full", "chunks": len(splits)}


def sync_faiss_index(
    docs_root: Path,
    faiss_index_dir: Path,
    embeddings: Embeddings,
    *,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    ## ⬇️ Reconcile FAISS on disk with docs/ and manifest; returns a small summary dict.
    docs_root = docs_root.resolve()
    faiss_index_dir = faiss_index_dir.resolve()
    manifest_file = manifest_path or manifest_path_default(faiss_index_dir)
    disk = disk_snapshot(docs_root)

    if not index_dir_has_faiss(faiss_index_dir):
        return full_rebuild(docs_root, faiss_index_dir, manifest_file, embeddings)

    loaded = load_manifest(manifest_file)
    if loaded is None:
        logger.info("RAG sync: missing or invalid manifest; full rebuild.")
        return full_rebuild(docs_root, faiss_index_dir, manifest_file, embeddings)

    prev_files: dict[str, dict[str, int]] = loaded["files"]
    removed, added, updated = classify_changes(prev_files, disk)
    if not removed and not added and not updated:
        return {"action": "noop"}

    vectorstore = FAISS.load_local(
        str(faiss_index_dir),
        embeddings,
        allow_dangerous_deserialization=True,
    )

    deleted_ids: list[str] = []
    for rel in sorted(removed | updated):
        abs_p = _rel_to_abs(docs_root, rel)
        deleted_ids.extend(_docstore_ids_for_absolute_source(vectorstore, abs_p))
    unique_del: list[str] = []
    _seen: set[str] = set()
    for x in deleted_ids:
        if x not in _seen:
            _seen.add(x)
            unique_del.append(x)
    if unique_del:
        vectorstore.delete(unique_del)

    to_ingest = sorted(added | updated)
    new_chunks = 0
    for rel in to_ingest:
        p = docs_root / Path(rel)
        if not p.is_file():
            continue
        chunks = split_markdown_documents([p])
        if chunks:
            vectorstore.add_documents(chunks)
            new_chunks += len(chunks)

    if not vectorstore.index_to_docstore_id:
        ## ⬇️ LangChain cannot persist a zero-vector FAISS index; remove the directory instead.
        _clear_index_dir(faiss_index_dir)
        save_manifest(manifest_file, disk)
        logger.info("RAG sync: index empty after edits; removed faiss dir.")
        return {
            "action": "incremental",
            "removed": len(removed),
            "added": len(added),
            "updated": len(updated),
            "chunks_added": new_chunks,
            "index_cleared": True,
        }

    vectorstore.save_local(str(faiss_index_dir))
    save_manifest(manifest_file, disk)
    logger.info(
        "RAG sync: incremental removed=%s added=%s updated=%s new_chunks=%s",
        len(removed),
        len(added),
        len(updated),
        new_chunks,
    )
    return {
        "action": "incremental",
        "removed": len(removed),
        "added": len(added),
        "updated": len(updated),
        "chunks_added": new_chunks,
    }
