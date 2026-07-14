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
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://clipping-project.onrender.com"
DEFAULT_EXPECTED_VIEWER_PROFILES = ("flavio", "shakira", "rio_economico")


DEFAULT_FORBIDDEN_TARGETS = {
    "flavio": ["shakira", "rio_economico"],
    "shakira": ["flavio_valle", "bernardo_rubiao", "pedro_angelito", "pedro_duarte", "rio_economico"],
    "rio_economico": ["flavio_valle", "shakira", "bernardo_rubiao", "pedro_angelito", "pedro_duarte"],
    "demo_cliente": ["flavio_valle", "shakira", "rio_economico"],
}


VIEWER_SHELL_MARKERS = (
    'data-clipping-session-role="viewer"',
    '<body class="viewer-readonly">',
)

VIEWER_CSS_MARKERS = (
    "body.viewer-readonly .add-target-box",
    "body.viewer-readonly .manage-targets-box",
    "display: none !important",
)

VIEWER_JS_MARKERS = (
    "function applyViewerControls",
    "classificationVisible",
    "classificationWritable",
    "document.body.classList.toggle(\"viewer-readonly\", !canMutate)",
    "addTargetForm.closest(\"details\").hidden = true",
    "manageTargetsBox.hidden = true",
    "viewerCanSeeRioReport()",
)


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


def missing_markers(text: str, markers: list[str] | tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def parse_expected_profiles(raw: str) -> list[str]:
    profiles = [profile.strip() for profile in raw.split(",") if profile.strip()]
    return profiles or list(DEFAULT_EXPECTED_VIEWER_PROFILES)


def parse_secret_file_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("export "):
        stripped = stripped.removeprefix("export ").strip()
    if "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip().strip('"').strip("'")
    if not key:
        return None
    return key, value


def read_credentials_file(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_secret_file_line(line)
        if parsed:
            key, value = parsed
            if key.startswith("CLIPPING_SMOKE_"):
                values[key] = value
    return values


def smoke_env(credentials_file: Path | None = None) -> dict[str, str]:
    values = read_credentials_file(credentials_file)
    values.update({key: value for key, value in os.environ.items() if key.startswith("CLIPPING_SMOKE_")})
    return values


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


def disposable_target_name(now: datetime | None = None) -> str:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d%H%M%S")
    return f"Atlas Teste Smoke {stamp}"


def check_viewer(base_url: str, profile: str, password: str, forbidden_targets: list[str]) -> list[CheckResult]:
    client = SmokeClient(base_url)
    checks: list[CheckResult] = []
    status, body, _raw = client.request("POST", "/api/login", {"password": password})
    actual_profile = body.get("profile") if isinstance(body, dict) else ""
    checks.append(result(f"{profile} login", status == 200 and actual_profile == profile, f"status={status} profile={actual_profile}"))

    status, _body, raw_html = client.request("GET", "/")
    shell_markers = (*VIEWER_SHELL_MARKERS, f'data-clipping-session-profile="{profile}"')
    shell_missing = missing_markers(raw_html, shell_markers)
    admin_marker_seen = 'data-clipping-session-role="admin"' in raw_html
    checks.append(
        result(
            f"{profile} viewer readonly shell",
            status == 200 and not shell_missing and not admin_marker_seen,
            f"status={status} missing={shell_missing} admin_marker_seen={admin_marker_seen}",
        )
    )

    status, _body, raw_css = client.request("GET", "/assets/clipping.css")
    css_missing = missing_markers(raw_css, VIEWER_CSS_MARKERS)
    checks.append(result(f"{profile} viewer readonly css", status == 200 and not css_missing, f"status={status} missing={css_missing}"))

    status, _body, raw_js = client.request("GET", "/assets/clipping.js")
    js_missing = missing_markers(raw_js, VIEWER_JS_MARKERS)
    checks.append(result(f"{profile} viewer control js", status == 200 and not js_missing, f"status={status} missing={js_missing}"))

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


def check_expected_viewer_profiles(
    viewer_passwords: dict[str, str],
    expected_profiles: list[str],
) -> list[CheckResult]:
    if not viewer_passwords:
        return [result("viewer passwords configured for smoke", False, "set CLIPPING_SMOKE_VIEWER_PASSWORDS outside Git")]
    missing = [profile for profile in expected_profiles if profile not in viewer_passwords]
    if missing:
        return [
            result(
                "expected viewer profiles configured",
                False,
                f"missing={missing} configured={sorted(viewer_passwords)}",
            )
        ]
    return [
        result(
            "expected viewer profiles configured",
            True,
            f"configured={sorted(viewer_passwords)} expected={expected_profiles}",
        )
    ]


def check_admin(base_url: str, password: str, allow_mutation: bool) -> list[CheckResult]:
    client = SmokeClient(base_url)
    checks: list[CheckResult] = []
    status, body, _raw = client.request("POST", "/api/login", {"password": password})
    role = body.get("role") if isinstance(body, dict) else ""
    checks.append(result("admin login", status == 200 and role == "admin", f"status={status} role={role}"))

    status, _body, raw_html = client.request("GET", "/")
    admin_marker_seen = 'data-clipping-session-role="admin"' in raw_html
    viewer_readonly_seen = "viewer-readonly" in raw_html
    checks.append(
        result(
            "admin shell",
            status == 200 and admin_marker_seen and not viewer_readonly_seen,
            f"status={status} admin_marker_seen={admin_marker_seen} viewer_readonly_seen={viewer_readonly_seen}",
        )
    )

    status, csrf_payload, _raw = client.request("GET", "/api/csrf")
    token = csrf_payload.get("csrf") if isinstance(csrf_payload, dict) else ""
    checks.append(result("admin csrf token", status == 200 and bool(token), f"status={status} token_present={bool(token)}"))

    status, no_csrf_payload, _raw = client.request("POST", "/api/targets", {"display_name": "Smoke Should Not Create"})
    detail = no_csrf_payload.get("detail") if isinstance(no_csrf_payload, dict) else no_csrf_payload
    checks.append(result("admin mutation without csrf rejected", status == 403, f"status={status} detail={detail}"))

    if allow_mutation:
        if not token:
            checks.append(result("admin mutation with csrf", False, "skipped because csrf token was not available"))
            return checks
        display_name = disposable_target_name()
        status, create_payload, _raw = client.request(
            "POST",
            "/api/targets",
            {"display_name": display_name, "keywords": [display_name]},
            headers={"X-CSRF-Token": token},
        )
        target_key = create_payload.get("key") if isinstance(create_payload, dict) else ""
        archived = bool(create_payload.get("archived")) if isinstance(create_payload, dict) else False
        create_ok = status == 200 and str(target_key).startswith("atlas_teste_smoke")
        checks.append(
            result(
                "admin mutation with csrf creates disposable target",
                create_ok,
                f"status={status} key={target_key} archived={archived}",
            )
        )
        if create_ok:
            status, archive_payload, _raw = client.request(
                "POST",
                f"/api/targets/{urllib.parse.quote(str(target_key))}/archive",
                {"reason": "Authenticated Render smoke cleanup."},
                headers={"X-CSRF-Token": token},
            )
            archived = bool(archive_payload.get("archived")) if isinstance(archive_payload, dict) else False
            checks.append(
                result(
                    "admin mutation cleanup archive",
                    status == 200 and archived,
                    f"status={status} key={target_key} archived={archived}",
                )
            )
    else:
        checks.append(result("admin mutation with csrf", True, "skipped by default to avoid production target writes"))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Authenticated smoke for Render profile segregation.")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--credentials-file", type=Path, default=None)
    parser.add_argument("--expected-viewer-profiles", default=None)
    parser.add_argument("--allow-admin-mutation", action="store_true", default=False)
    args = parser.parse_args()

    env = smoke_env(args.credentials_file)
    base_url = args.base_url or env.get("CLIPPING_SMOKE_BASE_URL") or DEFAULT_BASE_URL
    expected_profiles = parse_expected_profiles(
        args.expected_viewer_profiles
        or env.get("CLIPPING_SMOKE_EXPECTED_VIEWER_PROFILES", "")
        or ",".join(DEFAULT_EXPECTED_VIEWER_PROFILES)
    )
    allow_mutation = args.allow_admin_mutation or env.get("CLIPPING_SMOKE_ALLOW_ADMIN_MUTATION") == "1"
    viewer_passwords = parse_profile_passwords(env.get("CLIPPING_SMOKE_VIEWER_PASSWORDS", ""))
    admin_password = env.get("CLIPPING_SMOKE_ADMIN_PASSWORD", "").strip()
    forbidden_targets = parse_forbidden_targets(env.get("CLIPPING_SMOKE_FORBIDDEN_TARGETS", ""))

    all_checks: list[CheckResult] = []
    all_checks.extend(check_expected_viewer_profiles(viewer_passwords, expected_profiles))
    for profile, password in sorted(viewer_passwords.items()):
        all_checks.extend(check_viewer(base_url, profile, password, forbidden_targets.get(profile, [])))

    if admin_password:
        all_checks.extend(check_admin(base_url, admin_password, allow_mutation))
    else:
        all_checks.append(result("admin password configured for smoke", False, "set CLIPPING_SMOKE_ADMIN_PASSWORD outside Git"))

    failed = [check for check in all_checks if not check.ok]
    print(json.dumps({"ok": not failed, "failed": [check.name for check in failed]}, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
