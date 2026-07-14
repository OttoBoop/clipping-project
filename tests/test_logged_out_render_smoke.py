from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import logged_out_render_smoke as smoke


def quiet_check(client, endpoint):
    with redirect_stdout(io.StringIO()):
        return smoke.check_endpoint(client, endpoint)


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.seen = []

    def request(self, method, path, body=None):
        self.seen.append((method, path, body))
        status, body, raw, content_type = self.responses[(method, path)]
        return smoke.HttpResponse(status=status, body=body, raw=raw, content_type=content_type)


class SequenceClient:
    def __init__(self, responses):
        self.responses = responses
        self.seen = []

    def request(self, method, path, body=None):
        self.seen.append((method, path, body))
        rows = self.responses[(method, path)]
        if len(rows) > 1:
            status, body, raw, content_type = rows.pop(0)
        else:
            status, body, raw, content_type = rows[0]
        return smoke.HttpResponse(status=status, body=body, raw=raw, content_type=content_type)

    def get(self, path):
        return self.request("GET", path)


def test_default_logged_out_smoke_passes_expected_boundary():
    responses = {
        (endpoint.method, endpoint.path): (
            endpoint.status,
            {"detail": endpoint.detail} if endpoint.detail else {},
            'Acessar clipping id="loginButton"' if endpoint.path == "/" else "{}",
            "application/json",
        )
        for endpoint in smoke.DEFAULT_ENDPOINTS
    }
    responses[("GET", "/healthz")] = (
        200,
        {
            "loginConfigured": True,
            "viewerAuthConfigured": True,
            "viewerProfilesConfigured": True,
            "demoViewerConfigured": True,
            "missingConfig": [],
        },
        "{}",
        "application/json",
    )
    client = FakeClient(responses)

    checks = [quiet_check(client, endpoint) for endpoint in smoke.DEFAULT_ENDPOINTS]

    assert all(check.ok for check in checks)
    assert client.seen == [(endpoint.method, endpoint.path, endpoint.body) for endpoint in smoke.DEFAULT_ENDPOINTS]


def test_private_payload_200_is_a_failure():
    client = FakeClient(
        {
            ("GET", "/assets/clipping-data.json"): (
                200,
                {"stories": [{"targetKeys": ["flavio_valle"]}]},
                '{"stories":[]}',
                "application/json",
            )
        }
    )

    check = quiet_check(
        client,
        smoke.ExpectedEndpoint("/assets/clipping-data.json", 401, "viewer_login_required"),
    )

    assert check.ok is False
    assert "status=200 expected=401" in check.detail


def test_health_requires_viewer_configuration():
    client = FakeClient(
        {
            ("GET", "/healthz"): (
                200,
                {
                    "loginConfigured": True,
                    "viewerAuthConfigured": False,
                    "viewerProfilesConfigured": True,
                    "demoViewerConfigured": True,
                    "missingConfig": ["CLIPPING_VIEWER_PASSWORDS"],
                },
                "{}",
                "application/json",
            )
        }
    )

    check = quiet_check(client, smoke.ExpectedEndpoint("/healthz", 200))

    assert check.ok is False
    assert "viewerAuthConfigured" in check.detail


def test_login_page_requires_expected_markers():
    client = FakeClient({("GET", "/"): (200, "<html></html>", "<html></html>", "text/html")})

    check = quiet_check(
        client,
        smoke.ExpectedEndpoint("/", 200, markers=("Acessar clipping", 'id="loginButton"')),
    )

    assert check.ok is False
    assert "missing_markers" in check.detail


def test_logged_out_target_mutation_rejection_is_checked():
    target_mutations = [
        endpoint
        for endpoint in smoke.DEFAULT_ENDPOINTS
        if endpoint.path.startswith("/api/targets") and endpoint.method in {"POST", "PATCH"}
    ]

    assert {endpoint.path for endpoint in target_mutations} == {
        "/api/targets",
        "/api/targets/shakira",
        "/api/targets/shakira/archive",
        "/api/targets/shakira/restore",
    }
    assert all(endpoint.detail == "viewer_login_required" for endpoint in target_mutations)


def test_logged_out_operator_mutation_rejection_is_checked():
    operator_mutations = [
        endpoint
        for endpoint in smoke.DEFAULT_ENDPOINTS
        if endpoint.method == "POST" and endpoint.path in {
            "/api/update/start",
            "/api/update/cancel",
            "/api/update/resume",
            "/api/export",
            "/api/categories",
            "/api/classifications",
        }
    ]

    assert {endpoint.path: endpoint.detail for endpoint in operator_mutations} == {
        "/api/update/start": "admin_login_required",
        "/api/update/cancel": "admin_login_required",
        "/api/update/resume": "admin_login_required",
        "/api/export": "admin_login_required",
        "/api/categories": "viewer_login_required",
        "/api/classifications": "viewer_login_required",
    }


def test_logged_out_rio_corpus_boundary_is_checked():
    rio_checks = [endpoint for endpoint in smoke.DEFAULT_ENDPOINTS if endpoint.path.startswith("/api/rio/")]

    assert {endpoint.path: (endpoint.method, endpoint.detail) for endpoint in rio_checks} == {
        "/api/rio/status": ("GET", "viewer_login_required"),
        "/api/rio/sources": ("GET", "viewer_login_required"),
        "/api/rio/corpus": ("GET", "viewer_login_required"),
        "/api/rio/coverage": ("GET", "viewer_login_required"),
        "/api/rio/audit": ("GET", "viewer_login_required"),
        "/api/rio/schedule": ("POST", "rio_corpus_scheduler_auth_required"),
    }


def test_invalid_login_rejection_forbids_profile_leaks():
    login_checks = [endpoint for endpoint in smoke.DEFAULT_ENDPOINTS if endpoint.path == "/api/login"]

    assert len(login_checks) == 1
    login_check = login_checks[0]
    assert login_check.method == "POST"
    assert login_check.detail == "invalid_password"
    assert "flavio" in login_check.absent_markers
    assert "shakira" in login_check.absent_markers


def test_absent_marker_seen_is_a_failure():
    client = FakeClient(
        {
            ("POST", "/api/login"): (
                401,
                {"detail": "invalid_password", "profile": "flavio"},
                '{"detail":"invalid_password","profile":"flavio"}',
                "application/json",
            )
        }
    )

    check = quiet_check(
        client,
        smoke.ExpectedEndpoint(
            "/api/login",
            401,
            "invalid_password",
            absent_markers=("flavio",),
            method="POST",
            body={"password": "wrong"},
        ),
    )

    assert check.ok is False
    assert "forbidden_markers" in check.detail


def test_preflight_retries_transient_health_before_smoke(monkeypatch=None):
    endpoint = smoke.ExpectedEndpoint("/healthz", 200)
    client = SequenceClient(
        {
            ("GET", "/healthz"): [
                (503, "Service Unavailable", "Service Unavailable", "text/plain"),
                (
                    200,
                    {
                        "loginConfigured": True,
                        "viewerAuthConfigured": True,
                        "viewerProfilesConfigured": True,
                        "demoViewerConfigured": True,
                        "missingConfig": [],
                    },
                    "{}",
                    "application/json",
                ),
            ]
        }
    )

    original_client = smoke.SmokeClient
    smoke.SmokeClient = lambda _base_url: client
    try:
        with redirect_stdout(io.StringIO()):
            checks = smoke.run_smoke(
                "https://example.test",
                endpoints=(endpoint,),
                preflight_retries=1,
                retry_delay_seconds=0,
            )
    finally:
        smoke.SmokeClient = original_client

    assert all(check.ok for check in checks)
    assert client.seen == [
        ("GET", "/healthz", None),
        ("GET", "/healthz", None),
        ("GET", "/healthz", None),
    ]


def test_preflight_fails_fast_when_health_stays_transient():
    client = SequenceClient(
        {
            ("GET", "/healthz"): [
                (503, "Service Unavailable", "Service Unavailable", "text/plain"),
            ]
        }
    )

    original_client = smoke.SmokeClient
    smoke.SmokeClient = lambda _base_url: client
    try:
        with redirect_stdout(io.StringIO()):
            checks = smoke.run_smoke(
                "https://example.test",
                endpoints=(smoke.ExpectedEndpoint("/assets/clipping-data.json", 401),),
                preflight_retries=1,
                retry_delay_seconds=0,
            )
    finally:
        smoke.SmokeClient = original_client

    assert len(checks) == 1
    assert checks[0].ok is False
    assert checks[0].name == "preflight /healthz"
    assert client.seen == [("GET", "/healthz", None), ("GET", "/healthz", None)]


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
