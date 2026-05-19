#!/usr/bin/env python3
"""End-to-end smoke for the /api/admin/viewers endpoints in production.

Exercises Goal 1 of the CCM-2026-05-19 loop (admin manages viewer clients
via UI without redeploy). Walks through:

  1. admin login + csrf
  2. list (capture baseline)
  3. create a throwaway viewer with a derived password
  4. log in as that viewer (separate cookie jar)
  5. patch the viewer (rename)
  6. archive the viewer
  7. confirm login fails after archive (HTTP 401)
  8. final list — throwaway must be gone

Passwords are read from the environment (CLIPPING_ADMIN_PASSWORD) and never
printed. Exits non-zero on any unexpected status.

Usage:
    CLIPPING_ADMIN_PASSWORD=... python tools/admin_viewers_smoke.py
    CLIPPING_ADMIN_PASSWORD=... python tools/admin_viewers_smoke.py --base http://localhost:8000
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


def make_opener() -> tuple[urllib.request.OpenerDirector, CookieJar]:
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    return opener, jar


def request(
    opener: urllib.request.OpenerDirector,
    method: str,
    url: str,
    *,
    body: dict[str, Any] | None = None,
    csrf: str | None = None,
) -> tuple[int, dict[str, Any] | str]:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if csrf:
        headers["X-CSRF-Token"] = csrf
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with opener.open(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
            status = resp.getcode()
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        status = exc.code
    parsed: dict[str, Any] | str
    try:
        parsed = json.loads(payload) if payload else {}
    except json.JSONDecodeError:
        parsed = payload
    return status, parsed


def expect(actual: int, expected: int, label: str) -> None:
    marker = "OK" if actual == expected else "FAIL"
    print(f"  [{marker}] {label} (HTTP {actual}, expected {expected})")
    if actual != expected:
        sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    base = args.base.rstrip("/")

    admin_pass = os.environ.get("CLIPPING_ADMIN_PASSWORD", "").strip()
    if not admin_pass:
        print("CLIPPING_ADMIN_PASSWORD env var is required", file=sys.stderr)
        return 2

    tag = str(int(time.time()))
    smoke_profile = f"smoke_{tag}"
    smoke_password = f"smoke-{smoke_profile}-2026"

    opener, _ = make_opener()
    print(f"==> Smoke against {base} (smoke profile: {smoke_profile})")

    print("\n1. Admin login")
    status, body = request(opener, "POST", f"{base}/api/login", body={"password": admin_pass})
    expect(status, 200, "admin login")

    print("\n2. CSRF token")
    status, body = request(opener, "GET", f"{base}/api/csrf")
    expect(status, 200, "csrf fetch")
    csrf = body["csrf"] if isinstance(body, dict) else ""
    assert csrf, "csrf token missing"

    print("\n3. List viewers (before)")
    status, body = request(opener, "GET", f"{base}/api/admin/viewers")
    expect(status, 200, "list viewers")
    profiles_before = {row["profile"] for row in body.get("viewers", [])} if isinstance(body, dict) else set()
    print(f"     before: {sorted(profiles_before)}")
    assert smoke_profile not in profiles_before, "smoke profile already exists — pick a different tag"

    print("\n4. Create viewer")
    status, body = request(
        opener, "POST", f"{base}/api/admin/viewers", csrf=csrf,
        body={
            "profile": smoke_profile,
            "label": f"Smoke {tag}",
            "target_keys": ["shakira"],
            "password": smoke_password,
        },
    )
    expect(status, 200, "create viewer")
    assert isinstance(body, dict) and body.get("viewer", {}).get("has_password") is True

    print("\n5. Login as smoke viewer (separate jar)")
    smoke_opener, _ = make_opener()
    status, body = request(smoke_opener, "POST", f"{base}/api/login", body={"password": smoke_password})
    expect(status, 200, "viewer login")
    assert isinstance(body, dict) and body.get("profile") == smoke_profile, body

    print("\n6. Patch viewer (rename)")
    status, body = request(
        opener, "PATCH", f"{base}/api/admin/viewers/{smoke_profile}", csrf=csrf,
        body={"label": f"Smoke {tag} renamed"},
    )
    expect(status, 200, "patch viewer")
    assert isinstance(body, dict) and "renamed" in body["viewer"]["label"], body

    print("\n7. Archive viewer")
    status, body = request(
        opener, "POST", f"{base}/api/admin/viewers/{smoke_profile}/archive", csrf=csrf,
    )
    expect(status, 200, "archive viewer")

    print("\n8. Confirm viewer login fails after archive")
    fresh_opener, _ = make_opener()
    status, body = request(fresh_opener, "POST", f"{base}/api/login", body={"password": smoke_password})
    expect(status, 401, "viewer login blocked after archive")

    print("\n9. Final viewer list — smoke profile must be gone")
    status, body = request(opener, "GET", f"{base}/api/admin/viewers")
    expect(status, 200, "list viewers (after)")
    profiles_after = {row["profile"] for row in body.get("viewers", [])} if isinstance(body, dict) else set()
    print(f"     after: {sorted(profiles_after)}")
    assert smoke_profile not in profiles_after, f"smoke profile {smoke_profile} still in list"

    print("\nSmoke OK — Goal 1 endpoints behave as specified in GOALS_ATINGIDOS.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
