from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_rio_economic_panel_is_hidden_by_default_and_readonly():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert 'id="rioEconomicReportPanel"' in html
    assert 'hidden>' in html
    assert "rioEconomicReportList" in html
    start = html.index('<section class="rio-report-panel"')
    end = html.index("</section>", start)
    panel_html = html[start:end]
    for forbidden in ("Adicionar", "Aprovar", "Publicar", "<button", "<form"):
        assert forbidden not in panel_html


def test_rio_economic_panel_fetch_is_profile_gated():
    js = (ROOT / "assets" / "clipping.js").read_text(encoding="utf-8")

    assert 'app.dataset.clippingSessionProfile' in js
    assert 'sessionProfile() === "rio_economico"' in js
    assert 'apiFetch("/api/reports/rio-economic-topic"' in js
    assert "meta.indicator_policy_counts || meta.date_quality_policy_counts" in js
    assert "story.indicator_policy || story.date_quality_policy" in js
    assert "viewerCanSeeRioReport()" in js
    assert "rioEconomicReportPanel.hidden = true" in js
    start = js.index("function rioPolicyLabel")
    end = js.index("function renderRunTarget")
    rio_js = js[start:end]
    assert "apiPost(" not in rio_js
    assert "apiPatch(" not in rio_js
    assert "/api/targets" not in rio_js


def test_rio_economic_panel_has_styles_without_action_controls():
    css = (ROOT / "assets" / "clipping.css").read_text(encoding="utf-8")

    assert ".rio-report-panel" in css
    assert ".rio-report-item" in css
    assert ".rio-report-status" in css
