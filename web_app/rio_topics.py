from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.matcher import Target

from .config import ROOT


RIO_ECONOMICO_SCOPE = "rio_economico"
RIO_TOURISM_TOPIC = "tourism_events"
RIO_TOURISM_CONFIG_PATH = ROOT / "data" / "topic_configs" / "rio_economico_tourism_events_v1.json"


@dataclass(frozen=True)
class RioTopicConfig:
    version: str
    scope: str
    topic: str
    dimension: str
    label: str
    target: Target
    queries: tuple[dict[str, Any], ...]
    forced_terms: tuple[str, ...]
    required_terms: tuple[str, ...]
    exclude_title_terms: tuple[str, ...]
    exclude_body_terms: tuple[str, ...]
    source_queries: tuple[str, ...]


def _clean_list(values: Any) -> tuple[str, ...]:
    if not isinstance(values, list):
        return ()
    return tuple(str(item).strip() for item in values if str(item).strip())


def _load_config_payload(path: Path = RIO_TOURISM_CONFIG_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("rio_topic_config_invalid")
    return payload


def load_rio_tourism_config(path: Path = RIO_TOURISM_CONFIG_PATH) -> RioTopicConfig:
    payload = _load_config_payload(path)
    scope = str(payload.get("scope") or "").strip()
    topic = str(payload.get("topic") or "").strip()
    if scope != RIO_ECONOMICO_SCOPE or topic != RIO_TOURISM_TOPIC:
        raise ValueError("rio_topic_config_scope_mismatch")

    target_payload = payload.get("target") if isinstance(payload.get("target"), dict) else {}
    target_key = str(target_payload.get("key") or "").strip()
    if target_key != RIO_ECONOMICO_SCOPE:
        raise ValueError("rio_topic_target_must_be_rio_economico")

    raw_queries = payload.get("queries")
    if not isinstance(raw_queries, list) or not raw_queries:
        raise ValueError("rio_topic_queries_required")

    queries: list[dict[str, Any]] = []
    for index, row in enumerate(raw_queries):
        if not isinstance(row, dict):
            continue
        query = str(row.get("query") or "").strip()
        if not query:
            continue
        queries.append(
            {
                "index": index,
                "group": str(row.get("group") or "tourism").strip() or "tourism",
                "query": query,
                "weight": float(row.get("weight") or 1.0),
                "why": str(row.get("why") or "").strip(),
            }
        )
    if not queries:
        raise ValueError("rio_topic_queries_required")

    label = str(payload.get("label") or "Turismo Rio").strip()
    target = Target(
        key=target_key,
        label=str(target_payload.get("label") or label).strip(),
        display_name=str(target_payload.get("display_name") or label).strip(),
        keywords=list(_clean_list(target_payload.get("keywords"))),
        exact_aliases=list(_clean_list(target_payload.get("exact_aliases"))),
        primary=bool(target_payload.get("primary")),
        priority=int(target_payload.get("priority") or 2),
    )
    return RioTopicConfig(
        version=str(payload.get("version") or path.stem).strip(),
        scope=scope,
        topic=topic,
        dimension=str(payload.get("dimension") or topic).strip(),
        label=label,
        target=target,
        queries=tuple(queries),
        forced_terms=_clean_list(payload.get("forced_terms")),
        required_terms=_clean_list(payload.get("required_terms")),
        exclude_title_terms=_clean_list(payload.get("exclude_title_terms")),
        exclude_body_terms=_clean_list(payload.get("exclude_body_terms")),
        source_queries=_clean_list(payload.get("source_queries")),
    )


def is_rio_tourism_request(payload: dict[str, Any]) -> bool:
    scope = str(payload.get("scope") or payload.get("target_scope") or "").strip()
    topic = str(payload.get("topic") or payload.get("topic_key") or "").strip()
    preset = str(payload.get("preset") or "").strip()
    return bool(
        (scope == RIO_ECONOMICO_SCOPE and topic == RIO_TOURISM_TOPIC)
        or preset in {"rio_tourism", "rio_tourism_canary"}
    )


def rio_tourism_query_texts(config: RioTopicConfig | None = None) -> list[str]:
    cfg = config or load_rio_tourism_config()
    return [str(row["query"]) for row in cfg.queries]


def rio_tourism_source_query_texts(config: RioTopicConfig | None = None) -> list[str]:
    cfg = config or load_rio_tourism_config()
    return list(cfg.source_queries or rio_tourism_query_texts(cfg))


def rio_topic_target_snapshot(config: RioTopicConfig | None = None) -> dict[str, Any]:
    cfg = config or load_rio_tourism_config()
    target = cfg.target
    return {
        "key": target.key,
        "label": target.label,
        "display_name": target.display_name,
        "keywords": list(target.keywords or []),
        "exact_aliases": list(target.exact_aliases or []),
        "className": target.className,
        "primary": bool(target.primary),
        "priority": int(target.priority or 2),
        "topic_scope": cfg.scope,
        "topic": cfg.topic,
        "topic_dimension": cfg.dimension,
        "topic_config_version": cfg.version,
    }


def rio_topic_labels() -> dict[str, str]:
    cfg = load_rio_tourism_config()
    return {cfg.scope: cfg.label}
