#!/usr/bin/env python3
"""Smoke for /api/classifications — input-gate coverage only.

The happy path mutates production data (creates mention + classification
+ categories + Supabase upload). This smoke covers the validation gates
that fail BEFORE any DB write:

1. POST sem CSRF → 403
2. POST sem article_id → 400 "article_id and target_key are required"
3. POST com article_id inválido (string não-numérica) → 400 "article_id must be an integer"
4. POST com article_sentiment inválido → 400 "must be one of"
5. POST com centimetragem não-numérica → 400 "centimetragem must be numeric"
6. POST com categories não-lista → 400 "categories must be a list"
7. GET /api/classifications → 200 (read-only OK)
8. viewer POST → 401

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


DEFAULT_BASE_URL = "https://clipping-project.onrender.com"


def make_opener():
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


def detail(body):
    if isinstance(body, dict):
        return str(body.get("detail") or body.get("message") or "")
    return str(body)[:120]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    base = args.base.rstrip("/")

    admin_pass = os.environ.get("CLIPPING_ADMIN_PASSWORD", "").strip()
    if not admin_pass:
        print("CLIPPING_ADMIN_PASSWORD env var is required", file=sys.stderr)
        return 2

    print(f"==> Classifications input-gate smoke against {base}")
    opener = make_opener()
    expect(request(opener, "POST", f"{base}/api/login", {"password": admin_pass})[0], 200, "admin login")
    csrf = request(opener, "GET", f"{base}/api/csrf")[1].get("csrf", "")

    print("\n1. POST sem CSRF — espera 403")
    s, body = request(opener, "POST", f"{base}/api/classifications", {"article_id": 1, "target_key": "shakira"})
    expect(s, 403, "no csrf rejected")

    print("\n2. POST sem article_id — espera 400")
    s, body = request(opener, "POST", f"{base}/api/classifications", {"target_key": "shakira"}, csrf=csrf)
    expect(s, 400, "missing article_id rejected")
    msg = detail(body)
    assert "article_id" in msg, f"expected article_id in error, got {msg!r}"

    print("\n3. POST com article_id não-numérico — espera 400")
    s, body = request(opener, "POST", f"{base}/api/classifications", {"article_id": "abc", "target_key": "shakira"}, csrf=csrf)
    expect(s, 400, "non-numeric article_id rejected")
    msg = detail(body)
    assert "integer" in msg, f"expected 'integer' in error, got {msg!r}"

    print("\n4. POST com article_sentiment inválido — espera 400")
    s, body = request(opener, "POST", f"{base}/api/classifications",
                       {"article_id": 99999999, "target_key": "shakira", "article_sentiment": "wrong"}, csrf=csrf)
    expect(s, 400, "invalid sentiment rejected")
    msg = detail(body)
    assert "one of" in msg, f"expected 'one of' in error, got {msg!r}"

    print("\n5. POST com centimetragem não-numérica — espera 400")
    s, body = request(opener, "POST", f"{base}/api/classifications",
                       {"article_id": 99999999, "target_key": "shakira", "centimetragem": "five"}, csrf=csrf)
    expect(s, 400, "non-numeric centimetragem rejected")
    msg = detail(body)
    assert "numeric" in msg, f"expected 'numeric' in error, got {msg!r}"

    print("\n6. POST com categories não-lista — espera 400")
    s, body = request(opener, "POST", f"{base}/api/classifications",
                       {"article_id": 99999999, "target_key": "shakira", "categories": "not-a-list"}, csrf=csrf)
    expect(s, 400, "non-list categories rejected")
    msg = detail(body)
    assert "list" in msg, f"expected 'list' in error, got {msg!r}"

    print("\n7. GET /api/classifications — espera 200")
    s, body = request(opener, "GET", f"{base}/api/classifications")
    expect(s, 200, "list classifications")
    print(f"     count: {len(body.get('classifications', [])) if isinstance(body, dict) else 'n/a'}")

    print("\n8. viewer POST — espera 401")
    viewer = make_opener()
    request(viewer, "POST", f"{base}/api/login", {"password": "flavio-gabinete-2026"})
    v_csrf = request(viewer, "GET", f"{base}/api/csrf")[1].get("csrf", "")
    s, body = request(viewer, "POST", f"{base}/api/classifications",
                       {"article_id": 1, "target_key": "shakira"}, csrf=v_csrf)
    expect(s, 401, "viewer cannot upsert classification")

    print("\nSmoke OK — /api/classifications input gates verified.")
    print("(no classification was actually upserted; this smoke is non-destructive)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
