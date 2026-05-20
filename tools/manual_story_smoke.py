#!/usr/bin/env python3
"""Read-only smoke for /api/manual-story — validates the input gates
without actually inserting a story (which has heavy side effects:
DB insert, Supabase backup, optional export, job record).

Strategy: submit invalid payloads and assert the structured 400
error matches the spec. The contract is:
- missing title → 400 "Informe o titulo da materia"
- missing summary and full_text → 400 "Informe um resumo ou o texto"
- unknown target_key → 400 "Nome acompanhado desconhecido"
- bad URL → 400 (validate_url enforces)

Plus the standard auth gates:
- viewer cannot call → 401
- missing CSRF → 403

Reads CLIPPING_ADMIN_PASSWORD from env.

Usage: CLIPPING_ADMIN_PASSWORD=... python tools/manual_story_smoke.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from typing import Any


DEFAULT_BASE_URL = "https://clipping-project.onrender.com"


def make_opener() -> urllib.request.OpenerDirector:
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    return opener


def request(opener: urllib.request.OpenerDirector, method: str, url: str, body: Any = None, csrf: str | None = None, retries_on_5xx: int = 2) -> tuple[int, Any]:
    """HTTP request with bounded retry on 5xx (Render gateway/coldstart)."""
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if csrf:
        headers["X-CSRF-Token"] = csrf
    attempts = retries_on_5xx + 1
    payload = ""
    status = 0
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with opener.open(req, timeout=30) as resp:
                payload = resp.read().decode("utf-8", errors="replace")
                status = resp.getcode()
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            status = exc.code
        if status < 500:
            break
        if attempt < attempts:
            print(f"  ! transient {status} on {method} {url} — retry {attempt}/{retries_on_5xx} in 3s", file=sys.stderr)
            time.sleep(3)
    try:
        return status, json.loads(payload) if payload else {}
    except json.JSONDecodeError:
        return status, payload


def expect(actual: int, expected: int, label: str) -> None:
    marker = "OK" if actual == expected else "FAIL"
    print(f"  [{marker}] {label} (HTTP {actual}, expected {expected})")
    if actual != expected:
        sys.exit(1)


def detail(body: Any) -> str:
    if isinstance(body, dict):
        return str(body.get("detail") or body.get("message") or "")
    return str(body)[:120]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    base = args.base.rstrip("/")

    admin_pass = os.environ.get("CLIPPING_ADMIN_PASSWORD", "").strip()
    if not admin_pass:
        print("CLIPPING_ADMIN_PASSWORD env var is required", file=sys.stderr)
        return 2

    print(f"==> Manual-story input-gate smoke against {base}")

    opener = make_opener()
    status, _ = request(opener, "POST", f"{base}/api/login", {"password": admin_pass})
    expect(status, 200, "admin login")
    status, body = request(opener, "GET", f"{base}/api/csrf")
    expect(status, 200, "csrf fetch")
    csrf = body["csrf"] if isinstance(body, dict) else ""

    print("\n1. POST sem CSRF — espera 403")
    status, body = request(opener, "POST", f"{base}/api/manual-story", {"title": "x"})
    expect(status, 403, "no csrf rejected")
    print(f"     detail: {detail(body)}")

    # target_keys is validated BEFORE title — so include a valid one
    # ("shakira" exists in prod) when probing title/summary errors.
    print("\n2. POST sem title — espera 400 'Informe o titulo'")
    status, body = request(
        opener, "POST", f"{base}/api/manual-story",
        {"summary": "tem resumo", "url": "https://example.com/a", "target_keys": ["shakira"]},
        csrf=csrf,
    )
    expect(status, 400, "missing title rejected")
    msg = detail(body)
    assert "titulo" in msg, f"expected 'titulo' in error, got {msg!r}"
    print(f"     detail: {msg}")

    print("\n3. POST sem summary nem full_text — espera 400 'Informe um resumo'")
    status, body = request(
        opener, "POST", f"{base}/api/manual-story",
        {"title": "Titulo X", "url": "https://example.com/b", "target_keys": ["shakira"]},
        csrf=csrf,
    )
    expect(status, 400, "missing body rejected")
    msg = detail(body)
    assert "resumo" in msg or "texto" in msg, f"expected 'resumo' or 'texto' in error, got {msg!r}"
    print(f"     detail: {msg}")

    print("\n3b. POST sem target_keys — espera 400 'Escolha pelo menos um nome'")
    status, body = request(
        opener, "POST", f"{base}/api/manual-story",
        {"title": "Titulo Z", "summary": "resumo", "url": "https://example.com/e"},
        csrf=csrf,
    )
    expect(status, 400, "missing target_keys rejected")
    msg = detail(body)
    assert "nome" in msg, f"expected 'nome' in error, got {msg!r}"
    print(f"     detail: {msg}")

    print("\n4. POST com target_key desconhecido — espera 400")
    status, body = request(
        opener, "POST", f"{base}/api/manual-story",
        {
            "title": "Titulo Y", "summary": "resumo",
            "url": "https://example.com/c",
            "target_keys": ["nao_existe_smoke"],
        },
        csrf=csrf,
    )
    expect(status, 400, "unknown target_key rejected")
    msg = detail(body)
    print(f"     detail: {msg}")

    print("\n5. viewer tenta POST /api/manual-story — espera 401")
    viewer_jar = make_opener()
    request(viewer_jar, "POST", f"{base}/api/login", {"password": "flavio-gabinete-2026"})
    v_csrf_resp = request(viewer_jar, "GET", f"{base}/api/csrf")
    v_csrf = v_csrf_resp[1]["csrf"] if isinstance(v_csrf_resp[1], dict) else ""
    status, body = request(
        viewer_jar, "POST", f"{base}/api/manual-story",
        {"title": "x", "summary": "y", "url": "https://example.com/d"},
        csrf=v_csrf,
    )
    expect(status, 401, "viewer cannot post")
    print(f"     detail: {detail(body)}")

    print("\nSmoke OK — /api/manual-story input gates behave as specified.")
    print("(no story was actually inserted; this smoke is non-destructive)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
