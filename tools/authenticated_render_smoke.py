#!/usr/bin/env python3
"""Authenticated Render smoke for the clipping segregation product.

This script intentionally reads passwords only from environment variables and
never prints them. It is meant for an operator shell, not CI logs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.cookiejar import CookieJar
from typing import Any


DEFAULT_BASE_URL = "https://clipping-project.onrender.com"


DEFAULT_FORBIDDEN_TARGETS = {
    "flavio": ["shakira", "rio_economico"],
    "shakira": ["flavio_valle", "bernardo_rubiao", "pedro_angelito", "pedro_duarte", "rio_economico"],
    "rio_economico": ["flavio_valle", "shakira", "bernardo_rubiao", "pedro_angelito", "pedro_duarte"],
    "demo_cliente": ["flavio_valle", "shakira", "rio_economico"],
}


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


class SmokeClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.cookies = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))

    def request(self, method: str, path: str, body: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> tuple[int, Any, str]:
        data = None
        request_headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        if headers:
            request_headers.update(headers)
        req = urllib.request.Request(
            urllib.parse.urljoin(self.base_url + "/", path.lstrip("/")),
            data=data,
            method=method,
            headers=request_headers,
        )
        try:
            with self.opener.open(req, timeout=30) as response:
                raw = response.read().decode("utf-8", errors="replace")
                return response.status, parse_body(raw, response.headers.get("content-type", "")), raw
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            return exc.code, parse_body(raw, exc.headers.get("content-type", "")), raw


def parse_body(raw: str, content_type: str) -> Any:
    if "json" not in content_type:
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def parse_profile_passwords(raw: str) -> dict[str, str]:
    raw = raw.strip()
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
            password_value = value.get("password") if isinstance(value, dict) else value
            password = str(password_value or "").strip()
            if key and password:
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


def parse_forbidden_targets(raw: str) -> dict[str, list[str]]:
    if not raw.strip():
        return DEFAULT_FORBIDDEN_TARGETS
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("CLIPPING_SMOKE_FORBIDDEN_TARGETS must be a JSON object")
    return {
        str(profile): [str(item) for item in values]
        for profile, values in parsed.items()
        if isinstance(values, list)
    }


def text_contains_any(value: Any, needles: list[str]) -> list[str]:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True) if not isinstance(value, str) else value
    return [needle for needle in needles if needle and needle in text]


def target_keys_from_targets_payload(payload: Any) -> set[str]:
    if not isinstance(payload, dict):
        return set()
    rows = payload.get("targets")
    if isinstance(rows, dict):
        rows = rows.get("targets")
    if not isinstance(rows, list):
        return set()
    return {str(row.get("key")) for row in rows if isinstance(row, dict) and row.get("key")}


def payload_target_keys(payload: Any) -> set[str]:
    found: set[str] = set()
    if not isinstance(payload, dict):
        return found
    for target in payload.get("targets") or []:
        if isinstance(target, dict) and target.get("key"):
            found.add(str(target["key"]))
    for story in payload.get("stories") or []:
        if not isinstance(story, dict):
            continue
        found.update(str(key) for key in story.get("targetKeys") or [] if key)
        for article in story.get("articles") or []:
            if isinstance(article, dict):
                found.update(str(key) for key in article.get("targetKeys") or [] if key)
    return found


def result(name: str, ok: bool, detail: str) -> CheckResult:
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")
    return CheckResult(name, ok, detail)


def check_viewer(base_url: str, profile: str, password: str, forbidden_targets: list[str]) -> list[CheckResult]:
    client = SmokeClient(base_url)
    checks: list[CheckResult] = []
    status, body, _raw = client.request("POST", "/api/login", {"password": password})
    actual_profile = body.get("profile") if isinstance(body, dict) else ""
    checks.append(result(f"{profile} login", status == 200 and actual_profile == profile, f"status={status} profile={actual_profile}"))

    status, data_payload, _raw = client.request("GET", "/assets/clipping-data.json")
    payload_keys = payload_target_keys(data_payload)
    leaked = sorted(payload_keys.intersection(forbidden_targets))
    checks.append(result(f"{profile} scoped data", status == 200 and not leaked, f"status={status} forbidden_seen={leaked} target_count={len(payload_keys)}"))

    status, raw_payload, _raw = client.request("GET", "/assets/clipping-raw-texts.json")
    raw_leaked = text_contains_any(raw_payload, forbidden_targets)
    checks.append(result(f"{profile} raw text scope", status == 200 and not raw_leaked, f"status={status} forbidden_seen={raw_leaked}"))

    status, targets_payload, _raw = client.request("GET", "/api/targets")
    target_keys = target_keys_from_targets_payload(targets_payload)
    target_leaked = sorted(target_keys.intersection(forbidden_targets))
    checks.append(result(f"{profile} targets scope", status == 200 and not target_leaked, f"status={status} forbidden_seen={target_leaked} target_count={len(target_keys)}"))

    for forbidden in forbidden_targets[:2]:
        status, live_payload, _raw = client.request("GET", f"/api/update/live-results?target_key={urllib.parse.quote(forbidden)}&limit=30")
        live_leaked = text_contains_any(live_payload, [forbidden])
        checks.append(result(f"{profile} forbidden live-results {forbidden}", status == 200 and not live_leaked, f"status={status} forbidden_seen={live_leaked}"))

    status, rio_payload, _raw = client.request("GET", "/api/reports/rio-economic-topic")
    expected_rio_status = 200 if profile == "rio_economico" else 403
    checks.append(result(f"{profile} Rio endpoint boundary", status == expected_rio_status, f"status={status} expected={expected_rio_status}"))

    status, write_payload, _raw = client.request("POST", "/api/targets", {"display_name": "Smoke Should Not Create"})
    detail = write_payload.get("detail") if isinstance(write_payload, dict) else write_payload
    checks.append(result(f"{profile} target write rejected", status in {401, 403}, f"status={status} detail={detail}"))
    return checks


def check_admin(base_url: str, password: str, allow_mutation: bool) -> list[CheckResult]:
    client = SmokeClient(base_url)
    checks: list[CheckResult] = []
    status, body, _raw = client.request("POST", "/api/login", {"password": password})
    role = body.get("role") if isinstance(body, dict) else ""
    checks.append(result("admin login", status == 200 and role == "admin", f"status={status} role={role}"))

    status, csrf_payload, _raw = client.request("GET", "/api/csrf")
    token = csrf_payload.get("csrf") if isinstance(csrf_payload, dict) else ""
    checks.append(result("admin csrf token", status == 200 and bool(token), f"status={status} token_present={bool(token)}"))

    status, no_csrf_payload, _raw = client.request("POST", "/api/targets", {"display_name": "Smoke Should Not Create"})
    detail = no_csrf_payload.get("detail") if isinstance(no_csrf_payload, dict) else no_csrf_payload
    checks.append(result("admin mutation without csrf rejected", status == 403, f"status={status} detail={detail}"))

    if allow_mutation:
        checks.append(result("admin mutation with csrf", False, "not implemented deliberately; create an approved disposable-target cleanup plan first"))
    else:
        checks.append(result("admin mutation with csrf", True, "skipped by default to avoid production target writes"))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Authenticated smoke for Render profile segregation.")
    parser.add_argument("--base-url", default=os.environ.get("CLIPPING_SMOKE_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--allow-admin-mutation", action="store_true", default=os.environ.get("CLIPPING_SMOKE_ALLOW_ADMIN_MUTATION") == "1")
    args = parser.parse_args()

    viewer_passwords = parse_profile_passwords(os.environ.get("CLIPPING_SMOKE_VIEWER_PASSWORDS", ""))
    admin_password = os.environ.get("CLIPPING_SMOKE_ADMIN_PASSWORD", "").strip()
    forbidden_targets = parse_forbidden_targets(os.environ.get("CLIPPING_SMOKE_FORBIDDEN_TARGETS", ""))

    all_checks: list[CheckResult] = []
    if not viewer_passwords:
        all_checks.append(result("viewer passwords configured for smoke", False, "set CLIPPING_SMOKE_VIEWER_PASSWORDS outside Git"))
    for profile, password in sorted(viewer_passwords.items()):
        all_checks.extend(check_viewer(args.base_url, profile, password, forbidden_targets.get(profile, [])))

    if admin_password:
        all_checks.extend(check_admin(args.base_url, admin_password, args.allow_admin_mutation))
    else:
        all_checks.append(result("admin password configured for smoke", False, "set CLIPPING_SMOKE_ADMIN_PASSWORD outside Git"))

    failed = [check for check in all_checks if not check.ok]
    print(json.dumps({"ok": not failed, "failed": [check.name for check in failed]}, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
