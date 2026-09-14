"""Source identities and collection permissions, without rewriting archived rows."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
PSD_PROFILE = "psd_rj_2026"


def catalog_sources() -> list[dict]:
    rows = json.loads((DATA / "political_sources_v1.json").read_text())["sources"]
    extra = DATA / "political_sources_expansion_v1.json"
    if extra.exists():
        value = json.loads(extra.read_text())
        rows += value["sources"] if isinstance(value, dict) else value
    unique = {}
    for row in rows:
        if row["key"] in unique:
            raise ValueError("duplicate_source_key")
        unique[row["key"]] = row
    return list(unique.values())


def allowed_sources(profile: str = "") -> list[dict]:
    return [row for row in catalog_sources()
            if not row.get("allowed_profiles") or profile in row["allowed_profiles"]]


def select_sources(requested, profile: str = "") -> list[dict]:
    available = {row["key"]: row for row in allowed_sources(profile) if row.get("enabled", True)}
    if requested is None:
        return list(available.values())
    if not isinstance(requested, list) or not requested or any(not isinstance(k, str) for k in requested):
        raise ValueError("select_allowed_sources")
    if set(requested) - available.keys():
        raise ValueError("source_access_denied")
    return [available[key] for key in sorted(set(requested))]


def source_snapshot(rows: list[dict]) -> dict:
    canonical = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"source_keys": sorted(row["key"] for row in rows), "source_snapshots": rows,
            "source_catalog_version": hashlib.sha256(canonical.encode()).hexdigest()}


def source_aliases(source_key: str, rows: list[dict] | None = None) -> list[str]:
    for row in catalog_sources() if rows is None else rows:
        aliases = [row["key"], *row.get("legacy_source_keys", [])]
        if row.get("domain"):
            aliases.append("publisher:" + row["domain"].removeprefix("www."))
        if source_key in aliases:
            return list(dict.fromkeys(aliases))
    return [source_key]


def source_for_task(task: dict) -> dict | None:
    snapshot = task.get("source_snapshot")
    if snapshot:
        return snapshot
    return next((row for row in catalog_sources() if row["key"] == task["source_key"]), None)
