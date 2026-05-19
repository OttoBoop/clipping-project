#!/usr/bin/env python3
"""Logged-out Render smoke for the clipping segregation product.

This checks the public boundary that does not require any secrets: private
payloads must return 401, raw data files must not be served, and health must
show viewer auth/profile configuration.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_BASE_URL = "https://clipping-project.onrender.com"


@dataclass(frozen=True)
class ExpectedEndpoint:
    path: str
    status: int
    detail: str | None = None
    markers: tuple[str, ...] = ()
    method: str = "GET"
    body: dict[str, Any] | None = None


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: Any
    raw: str
    content_type: str


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


DEFAULT_ENDPOINTS = (
    ExpectedEndpoint("/healthz", 200),
    ExpectedEndpoint("/", 200, markers=("Acessar clipping", "Senha de acesso")),
    ExpectedEndpoint("/assets/clipping-data.json", 401, "viewer_login_required"),
    ExpectedEndpoint("/assets/clipping-raw-texts.json", 401, "viewer_login_required"),
    ExpectedEndpoint("/api/reports/rio-economic-topic", 401, "viewer_login_required"),
    ExpectedEndpoint("/api/update/status", 401, "viewer_login_required"),
    ExpectedEndpoint("/api/update/live-results?scope=base&limit=240", 401, "viewer_login_required"),
    ExpectedEndpoint("/api/targets", 401, "viewer_login_required"),
    ExpectedEndpoint("/api/categories", 401, "viewer_login_required"),
    ExpectedEndpoint("/api/classifications", 401, "viewer_login_required"),
    ExpectedEndpoint("/api/csrf", 401, "viewer_login_required"),
    ExpectedEndpoint("/data/targets.json", 404, "Not Found"),
    ExpectedEndpoint("/data/viewer_profiles.json", 404, "Not Found"),
    ExpectedEndpoint("/data/reports/rio_economic_topic_report_20260519T142621Z.json", 404, "Not Found"),
    ExpectedEndpoint("/clipping-data.json", 404, "Not Found"),
    ExpectedEndpoint("/api/update/start", 401, "admin_login_required", method="POST", body={"preset": "base"}),
    ExpectedEndpoint("/api/update/cancel", 401, "admin_login_required", method="POST", body={}),
    ExpectedEndpoint("/api/update/resume", 401, "admin_login_required", method="POST", body={"job_id": "logged-out-smoke"}),
    ExpectedEndpoint("/api/export", 401, "admin_login_required", method="POST", body={}),
    ExpectedEndpoint(
        "/api/targets",
        401,
        "admin_login_required",
        method="POST",
        body={"display_name": "Logged Out Smoke Should Not Create"},
    ),
    ExpectedEndpoint(
        "/api/targets/shakira",
        401,
        "admin_login_required",
        method="PATCH",
        body={"display_name": "Logged Out Smoke Should Not Edit"},
    ),
    ExpectedEndpoint(
        "/api/targets/shakira/archive",
        401,
        "admin_login_required",
        method="POST",
        body={"reason": "Logged-out smoke should not archive."},
    ),
    ExpectedEndpoint("/api/targets/shakira/restore", 401, "admin_login_required", method="POST", body={}),
    ExpectedEndpoint("/api/categories", 401, "admin_login_required", method="POST", body={"name": "Smoke Category"}),
    ExpectedEndpoint(
        "/api/classifications",
        401,
        "admin_login_required",
        method="POST",
        body={"article_id": "smoke", "target_key": "shakira", "sentiment": "neutral", "categories": []},
    ),
)


class SmokeClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> HttpResponse:
        url = urllib.parse.urljoin(self.base_url + "/", path.lstrip("/"))
        data = None
        headers = {"Accept": "application/json,text/html"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read().decode("utf-8", errors="replace")
                content_type = response.headers.get("content-type", "")
                return HttpResponse(response.status, parse_body(raw, content_type), raw, content_type)
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            content_type = exc.headers.get("content-type", "")
            return HttpResponse(exc.code, parse_body(raw, content_type), raw, content_type)

    def get(self, path: str) -> HttpResponse:
        return self.request("GET", path)


def parse_body(raw: str, content_type: str) -> Any:
    if "json" not in content_type:
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def result(name: str, ok: bool, detail: str) -> CheckResult:
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")
    return CheckResult(name=name, ok=ok, detail=detail)


def response_detail(response: HttpResponse) -> str:
    if isinstance(response.body, dict):
        value = response.body.get("detail")
        if value is not None:
            return str(value)
    return ""


def health_flags_ok(body: Any) -> tuple[bool, str]:
    if not isinstance(body, dict):
        return False, "health body is not JSON object"
    expected = {
        "loginConfigured": True,
        "viewerAuthConfigured": True,
        "viewerProfilesConfigured": True,
        "demoViewerConfigured": False,
        "missingConfig": [],
    }
    mismatches = {
        key: {"expected": expected_value, "actual": body.get(key)}
        for key, expected_value in expected.items()
        if body.get(key) != expected_value
    }
    if mismatches:
        return False, f"health mismatches={mismatches}"
    return True, (
        "loginConfigured=true viewerAuthConfigured=true "
        "viewerProfilesConfigured=true demoViewerConfigured=false missingConfig=[]"
    )


def check_endpoint(client: SmokeClient, expected: ExpectedEndpoint) -> CheckResult:
    response = client.request(expected.method, expected.path, expected.body)
    status_ok = response.status == expected.status
    detail_ok = expected.detail is None or response_detail(response) == expected.detail
    markers_missing = [marker for marker in expected.markers if marker not in response.raw]
    markers_ok = not markers_missing

    extra_ok = True
    extra_detail = ""
    if expected.method == "GET" and expected.path == "/healthz":
        extra_ok, extra_detail = health_flags_ok(response.body)

    ok = status_ok and detail_ok and markers_ok and extra_ok
    detail = f"status={response.status} expected={expected.status}"
    if expected.detail is not None:
        detail += f" detail={response_detail(response)}"
    if markers_missing:
        detail += f" missing_markers={markers_missing}"
    if extra_detail:
        detail += f" {extra_detail}"
    return result(f"{expected.method} {expected.path}", ok, detail)


def run_smoke(base_url: str, endpoints: tuple[ExpectedEndpoint, ...] = DEFAULT_ENDPOINTS) -> list[CheckResult]:
    client = SmokeClient(base_url)
    return [check_endpoint(client, endpoint) for endpoint in endpoints]


def main() -> int:
    parser = argparse.ArgumentParser(description="Logged-out Render privacy/static-boundary smoke.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    checks = run_smoke(args.base_url)
    failed = [check for check in checks if not check.ok]
    print(json.dumps({"ok": not failed, "failed": [check.name for check in failed]}, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
