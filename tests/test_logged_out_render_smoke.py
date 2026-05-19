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

    def get(self, path):
        self.seen.append(path)
        status, body, raw, content_type = self.responses[path]
        return smoke.HttpResponse(status=status, body=body, raw=raw, content_type=content_type)


def test_default_logged_out_smoke_passes_expected_boundary():
    responses = {
        endpoint.path: (
            endpoint.status,
            {"detail": endpoint.detail} if endpoint.detail else {},
            "Acessar clipping Senha de acesso" if endpoint.path == "/" else "{}",
            "application/json",
        )
        for endpoint in smoke.DEFAULT_ENDPOINTS
    }
    responses["/healthz"] = (
        200,
        {
            "loginConfigured": True,
            "viewerAuthConfigured": True,
            "viewerProfilesConfigured": True,
            "demoViewerConfigured": False,
            "missingConfig": [],
        },
        "{}",
        "application/json",
    )
    client = FakeClient(responses)

    checks = [quiet_check(client, endpoint) for endpoint in smoke.DEFAULT_ENDPOINTS]

    assert all(check.ok for check in checks)
    assert client.seen == [endpoint.path for endpoint in smoke.DEFAULT_ENDPOINTS]


def test_private_payload_200_is_a_failure():
    client = FakeClient(
        {
            "/assets/clipping-data.json": (
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
            "/healthz": (
                200,
                {
                    "loginConfigured": True,
                    "viewerAuthConfigured": False,
                    "viewerProfilesConfigured": True,
                    "demoViewerConfigured": False,
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
    client = FakeClient({"/": (200, "<html></html>", "<html></html>", "text/html")})

    check = quiet_check(
        client,
        smoke.ExpectedEndpoint("/", 200, markers=("Acessar clipping", "Senha de acesso")),
    )

    assert check.ok is False
    assert "missing_markers" in check.detail


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
