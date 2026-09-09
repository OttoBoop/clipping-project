"""Shared bounded capacity for worker threads and PostgreSQL task claims."""
import os


def fetch_concurrency() -> int:
    try:
        configured = int(os.environ.get("POLITICAL_FETCH_CONCURRENCY", "4"))
    except (TypeError, ValueError):
        return 4
    return max(1, min(6, configured))
