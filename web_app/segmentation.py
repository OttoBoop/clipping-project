from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

from .config import DATA_DIR


DEFAULT_VIEWER_PROFILES: dict[str, dict[str, Any]] = {
    "flavio": {
        "label": "Flavio Valle",
        "target_keys": ["flavio_valle", "pedro_angelito", "bernardo_rubiao", "pedro_duarte"],
        "default_targets": ["flavio_valle", "pedro_angelito"],
    },
    "shakira": {
        "label": "Show da Shakira",
        "target_keys": ["shakira"],
        "default_targets": ["shakira"],
    },
    "rio_economico": {
        "label": "Rio Economico",
        "target_keys": ["rio_economico"],
        "default_targets": ["rio_economico"],
    },
    "demo_cliente": {
        "label": "Cliente Demo",
        "target_keys": [],
        "default_targets": [],
    },
}


def _normalize_profiles(parsed: Any) -> dict[str, dict[str, Any]]:
    try:
        raw_profiles = parsed.get("profiles") if isinstance(parsed, dict) and isinstance(parsed.get("profiles"), dict) else parsed
    except AttributeError:
        raw_profiles = parsed
    if not isinstance(raw_profiles, dict):
        return {}
    profiles: dict[str, dict[str, Any]] = {}
    for key, value in raw_profiles.items():
        profile_key = str(key or "").strip()
        if not profile_key:
            continue
        if isinstance(value, list):
            profiles[profile_key] = {
                "label": profile_key,
                "target_keys": [str(item).strip() for item in value if str(item).strip()],
                "default_targets": [],
            }
            continue
        if not isinstance(value, dict):
            continue
        target_keys = [
            str(item).strip()
            for item in (value.get("target_keys") or value.get("targetKeys") or [])
            if str(item).strip()
        ]
        default_targets = [
            str(item).strip()
            for item in (value.get("default_targets") or value.get("defaultTargets") or [])
            if str(item).strip()
        ]
        profiles[profile_key] = {
            "label": str(value.get("label") or profile_key),
            "target_keys": target_keys,
            "default_targets": default_targets,
        }
    return profiles


def _load_profiles_json(raw: str) -> dict[str, dict[str, Any]]:
    if not raw:
        return {}
    try:
        return _normalize_profiles(json.loads(raw))
    except json.JSONDecodeError:
        return {}


def _profiles_file_path() -> Path:
    configured = os.environ.get("CLIPPING_VIEWER_PROFILES_PATH", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return DATA_DIR / "viewer_profiles.json"


def _file_profiles() -> dict[str, dict[str, Any]]:
    path = _profiles_file_path()
    if not path.is_file():
        return {}
    try:
        return _load_profiles_json(path.read_text(encoding="utf-8"))
    except OSError:
        return {}


def _env_profiles() -> dict[str, dict[str, Any]]:
    raw = os.environ.get("CLIPPING_VIEWER_PROFILES", "").strip()
    if not raw:
        return {}
    return _load_profiles_json(raw)


def viewer_profiles_path() -> str:
    return str(_profiles_file_path())


def viewer_profiles_configured() -> bool:
    return bool(_file_profiles() or _env_profiles())


def viewer_profiles() -> dict[str, dict[str, Any]]:
    profiles = copy.deepcopy(DEFAULT_VIEWER_PROFILES)
    profiles.update(_file_profiles())
    profiles.update(_env_profiles())
    return profiles


def is_admin_session(session: dict[str, Any] | None) -> bool:
    return bool(session and str(session.get("role") or "admin") == "admin")


def session_profile_key(session: dict[str, Any] | None) -> str:
    return str((session or {}).get("profile") or ("admin" if is_admin_session(session) else "")).strip()


def profile_config(session: dict[str, Any] | None) -> dict[str, Any]:
    if is_admin_session(session):
        return {"label": "Admin", "target_keys": None, "default_targets": None}
    key = session_profile_key(session)
    return viewer_profiles().get(key, {"label": key or "Viewer", "target_keys": [], "default_targets": []})


def allowed_target_keys(session: dict[str, Any] | None) -> set[str] | None:
    if is_admin_session(session):
        return None
    raw = profile_config(session).get("target_keys") or []
    return {str(key).strip() for key in raw if str(key).strip()}


def _target_allowed(key: str, allowed: set[str] | None) -> bool:
    return allowed is None or key in allowed


def _article_keys(article: dict[str, Any], story_keys: list[str], allowed: set[str] | None) -> list[str]:
    source = article.get("targetKeys") or article.get("target_keys") or story_keys
    keys: list[str] = []
    for raw in source or []:
        key = str(raw or "").strip()
        if key and _target_allowed(key, allowed) and key not in keys:
            keys.append(key)
    return keys


def scoped_targets_response(response: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    allowed = allowed_target_keys(session)
    targets = [
        copy.deepcopy(row)
        for row in response.get("targets", [])
        if _target_allowed(str(row.get("key") or ""), allowed)
    ]
    primary = [str(key) for key in response.get("primaryKeys", []) if _target_allowed(str(key), allowed)]
    return {"targets": targets, "primaryKeys": primary}


def scoped_dashboard_payload(payload: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    allowed = allowed_target_keys(session)
    if allowed is None:
        scoped = copy.deepcopy(payload)
        scoped.setdefault("meta", {})
        scoped["meta"].update({"viewerRole": "admin", "viewerProfile": "admin", "editorEnabled": True})
        return scoped

    scoped: dict[str, Any] = copy.deepcopy(payload)
    target_rows = [
        row for row in scoped.get("targets", [])
        if _target_allowed(str(row.get("key") or ""), allowed)
    ]
    target_keys = [str(row.get("key") or "") for row in target_rows if str(row.get("key") or "")]
    default_targets = [
        str(key) for key in scoped.get("defaultTargets", [])
        if str(key) in target_keys
    ] or list(target_keys)

    stories: list[dict[str, Any]] = []
    total_articles = 0
    total_ai = 0
    total_raw = 0
    for story in scoped.get("stories", []) or []:
        story_keys = [str(key) for key in story.get("targetKeys", []) if str(key).strip()]
        articles: list[dict[str, Any]] = []
        story_target_keys: list[str] = []
        for article in story.get("articles", []) or []:
            article_keys = _article_keys(article, story_keys, allowed)
            if not article_keys:
                continue
            article_copy = copy.deepcopy(article)
            article_copy["targetKeys"] = article_keys
            if isinstance(article_copy.get("classifications"), list):
                article_copy["classifications"] = [
                    row for row in article_copy["classifications"]
                    if str(row.get("target_key") or "") in article_keys
                ]
            articles.append(article_copy)
            for key in article_keys:
                if key not in story_target_keys:
                    story_target_keys.append(key)
        if not articles:
            continue
        story_copy = copy.deepcopy(story)
        story_copy["articles"] = articles
        story_copy["targetKeys"] = story_target_keys
        story_copy["articleCount"] = len(articles)
        story_copy["aiCount"] = sum(1 for article in articles if str(article.get("summarySource") or "").lower() == "ai")
        story_copy["rawCount"] = story_copy["articleCount"] - story_copy["aiCount"]
        stories.append(story_copy)
        total_articles += story_copy["articleCount"]
        total_ai += story_copy["aiCount"]
        total_raw += story_copy["rawCount"]

    meta = copy.deepcopy(scoped.get("meta") or {})
    profile = profile_config(session)
    meta.update(
        {
            "viewerRole": "viewer",
            "viewerProfile": session_profile_key(session),
            "viewerLabel": str(profile.get("label") or session_profile_key(session)),
            "editorEnabled": False,
            "totalStories": len(stories),
            "totalArticles": total_articles,
            "totalAi": total_ai,
            "totalRaw": total_raw,
            "initialStoryCount": len(stories),
            "initialArticleCount": total_articles,
            "initialAiCount": total_ai,
            "initialRawCount": total_raw,
        }
    )
    scoped["meta"] = meta
    scoped["targets"] = target_rows
    scoped["defaultTargets"] = default_targets
    scoped["stories"] = stories
    if "storyTargets" in scoped:
        scoped["storyTargets"] = {
            str(sid): [key for key in keys if _target_allowed(str(key), allowed)]
            for sid, keys in (scoped.get("storyTargets") or {}).items()
            if any(_target_allowed(str(key), allowed) for key in keys)
        }
    return scoped


def scoped_raw_texts(raw_texts: dict[str, Any], scoped_payload: dict[str, Any]) -> dict[str, Any]:
    allowed_keys: set[str] = set()
    for story in scoped_payload.get("stories", []) or []:
        for article in story.get("articles", []) or []:
            raw_key = str(article.get("rawTextKey") or "").strip()
            if raw_key:
                allowed_keys.add(raw_key)
    return {key: raw_texts[key] for key in allowed_keys if key in raw_texts}


def scoped_live_results(data: dict[str, Any], session: dict[str, Any], *, requested_target_key: str = "") -> dict[str, Any]:
    allowed = allowed_target_keys(session)
    if allowed is None:
        return data
    items: list[dict[str, Any]] = []
    requested = str(requested_target_key or "").strip()
    if requested and requested not in allowed:
        return {**data, "items": [], "count": 0}
    for item in data.get("items", []) or []:
        keys = [str(key) for key in item.get("targetKeys", []) if str(key) in allowed]
        if requested and requested not in keys:
            continue
        if not keys:
            continue
        item_copy = copy.deepcopy(item)
        item_copy["targetKeys"] = keys
        labels = item_copy.get("targetLabels") or {}
        item_copy["targetLabels"] = {key: labels.get(key, key) for key in keys}
        items.append(item_copy)
    return {**data, "items": items, "count": len(items)}


def scoped_classifications(rows: list[dict[str, Any]], session: dict[str, Any]) -> list[dict[str, Any]]:
    allowed = allowed_target_keys(session)
    if allowed is None:
        return rows
    return [row for row in rows if str(row.get("target_key") or "") in allowed]


def scoped_status_response(status: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    if is_admin_session(session):
        return status
    current = status.get("current") if isinstance(status.get("current"), dict) else {}
    return {
        "current": {
            "status": str(current.get("status") or "idle"),
            "profile": session_profile_key(session),
        },
        "recent": [],
    }
