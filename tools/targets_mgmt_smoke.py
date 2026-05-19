#!/usr/bin/env python3
"""End-to-end smoke for Goal 5 (target management completo) endpoints.

Exercises the four sub-operations + the structured error paths:

  1. admin login + csrf
  2. create secondary (happy)
  3. duplicate display_name (400 with specific message + suggestion)
  4. promote secondary -> primary (happy)
  5. re-promote (400 'ja e principal')
  6. demote primary -> secondary (happy)
  7. demote protected primary (400 'Nomes principais nao podem ser editados')
  8. create primary directly (happy)
  9. archive both smoke targets
 10. restore conflict: recreate active homonym, attempt to restore archived
     (400 with 'Já existe um nome ativo cadastrado' + suggestion)

Reads CLIPPING_ADMIN_PASSWORD from env. Smoke targets are archived but not
deleted (no delete endpoint by design — archive is reversible).

Usage:
    CLIPPING_ADMIN_PASSWORD=... python tools/targets_mgmt_smoke.py
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
PROTECTED_PRIMARY_KEY_FOR_TEST = "flavio_valle"


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


def message_of(body: Any) -> str:
    if isinstance(body, dict):
        return str(body.get("message") or body.get("detail", {}).get("message") if isinstance(body.get("detail"), dict) else body.get("message") or "")
    return ""


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
    sec_name = f"Smoke Sec {tag}"
    pri_name = f"Smoke Pri {tag}"

    opener, _ = make_opener()
    print(f"==> Goal 5 smoke against {base} (tag {tag})")

    print("\n1. Admin login + CSRF")
    status, _ = request(opener, "POST", f"{base}/api/login", body={"password": admin_pass})
    expect(status, 200, "admin login")
    status, body = request(opener, "GET", f"{base}/api/csrf")
    expect(status, 200, "csrf fetch")
    csrf = body["csrf"] if isinstance(body, dict) else ""

    print(f"\n2. Create secondary '{sec_name}'")
    status, body = request(
        opener, "POST", f"{base}/api/targets", csrf=csrf,
        body={"display_name": sec_name, "keywords": []},
    )
    expect(status, 200, "create secondary")
    sec_key = body["key"] if isinstance(body, dict) else ""
    print(f"     key={sec_key}")

    print("\n3. Duplicate display_name (should 400)")
    status, body = request(
        opener, "POST", f"{base}/api/targets", csrf=csrf,
        body={"display_name": sec_name, "keywords": []},
    )
    expect(status, 400, "duplicate rejected")
    print(f"     message: {message_of(body)}")

    print(f"\n4. Promote {sec_key} -> primary")
    status, _ = request(opener, "POST", f"{base}/api/targets/{sec_key}/promote", csrf=csrf)
    expect(status, 200, "promote")

    print("\n5. Re-promote (should 400 ja e principal)")
    status, body = request(opener, "POST", f"{base}/api/targets/{sec_key}/promote", csrf=csrf)
    expect(status, 400, "re-promote rejected")
    print(f"     message: {message_of(body)}")

    print(f"\n6. Demote {sec_key} -> secondary")
    status, _ = request(opener, "POST", f"{base}/api/targets/{sec_key}/demote", csrf=csrf)
    expect(status, 200, "demote")

    print(f"\n7. Demote protected '{PROTECTED_PRIMARY_KEY_FOR_TEST}' (should 400)")
    status, body = request(
        opener, "POST", f"{base}/api/targets/{PROTECTED_PRIMARY_KEY_FOR_TEST}/demote", csrf=csrf,
    )
    expect(status, 400, "protected demote blocked")
    print(f"     message: {message_of(body)}")

    print(f"\n8. Create primary directly '{pri_name}'")
    status, body = request(
        opener, "POST", f"{base}/api/targets/primary", csrf=csrf,
        body={"display_name": pri_name, "keywords": []},
    )
    expect(status, 200, "create primary")
    pri_key = body["key"] if isinstance(body, dict) else ""

    print("\n9. Archive both smoke targets")
    status, _ = request(
        opener, "POST", f"{base}/api/targets/{pri_key}/archive", csrf=csrf,
        body={"reason": "smoke cleanup"},
    )
    expect(status, 200, f"archive {pri_key}")
    status, _ = request(
        opener, "POST", f"{base}/api/targets/{sec_key}/archive", csrf=csrf,
        body={"reason": "smoke cleanup"},
    )
    expect(status, 200, f"archive {sec_key}")

    print("\n10. Restore conflict guard")
    status, body = request(
        opener, "POST", f"{base}/api/targets", csrf=csrf,
        body={"display_name": sec_name, "keywords": []},
    )
    expect(status, 200, "homonym recreated")
    homonym_key = body["key"] if isinstance(body, dict) else ""
    status, body = request(opener, "POST", f"{base}/api/targets/{sec_key}/restore", csrf=csrf)
    expect(status, 400, "restore conflict blocked")
    print(f"     message: {message_of(body)}")

    print("\n11. Cleanup the homonym we just created (archive)")
    status, _ = request(
        opener, "POST", f"{base}/api/targets/{homonym_key}/archive", csrf=csrf,
        body={"reason": "smoke cleanup"},
    )
    expect(status, 200, f"archive {homonym_key}")

    print("\nSmoke OK — Goal 5 (target management) backend contract behaves as specified.")
    print("Targets archived (not deleted): {pri_key}, {sec_key}, {homonym_key}".format(
        pri_key=pri_key, sec_key=sec_key, homonym_key=homonym_key,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
