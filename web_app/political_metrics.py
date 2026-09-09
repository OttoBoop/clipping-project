"""Bounded JSON worker telemetry. No URLs, credentials, text or exception messages."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
import math
import os
from pathlib import Path
import re
import threading
import time

OPERATIONS = frozenset({"task", "http", "http_body", "throttle_wait", "extraction", "object_upload"})
OUTCOMES = frozenset({"ok", "error", "saved", "duplicate", "no_match", "outside_window", "complete",
                      "continue", "split", "gap", "backpressure", "lease_lost", "retryable", "metadata_only", "failed"})
KINDS = frozenset({"discovery", "fetch", "review"})
MAX_SERIES = 256
_local = threading.local()
_log = logging.getLogger("political_metrics")


def _sources() -> set[str]:
    try:
        data = json.loads((Path(__file__).resolve().parents[1] / "data/political_sources_v1.json").read_text())
        return {row["key"] for row in data.get("sources", []) if isinstance(row.get("key"), str)
                and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", row["key"])} | {"_review"}
    except (OSError, ValueError, TypeError, KeyError):
        return {"_review"}


def _milliseconds(seconds) -> float:
    try:
        value = float(seconds) * 1000
        return max(0.0, value) if math.isfinite(value) else 0.0
    except (TypeError, ValueError, OverflowError):
        return 0.0


def _outcome(value) -> str:
    return value if isinstance(value, str) and value in OUTCOMES else "other"


def _status(value) -> int:
    return value if isinstance(value, int) and 100 <= value <= 599 else 0


def _emit(event: str, **fields) -> None:
    _log.info(json.dumps({"event": event, "timestamp": datetime.now(timezone.utc).isoformat(),
                          "processId": os.getpid(), **fields}, separators=(",", ":"), allow_nan=False))


def configure_logging() -> None:
    """Keep each metric log line independently parseable as JSON on Render."""
    if not any(getattr(handler, "political_metrics_handler", False) for handler in _log.handlers):
        handler = logging.StreamHandler()
        handler.political_metrics_handler = True
        handler.setFormatter(logging.Formatter("%(message)s"))
        _log.addHandler(handler)
    _log.setLevel(logging.INFO)
    _log.propagate = False


class Collector:
    def __init__(self, *, allowed_sources=None, max_series=MAX_SERIES):
        self.allowed_sources = frozenset(_sources() if allowed_sources is None else allowed_sources)
        self.max_series = max(2, min(MAX_SERIES, int(max_series)))
        self._lock = threading.Lock()
        self._rows = {}

    def source(self, value) -> str:
        return value if isinstance(value, str) and value in self.allowed_sources else "unknown"

    def observe(self, kind: str, source: str, operation: str, milliseconds: float,
                outcome: str = "ok", status_code: int = 0) -> None:
        key = (kind if kind in KINDS else "unknown", self.source(source),
               operation if operation in OPERATIONS else "other", _outcome(outcome), _status(status_code))
        with self._lock:
            if key not in self._rows and len(self._rows) >= self.max_series - 1:
                key = ("unknown", "unknown", "other", "other", 0)
            row = self._rows.setdefault(key, {"count": 0, "durationMs": 0.0, "maxMs": 0.0})
            row["count"] += 1
            row["durationMs"] += milliseconds
            row["maxMs"] = max(row["maxMs"], milliseconds)

    def drain(self, interval_seconds: float) -> list[dict]:
        with self._lock:
            rows, self._rows = self._rows, {}
        interval = max(float(interval_seconds), .001)
        return [{"kind": key[0], "source": key[1], "operation": key[2], "outcome": key[3],
                 "httpStatus": key[4], "count": row["count"], "durationMs": round(row["durationMs"], 2),
                 "meanMs": round(row["durationMs"] / row["count"], 2), "maxMs": round(row["maxMs"], 2),
                 "perSecond": round(row["count"] / interval, 4), "intervalSeconds": round(interval, 3)}
                for key, row in sorted(rows.items())]


collector = Collector()


@dataclass
class Measurement:
    status_code: int = 0
    outcome: str = "ok"


@dataclass
class TaskMeasurement:
    kind: str
    source: str
    task_id: int | None
    collector: Collector
    outcome: str = "error"
    operations: dict = field(default_factory=dict)


def record_timing(operation: str, elapsed_seconds: float, *, status_code=None, outcome="ok") -> None:
    context = getattr(_local, "task", None)
    if context is None:
        return
    operation = operation if operation in OPERATIONS else "other"
    if operation == "http" and _status(status_code) >= 400 and outcome == "ok":
        outcome = "error"
    duration = _milliseconds(elapsed_seconds)
    context.collector.observe(context.kind, context.source, operation, duration, outcome, status_code)
    row = context.operations.setdefault(operation, {"count": 0, "durationMs": 0.0})
    row["count"] += 1
    row["durationMs"] = round(row["durationMs"] + duration, 2)


@contextmanager
def timed_operation(operation: str):
    measured = Measurement()
    started = time.monotonic()
    try:
        yield measured
    except BaseException:
        measured.outcome = "error"
        raise
    finally:
        record_timing(operation, time.monotonic() - started,
                      status_code=measured.status_code, outcome=measured.outcome)


@contextmanager
def task_metrics(task: dict, *, metrics: Collector | None = None):
    metrics = metrics or collector
    measured = TaskMeasurement(kind=task.get("kind") if task.get("kind") in KINDS else "unknown",
                               source=metrics.source(task.get("source_key")),
                               task_id=task.get("id") if isinstance(task.get("id"), int) else None,
                               collector=metrics)
    previous = getattr(_local, "task", None)
    _local.task = measured
    started = time.monotonic()
    try:
        yield measured
    except BaseException:
        measured.outcome = "error"
        raise
    finally:
        duration = _milliseconds(time.monotonic() - started)
        outcome = _outcome(measured.outcome)
        metrics.observe(measured.kind, measured.source, "task", duration, outcome)
        _emit("political_task_duration", kind=measured.kind, source=measured.source,
              taskId=measured.task_id, outcome=outcome, durationMs=round(duration, 2), operations=measured.operations)
        _local.task = previous


def report_interval(interval_seconds: float) -> None:
    for row in collector.drain(interval_seconds):
        _emit("political_worker_metrics", **row)


def reporting_loop(stop: threading.Event, *, interval_seconds: float = 30) -> None:
    started = time.monotonic()
    while not stop.wait(interval_seconds):
        current = time.monotonic()
        report_interval(current - started)
        started = current
    report_interval(time.monotonic() - started)
