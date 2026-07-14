#!/usr/bin/env python3
"""Smoke for /api/categories — happy path + input gates.

`get_or_create_category` é idempotente — chamar com mesmo nome retorna
o mesmo id. Logo, posso fazer happy path com nome "smoke_test_category"
sem acumular dados na DB.

Cobertura:
1. GET /api/categories → 200 com lista
2. POST sem CSRF → 403
3. POST sem name → 400 "name is required"
4. POST com name válido → 200 com id (idempotente)
5. POST de novo com mesmo name → 200 com MESMO id (idempotência)
6. viewer POST → 401

Reads CLIPPING_ADMIN_PASSWORD from env.
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
SMOKE_CATEGORY_NAME = "smoke_test_category"


def make_opener() -> urllib.request.OpenerDirector:
    jar = CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def request(opener, method, url, body=None, csrf=None, retries_on_5xx=2):
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


def expect(actual, expected, label):
    marker = "OK" if actual == expected else "FAIL"
    print(f"  [{marker}] {label} (HTTP {actual}, expected {expected})")
    if actual != expected:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    base = args.base.rstrip("/")

    admin_pass = os.environ.get("CLIPPING_ADMIN_PASSWORD", "").strip()
    if not admin_pass:
        print("CLIPPING_ADMIN_PASSWORD env var is required", file=sys.stderr)
        return 2

    print(f"==> Categories smoke against {base}")
    opener = make_opener()
    expect(request(opener, "POST", f"{base}/api/login", {"password": admin_pass})[0], 200, "admin login")
    s, body = request(opener, "GET", f"{base}/api/csrf")
    expect(s, 200, "csrf fetch")
    csrf = body["csrf"] if isinstance(body, dict) else ""

    print("\n1. GET /api/categories")
    s, body = request(opener, "GET", f"{base}/api/categories")
    expect(s, 200, "list categories")
    cats_before = body.get("categories", []) if isinstance(body, dict) else []
    print(f"     existing categories: {len(cats_before)}")

    print("\n2. POST sem CSRF — espera 403")
    s, body = request(opener, "POST", f"{base}/api/categories", {"name": "X"})
    expect(s, 403, "no csrf rejected")

    print("\n3. POST sem name — espera 400")
    s, body = request(opener, "POST", f"{base}/api/categories", {}, csrf=csrf)
    expect(s, 400, "missing name rejected")
    detail = str(body.get("detail", "")) if isinstance(body, dict) else ""
    assert "name is required" in detail, f"expected 'name is required' in error, got {detail!r}"

    print(f"\n4. POST com '{SMOKE_CATEGORY_NAME}' — happy path (idempotente)")
    s, body = request(opener, "POST", f"{base}/api/categories", {"name": SMOKE_CATEGORY_NAME}, csrf=csrf)
    expect(s, 200, "create category")
    first_id = body.get("id")
    print(f"     id={first_id}")

    print("\n5. POST de novo com mesmo name — espera mesmo id (idempotência)")
    s, body = request(opener, "POST", f"{base}/api/categories", {"name": SMOKE_CATEGORY_NAME}, csrf=csrf)
    expect(s, 200, "re-create category (idempotent)")
    assert body.get("id") == first_id, f"expected same id {first_id}, got {body.get('id')}"
    print(f"     id={body.get('id')} (matches first) ✅")

    print("\n6. viewer tenta POST — espera 200 (coworker pode categorizar)")
    viewer = make_opener()
    request(viewer, "POST", f"{base}/api/login", {"password": "flavio-gabinete-2026"})
    v_csrf = request(viewer, "GET", f"{base}/api/csrf")[1].get("csrf", "")
    s, body = request(viewer, "POST", f"{base}/api/categories", {"name": SMOKE_CATEGORY_NAME}, csrf=v_csrf)
    expect(s, 200, "viewer can create category")

    print("\nSmoke OK — /api/categories contract verified.")
    print(f"(left behind: idempotent '{SMOKE_CATEGORY_NAME}' — single row reused across runs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
