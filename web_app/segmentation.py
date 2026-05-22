from __future__ import annotations

import copy
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from .config import DATA_DIR


class ViewerProfileError(ValueError):
    """Raised when a viewer profile mutation cannot be applied.

    Carries a stable `code` (used by the API to map to a 400 payload),
    a human-readable `message`, and an optional `field` pointing the
    UI to the input that needs correcting.
    """

    def __init__(self, code: str, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field


PROFILE_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_]{1,31}$")


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
    file_profiles = _file_profiles()
    if file_profiles:
        # When the admin has written profiles to the file, it becomes the
        # source of truth — archiving works by removing keys, which would
        # be defeated if defaults kept resurrecting them.
        profiles = file_profiles
    else:
        profiles = copy.deepcopy(DEFAULT_VIEWER_PROFILES)
    profiles.update(_env_profiles())
    return profiles


def _write_profiles_file(profiles: dict[str, dict[str, Any]]) -> None:
    path = _profiles_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"profiles": profiles}
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _cleaned_target_keys(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple)):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in values:
        key = str(item or "").strip()
        if key and key not in seen:
            cleaned.append(key)
            seen.add(key)
    return cleaned


def _ensure_writable_profiles() -> dict[str, dict[str, Any]]:
    """Return a mutable copy of the current profile set, materialising
    defaults if the file is empty so subsequent writes do not implicitly
    drop them on disk.
    """
    file_profiles = _file_profiles()
    if file_profiles:
        return copy.deepcopy(file_profiles)
    return copy.deepcopy(DEFAULT_VIEWER_PROFILES)


def set_viewer_profile(
    profile_key: str,
    label: str,
    target_keys: list[str],
    default_targets: list[str] | None = None,
    *,
    create: bool = False,
) -> dict[str, Any]:
    """Create or update a viewer profile entry on disk.

    Validates the profile key (lowercase letters, digits, underscore; 2–32
    chars) and the target list, then writes the full profile map atomically.
    Raises ViewerProfileError with a stable code so the API layer can map it
    to a structured 400 response.
    """
    key = str(profile_key or "").strip().lower()
    if not key:
        raise ViewerProfileError("viewer_profile_invalid", "Identificador do cliente é obrigatório.", field="profile")
    if not PROFILE_KEY_RE.match(key):
        raise ViewerProfileError(
            "viewer_profile_invalid",
            "Use só letras minúsculas, números e _ (2 a 32 caracteres) — sem espaços.",
            field="profile",
        )

    label_clean = str(label or "").strip()
    if len(label_clean) < 2:
        raise ViewerProfileError("viewer_profile_invalid", "Nome do cliente precisa de pelo menos 2 caracteres.", field="label")

    target_clean = _cleaned_target_keys(target_keys)
    default_clean = _cleaned_target_keys(default_targets if default_targets is not None else target_clean)
    if default_clean and not all(item in target_clean for item in default_clean):
        raise ViewerProfileError(
            "viewer_profile_invalid",
            "Targets padrão precisam estar contidos na lista de targets visíveis.",
            field="default_targets",
        )

    profiles = _ensure_writable_profiles()
    exists = key in profiles
    if create and exists:
        raise ViewerProfileError(
            "viewer_profile_conflict",
            f'Já existe um cliente com identificador "{key}". Use editar ou escolha outro identificador.',
            field="profile",
        )
    if not create and not exists:
        raise ViewerProfileError(
            "viewer_profile_not_found",
            f'Cliente "{key}" não encontrado. Crie o cliente antes de editar.',
            field="profile",
        )

    profiles[key] = {
        "label": label_clean,
        "target_keys": target_clean,
        "default_targets": default_clean or list(target_clean),
    }
    _write_profiles_file(profiles)
    return {"profile": key, **profiles[key]}


def add_target_to_profile(profile_key: str, target_key: str) -> dict[str, Any]:
    """Add target_key to profile's target_keys, atomically.

    Used when admin in simulation mode (`?as_profile=X`) creates or promotes a
    target — the target_keys list is patched in-place so the profile sees the
    new target on next dashboard load. Idempotent: re-adding an existing key
    is a no-op.
    """
    key = str(profile_key or "").strip().lower()
    target = str(target_key or "").strip()
    if not key:
        raise ViewerProfileError("viewer_profile_invalid", "Identificador do cliente é obrigatório.", field="profile")
    if not target:
        raise ViewerProfileError("viewer_profile_invalid", "Identificador do target é obrigatório.", field="target_key")

    profiles = _ensure_writable_profiles()
    if key not in profiles:
        raise ViewerProfileError(
            "viewer_profile_not_found",
            f'Cliente "{key}" não encontrado.',
            field="profile",
        )

    entry = profiles[key] or {}
    target_keys = list(entry.get("target_keys") or [])
    if target not in target_keys:
        target_keys.append(target)
        entry["target_keys"] = target_keys
        profiles[key] = entry
        _write_profiles_file(profiles)
    return {"profile": key, **entry}


def remove_target_from_profile(profile_key: str, target_key: str) -> dict[str, Any]:
    """Remove target_key from profile's target_keys, atomically.

    Used when admin in simulation mode archives or demotes a target out of the
    profile's scope. Also strips the key from `default_targets` to keep
    invariants (default ⊆ target_keys). Idempotent.
    """
    key = str(profile_key or "").strip().lower()
    target = str(target_key or "").strip()
    if not key:
        raise ViewerProfileError("viewer_profile_invalid", "Identificador do cliente é obrigatório.", field="profile")
    if not target:
        raise ViewerProfileError("viewer_profile_invalid", "Identificador do target é obrigatório.", field="target_key")

    profiles = _ensure_writable_profiles()
    if key not in profiles:
        raise ViewerProfileError(
            "viewer_profile_not_found",
            f'Cliente "{key}" não encontrado.',
            field="profile",
        )

    entry = profiles[key] or {}
    target_keys = list(entry.get("target_keys") or [])
    defaults = list(entry.get("default_targets") or [])
    changed = False
    if target in target_keys:
        target_keys = [k for k in target_keys if k != target]
        entry["target_keys"] = target_keys
        changed = True
    if target in defaults:
        defaults = [k for k in defaults if k != target]
        entry["default_targets"] = defaults
        changed = True
    if changed:
        profiles[key] = entry
        _write_profiles_file(profiles)
    return {"profile": key, **entry}


def archive_viewer_profile(profile_key: str) -> dict[str, Any]:
    """Remove a viewer profile from the on-disk profile file.

    Raises ViewerProfileError if the profile is missing or is the admin
    pseudo-profile (which is not a viewer).
    """
    key = str(profile_key or "").strip().lower()
    if not key:
        raise ViewerProfileError("viewer_profile_invalid", "Identificador do cliente é obrigatório.", field="profile")
    if key == "admin":
        raise ViewerProfileError("viewer_profile_invalid", "O perfil admin não pode ser arquivado.", field="profile")

    profiles = _ensure_writable_profiles()
    if key not in profiles:
        raise ViewerProfileError(
            "viewer_profile_not_found",
            f'Cliente "{key}" não encontrado.',
            field="profile",
        )
    removed = profiles.pop(key)
    _write_profiles_file(profiles)
    return {"profile": key, **removed}


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
        # Admin path: only mutation is meta annotation. copy.deepcopy of a
        # multi-MiB payload (462+ stories, 784+ articles) was pure waste —
        # measured ~25 MiB RSS bump per /assets/clipping-data.json hit in
        # prod (2026-05-22). We shallow-copy the top-level dict so the
        # caller's payload is never mutated; meta is a new dict so updates
        # don't leak either.
        scoped = dict(payload)
        existing_meta = scoped.get("meta") or {}
        scoped["meta"] = {**existing_meta, "viewerRole": "admin", "viewerProfile": "admin", "editorEnabled": True}
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
