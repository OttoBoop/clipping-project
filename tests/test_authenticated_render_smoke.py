from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from tools import authenticated_render_smoke as smoke


def test_disposable_target_name_uses_auto_archive_marker():
    name = smoke.disposable_target_name(datetime(2026, 5, 19, 14, 40, 0, tzinfo=timezone.utc))

    assert name == "Atlas Teste Smoke 20260519144000"


def test_check_admin_can_run_disposable_mutation_with_cleanup():
    calls = []

    class FakeClient:
        def __init__(self, base_url):
            self.base_url = base_url

        def request(self, method, path, body=None, headers=None):
            calls.append((method, path, body or {}, headers or {}))
            if method == "POST" and path == "/api/login":
                return 200, {"role": "admin"}, ""
            if method == "GET" and path == "/api/csrf":
                return 200, {"csrf": "csrf-token"}, ""
            if method == "POST" and path == "/api/targets" and not headers:
                return 403, {"detail": "csrf_check_failed"}, ""
            if method == "POST" and path == "/api/targets":
                assert headers == {"X-CSRF-Token": "csrf-token"}
                assert body["display_name"].startswith("Atlas Teste Smoke ")
                return 200, {"key": "atlas_teste_smoke_20260519144000", "archived": True}, ""
            if method == "POST" and path == "/api/targets/atlas_teste_smoke_20260519144000/archive":
                assert headers == {"X-CSRF-Token": "csrf-token"}
                return 200, {"key": "atlas_teste_smoke_20260519144000", "archived": True}, ""
            raise AssertionError(f"unexpected request: {method} {path}")

    original_client = smoke.SmokeClient
    smoke.SmokeClient = FakeClient
    try:
        checks = smoke.check_admin("https://example.test", "secret", allow_mutation=True)
    finally:
        smoke.SmokeClient = original_client

    assert all(check.ok for check in checks)
    assert [call[1] for call in calls] == [
        "/api/login",
        "/api/csrf",
        "/api/targets",
        "/api/targets",
        "/api/targets/atlas_teste_smoke_20260519144000/archive",
    ]


def test_parse_expected_profiles_defaults_to_full_viewer_set():
    assert smoke.parse_expected_profiles("") == ["flavio", "shakira", "rio_economico"]
    assert smoke.parse_expected_profiles("flavio, shakira") == ["flavio", "shakira"]


def test_expected_viewer_profiles_fail_when_smoke_is_partial():
    checks = smoke.check_expected_viewer_profiles(
        {"flavio": "secret"},
        ["flavio", "shakira", "rio_economico"],
    )

    assert len(checks) == 1
    assert checks[0].ok is False
    assert "missing=['shakira', 'rio_economico']" in checks[0].detail


def test_credentials_file_reads_only_smoke_keys():
    with tempfile.TemporaryDirectory() as tmp:
        credentials = Path(tmp) / "smoke.env"
        credentials.write_text(
            "\n".join(
                [
                    "# local smoke credentials",
                    "CLIPPING_SMOKE_VIEWER_PASSWORDS='flavio=one;shakira=two'",
                    'export CLIPPING_SMOKE_ADMIN_PASSWORD="admin-secret"',
                    "UNRELATED_SECRET=should-not-load",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        values = smoke.read_credentials_file(credentials)

    assert values == {
        "CLIPPING_SMOKE_ADMIN_PASSWORD": "admin-secret",
        "CLIPPING_SMOKE_VIEWER_PASSWORDS": "flavio=one;shakira=two",
    }
