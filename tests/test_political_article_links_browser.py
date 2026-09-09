"""Opt-in browser checks of the actual dashboard JS with intercepted API reads.

No server, login, production requests, collection or database writes occur.
Run CLIPPING_BROWSER_TESTS=1 with Playwright Chromium installed.
"""
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("CLIPPING_BROWSER_TESTS") != "1", reason="opt-in Playwright browser check")
ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://clipping.test"


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        instance = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        yield instance
        instance.close()


@pytest.fixture
def dashboard(browser):
    context = browser.new_context(locale="pt-BR")
    page = context.new_page()
    calls, errors = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    article = {"id": 49, "title": "Matéria salva para consulta", "url": "https://publisher.example/noticia",
               "targetKeys": ["eduardo_paes"], "bodyStatus": "body_extracted"}

    def serve(route):
        parsed = urlparse(route.request.url)
        path = parsed.path
        calls.append((route.request.method, path, parse_qs(parsed.query)))
        assert parsed.netloc == "clipping.test", "dashboard must not fetch a publisher or another origin"
        assert route.request.method == "GET", "opening a saved article must not mutate anything"
        if path == "/politica":
            html = (ROOT / "web_app/templates/political.html").read_text().replace("{{ROLE}}", "viewer").replace("{{PROFILE}}", "PSD")
            route.fulfill(status=200, content_type="text/html", body=html)
        elif path == "/assets/political.js":
            route.fulfill(status=200, content_type="application/javascript", body=(ROOT / "assets/political.js").read_text())
        elif path == "/assets/political.css":
            route.fulfill(status=200, content_type="text/css", body="")
        elif path == "/api/political/meta":
            route.fulfill(json={"configured": True, "canRun": False, "targets": [{"key": "eduardo_paes", "display_name": "Eduardo Paes"}],
                                "defaultTargets": ["eduardo_paes"], "clientProfile": "psd_rj_2026"})
        elif path == "/api/csrf":
            route.fulfill(json={"csrf": "local-ui-fixture"})
        elif path == "/api/political/sources":
            route.fulfill(json={"sources": []})
        elif path == "/api/political/status":
            route.fulfill(json={"current": None, "workers": []})
        elif path == "/api/political/articles":
            # The linked article is deliberately absent from the first page.
            route.fulfill(json={"items": [{**article, "id": 7}], "hasMore": True, "nextCursor": "page-two"})
        elif path == "/api/political/articles/49":
            route.fulfill(json=article)
        elif path in {"/api/political/articles/403", "/api/political/articles/404"}:
            status = int(path.rsplit("/", 1)[-1])
            route.fulfill(status=status, json={"detail": "political_scope_denied" if status == 403 else "political_record_not_found"})
        elif path in {"/api/political/articles/49/text", "/api/political/articles/7/text"}:
            route.fulfill(json={"id": int(path.split("/")[-2]), "text": "Texto editorial salvo.", "bodyStatus": "body_extracted"})
        elif path.endswith("/classifications"):
            route.fulfill(json={"items": []})
        else:
            pytest.fail(f"Unexpected API or archive request: {path}")

    page.route("**/*", serve)
    yield page, calls, errors
    context.close()


def test_direct_article_uses_scoped_metadata_without_scanning_pages(dashboard):
    from playwright.sync_api import expect

    page, calls, errors = dashboard
    page.goto(ORIGIN + "/politica?client=psd_rj_2026&article=49")
    expect(page.locator("#article-dialog")).to_be_visible()
    expect(page.locator("#article-title")).to_have_text("Matéria salva para consulta")
    expect(page.locator("#article-text")).to_have_text("Texto editorial salvo.")
    expect(page.locator("#classification-target")).to_have_value("eduardo_paes")
    expect(page.locator("#article-message a")).to_have_attribute("href", "https://publisher.example/noticia")
    paths = [path for _, path, _ in calls]
    assert paths.count("/api/political/articles") == 1
    assert paths.count("/api/political/articles/49") == 1
    assert all(query.get("client") == ["psd_rj_2026"] for _, path, query in calls if path.startswith("/api/"))
    assert not errors
    page.locator("#close-article").click()
    expect(page.locator("#article-dialog")).not_to_be_visible()
    # Native dialog.close() hides the dialog before dispatching its close event.
    expect(page).to_have_url(ORIGIN + "/politica?client=psd_rj_2026")
    assert parse_qs(urlparse(page.url).query) == {"client": ["psd_rj_2026"]}


def test_direct_article_preserves_read_only_simulation_and_escape(dashboard):
    from playwright.sync_api import expect

    page, calls, errors = dashboard
    page.goto(ORIGIN + "/politica?as_profile=psd_rj_2026&article=49")
    expect(page.locator("#article-text")).to_have_text("Texto editorial salvo.")
    expect(page.locator("#classification")).not_to_be_visible()
    assert all(query.get("as_profile") == ["psd_rj_2026"] for _, path, query in calls if path.startswith("/api/"))
    page.keyboard.press("Escape")
    expect(page.locator("#article-dialog")).not_to_be_visible()
    expect(page).to_have_url(ORIGIN + "/politica?as_profile=psd_rj_2026")
    assert parse_qs(urlparse(page.url).query) == {"as_profile": ["psd_rj_2026"]}
    assert not errors


@pytest.mark.parametrize("query", ["0", "9007199254740992", "49%2Ftext", "49&article=50"])
def test_invalid_link_never_requests_article_detail(dashboard, query):
    from playwright.sync_api import expect

    page, calls, errors = dashboard
    page.goto(ORIGIN + "/politica?article=" + query)
    expect(page.locator("#message")).to_have_text("O link da notícia é inválido.")
    expect(page.locator("#article-dialog")).not_to_be_visible()
    assert not any(path.startswith("/api/political/articles/") for _, path, _ in calls)
    assert not errors


@pytest.mark.parametrize("article_id", [403, 404])
def test_missing_or_inaccessible_article_does_not_load_body(dashboard, article_id):
    from playwright.sync_api import expect

    page, calls, errors = dashboard
    page.goto(ORIGIN + f"/politica?article={article_id}")
    expect(page.locator("#message")).to_contain_text("perfil")
    expect(page.locator("#article-dialog")).not_to_be_visible()
    assert not any(path.endswith("/text") or path.endswith("/classifications") for _, path, _ in calls)
    assert not errors


def test_opening_existing_card_creates_shareable_article_url(dashboard):
    from playwright.sync_api import expect

    page, calls, errors = dashboard
    page.goto(ORIGIN + "/politica?client=psd_rj_2026")
    page.get_by_role("button", name="Ler e classificar").click()
    expect(page.locator("#article-text")).to_have_text("Texto editorial salvo.")
    assert parse_qs(urlparse(page.url).query) == {"client": ["psd_rj_2026"], "article": ["7"]}
    assert not errors
