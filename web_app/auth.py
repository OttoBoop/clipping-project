from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import HTTPException, Request


COOKIE_NAME = "clipping_admin"
SESSION_SECONDS = 8 * 60 * 60


def auth_configured() -> bool:
    return bool(os.environ.get("CLIPPING_ADMIN_PASSWORD") and os.environ.get("CLIPPING_SESSION_SECRET"))


def _secret() -> bytes:
    value = os.environ.get("CLIPPING_SESSION_SECRET", "")
    if not value:
        raise HTTPException(status_code=503, detail="admin_auth_not_configured")
    return value.encode("utf-8")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _sign(payload: str) -> str:
    return _b64(hmac.new(_secret(), payload.encode("ascii"), hashlib.sha256).digest())


def make_session(username: str = "admin") -> str:
    payload = _b64(
        json.dumps(
            {"sub": username, "exp": int(time.time()) + SESSION_SECONDS},
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return f"{payload}.{_sign(payload)}"


def verify_session(token: str | None) -> dict[str, Any] | None:
    if not token or "." not in token or not auth_configured():
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
    expected = os.environ.get("CLIPPING_ADMIN_PASSWORD", "")
    return bool(expected) and hmac.compare_digest(password, expected)


def require_admin(request: Request) -> dict[str, Any]:
    if not auth_configured():
        raise HTTPException(status_code=503, detail="admin_auth_not_configured")
    session = verify_session(request.cookies.get(COOKIE_NAME))
    if not session:
        raise HTTPException(status_code=401, detail="admin_login_required")
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

