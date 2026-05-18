from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import HTTPException, Request

from .segmentation import viewer_profiles


COOKIE_NAME = "clipping_admin"
SESSION_SECONDS = 8 * 60 * 60
PUBLIC_EMPTY_DEMO_PROFILE = "demo_cliente"
PUBLIC_EMPTY_DEMO_PASSWORD = "demo-cliente"


def _env_value(name: str) -> str:
    return os.environ.get(name, "").strip()


def auth_configured() -> bool:
    return bool(_env_value("CLIPPING_ADMIN_PASSWORD") and _env_value("CLIPPING_SESSION_SECRET"))


def viewer_auth_configured() -> bool:
    return bool(viewer_passwords() and _env_value("CLIPPING_SESSION_SECRET"))


def public_empty_demo_configured() -> bool:
    return bool(public_empty_demo_passwords() and _env_value("CLIPPING_SESSION_SECRET"))


def login_configured() -> bool:
    return bool(
        _env_value("CLIPPING_SESSION_SECRET")
        and (_env_value("CLIPPING_ADMIN_PASSWORD") or viewer_passwords() or public_empty_demo_passwords())
    )


def missing_auth_config() -> list[str]:
    missing: list[str] = []
    if not _env_value("CLIPPING_SESSION_SECRET"):
        missing.append("CLIPPING_SESSION_SECRET")
    if not _env_value("CLIPPING_ADMIN_PASSWORD"):
        missing.append("CLIPPING_ADMIN_PASSWORD")
    if not viewer_passwords():
        missing.append("CLIPPING_VIEWER_PASSWORDS")
    return missing


def _secret() -> bytes:
    value = _env_value("CLIPPING_SESSION_SECRET")
    if not value:
        raise HTTPException(status_code=503, detail="login_auth_not_configured")
    return value.encode("utf-8")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _sign(payload: str) -> str:
    return _b64(hmac.new(_secret(), payload.encode("ascii"), hashlib.sha256).digest())


def make_session(username: str = "admin", *, role: str = "admin", profile: str = "admin") -> str:
    payload = _b64(
        json.dumps(
            {
                "sub": username,
                "role": role,
                "profile": profile,
                "exp": int(time.time()) + SESSION_SECONDS,
            },
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return f"{payload}.{_sign(payload)}"


def verify_session(token: str | None) -> dict[str, Any] | None:
    if not token or "." not in token or not login_configured():
        return None
    payload, sig = token.split(".", 1)
    if not hmac.compare_digest(_sign(payload), sig):
        return None
    try:
        data = json.loads(_unb64(payload).decode("utf-8"))
    except Exception:
        return None
    if int(data.get("exp") or 0) < int(time.time()):
        return None
    return data


def check_password(password: str) -> bool:
    expected = _env_value("CLIPPING_ADMIN_PASSWORD")
    return bool(expected) and hmac.compare_digest(password, expected)


def viewer_passwords() -> dict[str, str]:
    raw = _env_value("CLIPPING_VIEWER_PASSWORDS")
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        result: dict[str, str] = {}
        for profile, value in parsed.items():
            key = str(profile or "").strip()
            if not key:
                continue
            password = ""
            if isinstance(value, str):
                password = value.strip()
            elif isinstance(value, dict):
                password = str(value.get("password") or "").strip()
            if password:
                result[key] = password
        return result

    result: dict[str, str] = {}
    for chunk in raw.split(";"):
        if "=" not in chunk:
            continue
        profile, password = chunk.split("=", 1)
        profile = profile.strip()
        password = password.strip()
        if profile and password:
            result[profile] = password
    return result


def _truthy_env(name: str) -> bool:
    return _env_value(name).lower() in {"1", "true", "yes", "on"}


def _profile_target_keys(profile: str) -> list[str]:
    row = viewer_profiles().get(profile, {})
    values = row.get("target_keys") if isinstance(row, dict) else []
    return [str(value).strip() for value in values if str(value).strip()]


def public_empty_demo_passwords() -> dict[str, str]:
    if _truthy_env("CLIPPING_DISABLE_PUBLIC_EMPTY_DEMO"):
        return {}
    if viewer_passwords() and not _truthy_env("CLIPPING_ENABLE_PUBLIC_EMPTY_DEMO_WITH_REAL_VIEWERS"):
        return {}
    password = _env_value("CLIPPING_EMPTY_DEMO_PASSWORD") or PUBLIC_EMPTY_DEMO_PASSWORD
    if not password:
        return {}
    if _profile_target_keys(PUBLIC_EMPTY_DEMO_PROFILE):
        return {}
    return {PUBLIC_EMPTY_DEMO_PROFILE: password}


def login_identity(password: str) -> dict[str, str] | None:
    if check_password(password):
        return {"sub": "admin", "role": "admin", "profile": "admin"}
    for profile, expected in viewer_passwords().items():
        if hmac.compare_digest(str(password or ""), expected):
            return {"sub": profile, "role": "viewer", "profile": profile}
    for profile, expected in public_empty_demo_passwords().items():
        if hmac.compare_digest(str(password or ""), expected):
            return {"sub": profile, "role": "viewer", "profile": profile}
    return None


def require_admin(request: Request) -> dict[str, Any]:
    if not auth_configured():
        raise HTTPException(status_code=503, detail="admin_auth_not_configured")
    session = verify_session(request.cookies.get(COOKIE_NAME))
    if not session or str(session.get("role") or "admin") != "admin":
        raise HTTPException(status_code=401, detail="admin_login_required")
    return session


def require_viewer(request: Request) -> dict[str, Any]:
    if not login_configured():
        raise HTTPException(status_code=503, detail="login_auth_not_configured")
    session = verify_session(request.cookies.get(COOKIE_NAME))
    if not session:
        raise HTTPException(status_code=401, detail="viewer_login_required")
    return session


def csrf_token(session_token: str | None) -> str:
    if not session_token:
        return ""
    return _b64(hmac.new(_secret(), f"csrf:{session_token}".encode("utf-8"), hashlib.sha256).digest())


def require_csrf(request: Request) -> None:
    session_token = request.cookies.get(COOKIE_NAME)
    expected = csrf_token(session_token)
    provided = request.headers.get("x-csrf-token", "")
    if not expected or not hmac.compare_digest(expected, provided):
        raise HTTPException(status_code=403, detail="csrf_check_failed")
