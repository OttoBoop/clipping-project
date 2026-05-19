from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_fastapi_does_not_mount_data_directory_as_static_surface():
    app_source = (ROOT / "web_app" / "app.py").read_text(encoding="utf-8")

    assert 'mount("/data"' not in app_source
    assert "StaticFiles" not in app_source
    assert '@app.get("/data' not in app_source
    assert '@app.get("/assets/{asset_path:path}")' in app_source


def test_dashboard_uses_scoped_asset_routes_not_raw_data_files():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert 'data-clipping-data-url="assets/clipping-data.json"' in html
    assert 'data-clipping-raw-url="assets/clipping-raw-texts.json"' in html
    assert 'data-clipping-data-url="data/' not in html
    assert 'data-clipping-raw-url="data/' not in html


def test_asset_handler_keeps_private_payloads_on_scoped_code_path():
    app_source = (ROOT / "web_app" / "app.py").read_text(encoding="utf-8")

    assert 'if asset_path == "clipping-data.json":' in app_source
    assert 'session = require_viewer(request)' in app_source
    assert "scoped_dashboard_payload" in app_source
    assert 'if asset_path == "clipping-raw-texts.json":' in app_source
    assert "scoped_raw_texts" in app_source
