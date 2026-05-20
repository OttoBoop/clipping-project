#!/usr/bin/env python3
"""Read-only smoke covering admin GET endpoints that didn't have a
sentinel yet. Designed to catch regression in the day-to-day operator
workflows: check status, list archived targets, read the Rio report,
fetch classifications. No mutations.

Reads CLIPPING_ADMIN_PASSWORD from env.

Usage:
    CLIPPING_ADMIN_PASSWORD=... python tools/admin_readonly_smoke.py
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


def request(opener: urllib.request.OpenerDirector, method: str, url: str, body: dict[str, Any] | None = None, retries_on_5xx: int = 2) -> tuple[int, Any]:
    """HTTP request with bounded retry on 5xx (Render gateway/coldstart)."""
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
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


def expect_status(label: str, actual: int, expected: int) -> bool:
    ok = actual == expected
    marker = "OK" if ok else "FAIL"
    print(f"  [{marker}] {label} (HTTP {actual}, expected {expected})")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    base = args.base.rstrip("/")

    admin_pass = os.environ.get("CLIPPING_ADMIN_PASSWORD", "").strip()
    if not admin_pass:
        print("CLIPPING_ADMIN_PASSWORD env var is required", file=sys.stderr)
        return 2

    opener = make_opener()
    failures: list[str] = []

    print(f"==> Admin read-only smoke against {base}")

    # Login
    status, body = request(opener, "POST", f"{base}/api/login", body={"password": admin_pass})
    if not expect_status("admin login", status, 200):
        return 1

    # Read-only endpoints to validate
    checks = [
        ("GET /api/csrf", "GET", "/api/csrf", 200, lambda b: bool(b.get("csrf"))),
        ("GET /api/healthz (no auth)", "GET", "/healthz", 200, lambda b: b.get("ok") is True),
        ("GET /api/targets (active only)", "GET", "/api/targets", 200, lambda b: isinstance(b.get("targets"), list) and len(b["targets"]) >= 4),
        ("GET /api/targets?include_archived=1", "GET", "/api/targets?include_archived=1", 200, lambda b: isinstance(b.get("targets"), list) and any(t.get("archived") for t in b["targets"])),
        ("GET /api/update/status", "GET", "/api/update/status", 200, lambda b: isinstance(b.get("current"), dict) and isinstance(b.get("recent"), list)),
        ("GET /api/update/live-results", "GET", "/api/update/live-results?limit=5", 200, lambda b: isinstance(b.get("items"), list)),
        ("GET /api/admin/viewers", "GET", "/api/admin/viewers", 200, lambda b: isinstance(b.get("viewers"), list) and len(b["viewers"]) >= 4),
        ("GET /api/categories", "GET", "/api/categories", 200, lambda b: isinstance(b.get("categories"), list)),
        ("GET /api/classifications", "GET", "/api/classifications", 200, lambda b: isinstance(b.get("classifications"), list)),
        ("GET /api/reports/rio-economic-topic (admin)", "GET", "/api/reports/rio-economic-topic", 200, lambda b: isinstance(b, dict)),
    ]
    for label, method, path, expected_status, body_check in checks:
        status, body = request(opener, method, f"{base}{path}")
        ok = expect_status(label, status, expected_status)
        if ok and not body_check(body):
            print(f"        body shape failed: {str(body)[:140]}")
            ok = False
            failures.append(label + " body shape")
        if status != expected_status:
            failures.append(label)

    print()
    if failures:
        print(f"FAIL — {len(failures)} checks failed: {failures}")
        return 1
    print("Smoke OK — admin read-only endpoints behave as expected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
