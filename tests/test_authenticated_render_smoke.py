from __future__ import annotations

from datetime import datetime, timezone

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
