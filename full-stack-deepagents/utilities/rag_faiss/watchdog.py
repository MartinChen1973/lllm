## ⬇️ Optional filesystem watcher: debounced callback when *.md under docs/ changes.

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def start_markdown_watchdog(
    docs_root: Path,
    sync_fn: Callable[[], Any],
    *,
    debounce_sec: float = 0.6,
) -> Any | None:
    ## ⬇️ Returns watchdog Observer or None if watchdog is not installed or docs_root is missing.
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        logger.debug("watchdog not installed; skipping docs file watcher.")
        return None

    docs_root = docs_root.resolve()
    if not docs_root.is_dir():
        return None

    lock = threading.Lock()
    timer_holder: dict[str, threading.Timer | None] = {"t": None}

    def schedule() -> None:
        def fire() -> None:
            try:
                sync_fn()
            except Exception:
                logger.exception("Debounced RAG sync failed after docs/ change.")

        with lock:
            t_old = timer_holder["t"]
            if t_old is not None:
                t_old.cancel()
            t = threading.Timer(debounce_sec, fire)
            t.daemon = True
            timer_holder["t"] = t
            t.start()

    class _Handler(FileSystemEventHandler):
        def on_any_event(self, event: Any) -> None:
            if event.is_directory:
                return
            p = getattr(event, "dest_path", None) or getattr(event, "src_path", "")
            if not str(p).lower().endswith(".md"):
                return
            schedule()

    observer = Observer()
    observer.schedule(_Handler(), str(docs_root), recursive=True)
    observer.daemon = True
    observer.start()
    logger.info("RAG docs watchdog started on %s", docs_root)
    return observer
