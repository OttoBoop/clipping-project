from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_rio_economic_panel_is_hidden_by_default_and_readonly():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert 'id="rioEconomicReportPanel"' in html
    assert 'hidden>' in html
    assert "rioEconomicReportList" in html
    assert "Adicionar" not in html[html.index('id="rioEconomicReportPanel"') :]


def test_rio_economic_panel_fetch_is_profile_gated():
    js = (ROOT / "assets" / "clipping.js").read_text(encoding="utf-8")

    assert 'app.dataset.clippingSessionProfile' in js
    assert 'sessionProfile() === "rio_economico"' in js
    assert 'apiFetch("/api/reports/rio-economic-topic"' in js
    assert "viewerCanSeeRioReport()" in js
    assert "rioEconomicReportPanel.hidden = true" in js


def test_rio_economic_panel_has_styles_without_action_controls():
    css = (ROOT / "assets" / "clipping.css").read_text(encoding="utf-8")

    assert ".rio-report-panel" in css
    assert ".rio-report-item" in css
    assert ".rio-report-status" in css
