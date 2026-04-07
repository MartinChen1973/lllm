## ⬇️ JSON manifest: relative doc paths under docs/ to mtime_ns + size for incremental sync.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MANIFEST_VERSION = 1


def manifest_path_default(faiss_index_dir: Path) -> Path:
    ## ⬇️ Sibling of faiss_index/ under faiss/
    return faiss_index_dir.parent / "index_manifest.json"


def load_manifest(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if data.get("version") != MANIFEST_VERSION:
        return None
    files = data.get("files")
    if not isinstance(files, dict):
        return None
    return data


def save_manifest(path: Path, files: dict[str, dict[str, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": MANIFEST_VERSION, "files": files}
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def disk_snapshot(docs_root: Path) -> dict[str, dict[str, int]]:
    ## ⬇️ Keys are POSIX paths relative to docs_root.
    root = docs_root.resolve()
    out: dict[str, dict[str, int]] = {}
    if not root.is_dir():
        return out
    for p in sorted(root.glob("**/*.md")):
        st = p.stat()
        key = p.resolve().relative_to(root).as_posix()
        out[key] = {"mtime_ns": st.st_mtime_ns, "size": st.st_size}
    return out


def classify_changes(
    prev_files: dict[str, dict[str, int]],
    disk: dict[str, dict[str, int]],
) -> tuple[set[str], set[str], set[str]]:
    ## ⬇️ Returns (removed, added, updated) using relative keys.
    prev_keys = set(prev_files)
    disk_keys = set(disk)
    removed = prev_keys - disk_keys
    added = disk_keys - prev_keys
    updated: set[str] = set()
    for k in prev_keys & disk_keys:
        a, b = prev_files[k], disk[k]
        if a.get("mtime_ns") != b.get("mtime_ns") or a.get("size") != b.get("size"):
            updated.add(k)
    return removed, added, updated
