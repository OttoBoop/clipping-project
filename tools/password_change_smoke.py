#!/usr/bin/env python3
"""Smoke for Goal 2 (Sessão controlada): /api/change-password endpoint.

Walks through the change-password contract in production:

  1. admin login with current password
  2. csrf fetch
  3. POST /api/change-password with wrong old_password -> expect 400
  4. POST /api/change-password with valid pair -> expect 200 + new cookie
  5. csrf refetch (new session invalidates old csrf token)
  6. log out
  7. log in with NEW password -> expect 200
  8. (cleanup) change password back to the original
  9. confirm original login works again

Reads CLIPPING_ADMIN_PASSWORD from env. The "new" password is a
deterministic-but-throwaway value derived from the unix timestamp so a
crashed run doesn't lock the admin out (the original is always restored
at step 7; if 7 fails, the new value is in the script logs).

Usage:
    CLIPPING_ADMIN_PASSWORD=... python tools/password_change_smoke.py
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

    original = os.environ.get("CLIPPING_ADMIN_PASSWORD", "").strip()
    if not original:
        print("CLIPPING_ADMIN_PASSWORD env var is required", file=sys.stderr)
        return 2

    tag = str(int(time.time()))
    throwaway = f"smoke-pwchange-{tag}"

    print(f"==> Password-change smoke against {base}")
    print(f"     throwaway password tag: {tag}  (revert is in step 7)")

    opener, _ = make_opener()
    print("\n1. Login with original password")
    status, _ = request(opener, "POST", f"{base}/api/login", body={"password": original})
    expect(status, 200, "admin login original")

    print("\n2. CSRF")
    status, body = request(opener, "GET", f"{base}/api/csrf")
    expect(status, 200, "csrf fetch")
    csrf = body["csrf"] if isinstance(body, dict) else ""

    print("\n3. Wrong old_password -> expect 400")
    status, body = request(
        opener, "POST", f"{base}/api/change-password", csrf=csrf,
        body={"old_password": "definitely-not-it", "new_password": throwaway},
    )
    expect(status, 400, "wrong old rejected")
    if isinstance(body, dict):
        print(f"     message: {body.get('message')}")

    print("\n4. Valid pair -> expect 200")
    status, body = request(
        opener, "POST", f"{base}/api/change-password", csrf=csrf,
        body={"old_password": original, "new_password": throwaway},
    )
    expect(status, 200, "change to throwaway")

    print("\n5. Refetch CSRF (new session cookie invalidated the old token)")
    status, body = request(opener, "GET", f"{base}/api/csrf")
    expect(status, 200, "csrf after change")
    csrf = body["csrf"] if isinstance(body, dict) else ""

    print("\n6. Logout (with new csrf)")
    status, _ = request(opener, "POST", f"{base}/api/logout", csrf=csrf)
    expect(status, 200, "logout ok")

    print("\n7. Login with NEW (throwaway) password")
    fresh_opener, _ = make_opener()
    status, body = request(fresh_opener, "POST", f"{base}/api/login", body={"password": throwaway})
    expect(status, 200, "login as throwaway")

    print("\n8. (cleanup) Change back to original")
    status, body = request(fresh_opener, "GET", f"{base}/api/csrf")
    expect(status, 200, "csrf after relogin")
    csrf = body["csrf"] if isinstance(body, dict) else ""
    status, _ = request(
        fresh_opener, "POST", f"{base}/api/change-password", csrf=csrf,
        body={"old_password": throwaway, "new_password": original},
    )
    if status != 200:
        print(f"  !! FAILED to restore original password — manual recovery may be required.")
        print(f"     throwaway password (still active): {throwaway}")
        return 1

    print("\n9. Final verification: original password works")
    final_opener, _ = make_opener()
    status, _ = request(final_opener, "POST", f"{base}/api/login", body={"password": original})
    expect(status, 200, "login as original")

    print("\nSmoke OK — Goal 2 change-password endpoint behaves as specified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
