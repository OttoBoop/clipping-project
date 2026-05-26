from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request

from .config import ROOT
from .segmentation import viewer_profiles


COOKIE_NAME = "clipping_admin"
SESSION_SECONDS = 8 * 60 * 60
CREDENTIALS_PATH = ROOT / "data" / "clipping_credentials.json"
PUBLIC_EMPTY_DEMO_PROFILE = "demo_cliente"
PUBLIC_EMPTY_DEMO_PASSWORD = "demo-cliente"


def _env_value(name: str) -> str:
    return os.environ.get(name, "").strip()


PASSWORD_HASH_PREFIX = "pbkdf2_sha256$"
PASSWORD_HASH_ROUNDS = 310_000


def _hash_password(plain: str) -> str:
    """Hash a password for storage in clipping_credentials.json.

    Returns a string like `pbkdf2_sha256$<rounds>$<salt_b64>$<hash_b64>`.
    The implementation uses hashlib.pbkdf2_hmac with SHA-256 — stdlib only,
    no new dependency — and a per-password 16-byte random salt.
    """
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, PASSWORD_HASH_ROUNDS)
    return f"{PASSWORD_HASH_PREFIX}{PASSWORD_HASH_ROUNDS}${base64.urlsafe_b64encode(salt).decode('ascii').rstrip('=')}${base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')}"


def _verify_password(plain: str, stored: str) -> bool:
    """Compare a plaintext password against a stored value.

    Accepts both hashed values (with `pbkdf2_sha256$...` prefix) and bare
    plaintext (for backward compatibility with env-var-defined passwords).
    """
    if not stored:
        return False
    if stored.startswith(PASSWORD_HASH_PREFIX):
        try:
            _, rounds_s, salt_b64, hash_b64 = stored.split("$", 3)
            rounds = int(rounds_s)
            salt = base64.urlsafe_b64decode(salt_b64 + "=" * (-len(salt_b64) % 4))
            expected = base64.urlsafe_b64decode(hash_b64 + "=" * (-len(hash_b64) % 4))
        except (ValueError, hashlib.UnsupportedAlgorithm if hasattr(hashlib, "UnsupportedAlgorithm") else Exception):
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, rounds)
        return hmac.compare_digest(candidate, expected)
    return hmac.compare_digest(plain, stored)


def _load_credentials_file() -> dict[str, Any] | None:
    """Return parsed credentials JSON, or None if missing/corrupt.

    Schema: {"admin_password": str, "viewer_passwords": {profile: password}}
    """
    if not CREDENTIALS_PATH.is_file():
        return None
    try:
        data = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _write_credentials_file(data: dict[str, Any]) -> None:
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{CREDENTIALS_PATH.name}.", suffix=".tmp", dir=str(CREDENTIALS_PATH.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, CREDENTIALS_PATH)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _file_admin_password() -> str:
    data = _load_credentials_file()
    if not data:
        return ""
    return str(data.get("admin_password") or "").strip()


def _file_viewer_passwords() -> dict[str, str]:
    data = _load_credentials_file()
    if not data:
        return {}
    raw = data.get("viewer_passwords") or {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, str] = {}
    for profile, value in raw.items():
        key = str(profile or "").strip()
        if not key:
            continue
        password = str(value or "").strip() if isinstance(value, str) else ""
        if password:
            result[key] = password
    return result


def credentials_source() -> str:
    """Return 'file' if credentials file is present and non-empty, else 'env'."""
    file_admin = _file_admin_password()
    file_viewers = _file_viewer_passwords()
    if file_admin or file_viewers:
        return "file"
    return "env"


def auth_configured() -> bool:
    has_admin = bool(_file_admin_password() or _env_value("CLIPPING_ADMIN_PASSWORD"))
    return has_admin and bool(_env_value("CLIPPING_SESSION_SECRET"))


def viewer_auth_configured() -> bool:
    return bool(viewer_passwords() and _env_value("CLIPPING_SESSION_SECRET"))


def public_empty_demo_configured() -> bool:
    return bool(public_empty_demo_passwords() and _env_value("CLIPPING_SESSION_SECRET"))


def login_configured() -> bool:
    has_any_password = bool(
        _file_admin_password()
        or _env_value("CLIPPING_ADMIN_PASSWORD")
        or viewer_passwords()
        or public_empty_demo_passwords()
    )
    return bool(_env_value("CLIPPING_SESSION_SECRET")) and has_any_password


def missing_auth_config() -> list[str]:
    missing: list[str] = []
    if not _env_value("CLIPPING_SESSION_SECRET"):
        missing.append("CLIPPING_SESSION_SECRET")
    if not (_file_admin_password() or _env_value("CLIPPING_ADMIN_PASSWORD")):
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
    expected = _file_admin_password() or _env_value("CLIPPING_ADMIN_PASSWORD")
    return _verify_password(password, expected)


def viewer_passwords() -> dict[str, str]:
    file_viewers = _file_viewer_passwords()
    if file_viewers:
        return file_viewers
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
    """Return the public demo profile's login pwd if exposed.

    Two modes, in order of precedence:

    1. **CLIPPING_DEMO_PUBLIC=1 (new, 2026-05-22)** — demo is exposed even
       with real viewers configured and even with target_keys assigned.
       Used pra landing page institucional onde o demo é a versão default
       acessível sem senha digitada (vitrine).

    2. **Legacy "empty demo"** — demo só se torna público se NÃO houver
       viewers reais (a menos que ..._WITH_REAL_VIEWERS=1 esteja setada)
       E se demo NÃO tiver target_keys configurado. Mantido pra não
       quebrar deploys que dependiam desse comportamento.

    Both modes respect CLIPPING_DISABLE_PUBLIC_EMPTY_DEMO=1 (kill switch).
    """
    if _truthy_env("CLIPPING_DISABLE_PUBLIC_EMPTY_DEMO"):
        return {}
    password = _env_value("CLIPPING_EMPTY_DEMO_PASSWORD") or PUBLIC_EMPTY_DEMO_PASSWORD
    if not password:
        return {}
    if _truthy_env("CLIPPING_DEMO_PUBLIC"):
        return {PUBLIC_EMPTY_DEMO_PROFILE: password}
    # Legacy "empty demo" gating
    if viewer_passwords() and not _truthy_env("CLIPPING_ENABLE_PUBLIC_EMPTY_DEMO_WITH_REAL_VIEWERS"):
        return {}
    if _profile_target_keys(PUBLIC_EMPTY_DEMO_PROFILE):
        return {}
    return {PUBLIC_EMPTY_DEMO_PROFILE: password}


def is_demo_session(session: dict[str, Any] | None) -> bool:
    """True if session identifies the public demo profile.

    Used pra read-only enforcement nos endpoints de mutação: demo public
    pode ler tudo, mas não pode adicionar/arquivar/promover/rebaixar nada
    nem trocar senha — defense in depth (front também esconde).
    """
    if not session:
        return False
    return str(session.get("profile") or "") == PUBLIC_EMPTY_DEMO_PROFILE


def require_not_demo(session: dict[str, Any]) -> None:
    """Raise 403 if session is the public demo. Use em endpoints de mutação."""
    if is_demo_session(session):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "demo_readonly",
                "message": "Modo demo é só leitura. Quer testar mutações? Falar comigo no LinkedIn.",
            },
        )


def set_admin_password(new_password: str) -> None:
    """Persist a new admin password to the credentials file.

    Migrates the existing env-var-defined viewer passwords into the file on the
    first write so a fresh `data/clipping_credentials.json` does not erase them.
    """
    cleaned = str(new_password or "").strip()
    if len(cleaned) < 3:
        raise ValueError("Senha precisa de pelo menos 3 caracteres.")
    data = _load_credentials_file() or {}
    if not data.get("viewer_passwords"):
        env_viewers = viewer_passwords()
        if env_viewers:
            data["viewer_passwords"] = {p: _hash_password(v) for p, v in env_viewers.items()}
    data["admin_password"] = _hash_password(cleaned)
    _write_credentials_file(data)


def set_viewer_password(profile: str, new_password: str) -> None:
    """Persist a new password for an existing viewer profile."""
    profile_key = str(profile or "").strip()
    if not profile_key:
        raise ValueError("Perfil obrigatorio.")
    cleaned = str(new_password or "").strip()
    if len(cleaned) < 3:
        raise ValueError("Senha precisa de pelo menos 3 caracteres.")
    data = _load_credentials_file() or {}
    viewers = dict(data.get("viewer_passwords") or {})
    if not viewers:
        env_viewers = viewer_passwords()
        viewers = {p: _hash_password(v) for p, v in env_viewers.items()}
    viewers[profile_key] = _hash_password(cleaned)
    data["viewer_passwords"] = viewers
    if not data.get("admin_password"):
        env_admin = _env_value("CLIPPING_ADMIN_PASSWORD")
        if env_admin:
            data["admin_password"] = _hash_password(env_admin)
    _write_credentials_file(data)


def remove_viewer_password(profile: str) -> bool:
    """Delete a viewer profile's password from the credentials file.

    Returns True if a password was removed; False if no entry existed.
    """
    profile_key = str(profile or "").strip()
    if not profile_key:
        return False
    data = _load_credentials_file() or {}
    viewers = dict(data.get("viewer_passwords") or {})
    if profile_key not in viewers:
        return False
    viewers.pop(profile_key, None)
    data["viewer_passwords"] = viewers
    if not data.get("admin_password"):
        env_admin = _env_value("CLIPPING_ADMIN_PASSWORD")
        if env_admin:
            data["admin_password"] = _hash_password(env_admin)
    _write_credentials_file(data)
    return True


def has_viewer_password(profile: str) -> bool:
    """Return True when the given viewer profile has a stored password
    (in the credentials file or fallback env var).
    """
    profile_key = str(profile or "").strip()
    if not profile_key:
        return False
    return bool(viewer_passwords().get(profile_key))


def login_identity(password: str) -> dict[str, str] | None:
    if check_password(password):
        return {"sub": "admin", "role": "admin", "profile": "admin"}
    for profile, expected in viewer_passwords().items():
        if _verify_password(str(password or ""), expected):
            return {"sub": profile, "role": "viewer", "profile": profile}
    for profile, expected in public_empty_demo_passwords().items():
        if _verify_password(str(password or ""), expected):
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
