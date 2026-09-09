"""Temporary, process-local write drain for the legacy SQLite cutover."""
from __future__ import annotations

import os
import threading


_lock = threading.Lock()
_requests = 0


def legacy_write_fenced() -> bool:
    return os.environ.get("CLIPPING_LEGACY_WRITE_FENCE", "").strip() == "1"


def require_legacy_writes() -> None:
    if legacy_write_fenced():
        raise RuntimeError("legacy_write_fenced")


def begin_request() -> None:
    global _requests
    with _lock:
        _requests += 1


def end_request() -> None:
    global _requests
    with _lock:
        _requests -= 1


def in_flight_requests() -> int:
    with _lock:
        return _requests
