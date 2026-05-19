from __future__ import annotations

import io
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import authenticated_render_smoke as smoke


def quiet_call(func, *args, **kwargs):
    with redirect_stdout(io.StringIO()):
        return func(*args, **kwargs)


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
            if method == "GET" and path == "/":
                return 200, "", '<div id="app" data-clipping-session-role="admin"></div>'
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
        checks = quiet_call(smoke.check_admin, "https://example.test", "secret", allow_mutation=True)
    finally:
        smoke.SmokeClient = original_client

    assert all(check.ok for check in checks)
    assert [call[1] for call in calls] == [
        "/api/login",
        "/",
        "/api/csrf",
        "/api/targets",
        "/api/targets",
        "/api/targets/atlas_teste_smoke_20260519144000/archive",
    ]


def test_check_viewer_verifies_readonly_shell_and_control_assets():
    calls = []

    class FakeClient:
        def __init__(self, base_url):
            self.base_url = base_url

        def request(self, method, path, body=None, headers=None):
            calls.append((method, path, body or {}, headers or {}))
            if method == "POST" and path == "/api/login":
                return 200, {"role": "viewer", "profile": "flavio"}, ""
            if method == "GET" and path == "/":
                return (
                    200,
                    "",
                    '<body class="viewer-readonly"><div id="app" data-clipping-session-role="viewer" data-clipping-session-profile="flavio"></div>',
                )
            if method == "GET" and path == "/assets/clipping.css":
                return 200, "", "\n".join(smoke.VIEWER_CSS_MARKERS)
            if method == "GET" and path == "/assets/clipping.js":
                return 200, "", "\n".join(smoke.VIEWER_JS_MARKERS)
            if method == "GET" and path == "/assets/clipping-data.json":
                return 200, {"targets": [{"key": "flavio_valle"}], "stories": []}, ""
            if method == "GET" and path == "/assets/clipping-raw-texts.json":
                return 200, {"rawTexts": {"a": "Flavio-only text"}}, ""
            if method == "GET" and path == "/api/targets":
                return 200, {"targets": [{"key": "flavio_valle"}]}, ""
            if method == "GET" and path.startswith("/api/update/live-results?target_key=shakira"):
                return 200, {"items": []}, ""
            if method == "GET" and path.startswith("/api/update/live-results?target_key=rio_economico"):
                return 200, {"items": []}, ""
            if method == "GET" and path == "/api/reports/rio-economic-topic":
                return 403, {"detail": "rio_economic_profile_required"}, ""
            if method == "POST" and path == "/api/targets":
                return 401, {"detail": "admin_login_required"}, ""
            raise AssertionError(f"unexpected request: {method} {path}")

    original_client = smoke.SmokeClient
    smoke.SmokeClient = FakeClient
    try:
        checks = quiet_call(smoke.check_viewer, "https://example.test", "flavio", "secret", ["shakira", "rio_economico"])
    finally:
        smoke.SmokeClient = original_client

    assert all(check.ok for check in checks)
    assert [call[1] for call in calls[:4]] == [
        "/api/login",
        "/",
        "/assets/clipping.css",
        "/assets/clipping.js",
    ]


def test_parse_expected_profiles_defaults_to_full_viewer_set():
    assert smoke.parse_expected_profiles("") == ["flavio", "shakira", "rio_economico"]
    assert smoke.parse_expected_profiles("flavio, shakira") == ["flavio", "shakira"]


def test_expected_viewer_profiles_fail_when_smoke_is_partial():
    checks = quiet_call(
        smoke.check_expected_viewer_profiles,
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


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
