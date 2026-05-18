"""Performance benchmark suite for the Pages clipping bundle.

Measures memory (JS heap), DOM node count, and timing at each interaction
step. Also generates synthetic heavy HTML files to identify at what point
performance degrades.

Produces a human-readable report — NOT pass/fail with arbitrary thresholds.
The goal is to measure deltas and identify bottlenecks.

Run with:
    .venv_playwright/bin/pytest tests/test_pages_performance.py -v -s
"""
from __future__ import annotations

import functools
import http.server
import json
import textwrap
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "data" / "reports" / "performance_benchmark.md"

# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def snapshot_metrics(page, label: str) -> dict:
    """Capture memory, DOM count, and timestamp from the browser."""
    metrics = page.evaluate("""() => {
        const perf = performance.memory || {};
        return {
            jsHeapUsedMB: Math.round((perf.usedJSHeapSize || 0) / 1024 / 1024 * 10) / 10,
            jsHeapTotalMB: Math.round((perf.totalJSHeapSize || 0) / 1024 / 1024 * 10) / 10,
            domNodes: document.querySelectorAll('*').length,
            articleCards: document.querySelectorAll('.article-card').length,
            storyCards: document.querySelectorAll('.story-card').length,
            timestamp: performance.now(),
        };
    }""")
    metrics["label"] = label
    return metrics


def format_report(snapshots: list[dict], title: str) -> str:
    """Format a list of metric snapshots as a markdown table."""
    lines = [
        f"### {title}\n",
        "| Step | JS Heap (MB) | DOM Nodes | Articles | Stories | Time (ms) |",
        "|------|-------------|-----------|----------|---------|-----------|",
    ]
    t0 = snapshots[0]["timestamp"] if snapshots else 0
    for s in snapshots:
        elapsed = round(s["timestamp"] - t0)
        lines.append(
            f"| {s['label']} | {s['jsHeapUsedMB']} | {s['domNodes']} "
            f"| {s['articleCards']} | {s['storyCards']} | {elapsed} |"
        )

    # Delta summary
    if len(snapshots) >= 2:
        first, last = snapshots[0], snapshots[-1]
        lines.append("")
        lines.append(f"**Delta (first → last):** "
                      f"Heap {first['jsHeapUsedMB']} → {last['jsHeapUsedMB']} MB, "
                      f"DOM {first['domNodes']} → {last['domNodes']} nodes")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Synthetic HTML generator for stress tests
# ---------------------------------------------------------------------------

def generate_synthetic_html(article_count: int, output_path: Path) -> None:
    """Generate a minimal HTML file with N article cards directly in the DOM.

    This simulates the worst case: all articles rendered upfront as static HTML.
    """
    articles = []
    for i in range(article_count):
        articles.append(f"""
        <article class="article-card" id="article-{i}">
          <div class="article-top">
            <div>
              <h3><a href="https://example.com/article-{i}" target="_blank">
                Artigo sintetico numero {i} para benchmark de stress
              </a></h3>
              <p class="article-meta">
                <span>Fonte Teste</span>
                <span>01/01/2026 00:00 UTC</span>
                <span>example.com</span>
              </p>
            </div>
            <div class="chips"><span class="chip">Teste</span></div>
          </div>
          <div class="article-links">
            <a href="https://example.com/article-{i}" target="_blank">Abrir materia</a>
          </div>
          <div class="summary-box summary-raw">
            <div class="summary-label">Texto bruto</div>
            <div class="body-text">{"Lorem ipsum dolor sit amet. " * 20}</div>
          </div>
        </article>""")

    html = textwrap.dedent(f"""\
    <!doctype html>
    <html lang="pt-BR">
    <head>
      <meta charset="utf-8">
      <title>Stress Test - {article_count} articles</title>
      <link rel="stylesheet" href="/assets/clipping.css">
    </head>
    <body>
      <main id="app">
        <section id="flatStack" class="flat-articles">
          {"".join(articles)}
        </section>
      </main>
      <script>
        // Signal that rendering is complete
        document.getElementById("app").dataset.loaded = "true";
      </script>
    </body>
    </html>
    """)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def local_server():
    """Start a local HTTP server serving the project root."""
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(ROOT)
    )
    server = http.server.HTTPServer(("127.0.0.1", 0), handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    port = server.server_address[1]
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture(scope="module")
def browser_ctx():
    """Launch Playwright Chromium with memory metrics enabled."""
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=True,
        args=["--enable-precise-memory-info", "--js-flags=--expose-gc"],
    )
    context = browser.new_context()
    yield context
    context.close()
    browser.close()
    pw.stop()


@pytest.fixture(scope="module")
def benchmark_report():
    """Collector for benchmark sections. Writes report at end."""
    sections = []
    yield sections
    # Write final report
    report = "# Performance Benchmark Report\n\n"
    report += "\n\n".join(sections)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\n\n{'='*60}")
    print(f"Benchmark report written to: {REPORT_PATH}")
    print(f"{'='*60}\n")
    print(report)


# ---------------------------------------------------------------------------
# Benchmark: Pages version in stages
# ---------------------------------------------------------------------------

class TestPagesBenchmark:
    def test_pages_step_by_step(self, browser_ctx, local_server, benchmark_report):
        """Measure Pages version at each interaction step."""
        page = browser_ctx.new_page()
        snapshots = []
        held_data_route = {}

        def hold_data_response(route):
            held_data_route["route"] = route

        page.route("**/assets/clipping-data.json", hold_data_response)

        # 1. Navigate
        page.goto(f"{local_server}/index.html", wait_until="domcontentloaded")
        page.wait_for_timeout(100)
        snapshots.append(snapshot_metrics(page, "DOM loaded (shell only)"))

        if "route" in held_data_route:
            held_data_route["route"].fulfill(
                status=200,
                content_type="application/json",
                body=(ROOT / "assets" / "clipping-data.json").read_text(encoding="utf-8"),
            )
            page.unroute("**/assets/clipping-data.json", hold_data_response)
        else:
            page.unroute("**/assets/clipping-data.json", hold_data_response)

        # 2. Wait for data fetch + initial render
        page.wait_for_function("document.getElementById('loadingState')?.hidden === true", timeout=30000)
        snapshots.append(snapshot_metrics(page, "Data loaded + first batch"))

        # 3. Load more (5 batches)
        for i in range(5):
            btn = page.query_selector(".load-more-btn")
            if not btn:
                break
            btn.click()
            page.wait_for_timeout(300)
            snapshots.append(snapshot_metrics(page, f"After load-more #{i+1}"))

        # 4. Switch to grouped view
        page.click('[data-sort="hottest"]')
        page.wait_for_selector("#storyStack:not([hidden])", timeout=10000)
        snapshots.append(snapshot_metrics(page, "Switched to grouped view"))

        # 5. Switch back to newest
        page.click('[data-sort="newest"]')
        page.wait_for_selector("#flatStack:not([hidden])", timeout=10000)
        snapshots.append(snapshot_metrics(page, "Switched back to newest"))

        # 6. Toggle a filter
        chips = page.query_selector_all("[data-filter-target]")
        if len(chips) >= 2:
            chips[1].click()
            page.wait_for_timeout(300)
            snapshots.append(snapshot_metrics(page, "After filter toggle"))

        # 7. Open raw text (scroll to a visible article first)
        details = page.query_selector("#flatStack .raw-details summary")
        if details:
            details.scroll_into_view_if_needed(timeout=5000)
            details.click(timeout=5000)
            page.wait_for_timeout(2000)
            snapshots.append(snapshot_metrics(page, "After raw text open"))

        page.close()

        section = format_report(snapshots, "Pages Version — Step by Step")
        benchmark_report.append(section)

        # Basic sanity: initial DOM should be small
        initial_dom = snapshots[0]["domNodes"]
        assert initial_dom < 500, f"Initial shell has {initial_dom} DOM nodes (expected <500)"


# ---------------------------------------------------------------------------
# Benchmark: Synthetic stress test
# ---------------------------------------------------------------------------

class TestSyntheticStress:
    @pytest.mark.parametrize("article_count", [100, 500, 1000, 2000])
    def test_synthetic_load(self, browser_ctx, local_server, benchmark_report, article_count):
        """Measure load metrics for synthetic HTML with N articles in DOM."""
        synthetic_path = ROOT / "data" / "reports" / f"_synthetic_{article_count}.html"
        try:
            generate_synthetic_html(article_count, synthetic_path)

            page = browser_ctx.new_page()
            snapshots = []

            page.goto(
                f"{local_server}/data/reports/_synthetic_{article_count}.html",
                wait_until="domcontentloaded",
            )
            snapshots.append(snapshot_metrics(page, f"DOM loaded ({article_count} articles)"))

            page.wait_for_selector('[data-loaded="true"]', timeout=30000)
            snapshots.append(snapshot_metrics(page, f"Render complete ({article_count} articles)"))

            page.close()

            section = format_report(
                snapshots,
                f"Synthetic Stress — {article_count} articles inline"
            )
            benchmark_report.append(section)
        finally:
            synthetic_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Functional verification (kept as sanity checks)
# ---------------------------------------------------------------------------

class TestFunctionalSanity:
    def test_articles_visible_after_load(self, browser_ctx, local_server):
        """At least some articles should be visible after load."""
        page = browser_ctx.new_page()
        page.goto(f"{local_server}/index.html", wait_until="networkidle")
        page.wait_for_function("document.getElementById('loadingState')?.hidden === true", timeout=30000)
        articles = page.query_selector_all("#flatStack .article-card")
        count = len(articles)
        page.close()
        assert count >= 10, f"Only {count} articles visible"

    def test_outros_candidatos_exists(self, browser_ctx, local_server):
        """Outros candidatos section should exist."""
        page = browser_ctx.new_page()
        page.goto(f"{local_server}/index.html", wait_until="networkidle")
        page.wait_for_function("document.getElementById('loadingState')?.hidden === true", timeout=30000)
        outros = page.query_selector("#outrosFilters")
        page.close()
        assert outros is not None

    def test_new_secondary_target_filter_is_visible_after_opening_outros(self, browser_ctx, local_server):
        """New active secondary targets should be visible and selectable in the filter UI."""
        page = browser_ctx.new_page()
        page.goto(f"{local_server}/index.html", wait_until="networkidle")
        page.wait_for_function("document.getElementById('loadingState')?.hidden === true", timeout=30000)
        page.click("#outrosFilters summary")
        page.wait_for_timeout(200)
        shakira = page.locator('[data-filter-target="shakira"]').first
        text = shakira.inner_text()
        visible = shakira.is_visible()
        shakira.click()
        page.wait_for_timeout(200)
        active = shakira.evaluate("el => el.classList.contains('active')")
        page.close()

        assert visible
        assert "Shakira" in text
        assert "0 histórias" in text
        assert active

    def test_add_target_shows_structured_validation_error_from_api(self, browser_ctx, local_server):
        """The add-target form should show API cause/suggestion, not a generic fallback."""
        page = browser_ctx.new_page()

        def csrf(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"csrf": "test-csrf"}),
            )

        def targets(route):
            if route.request.method == "POST":
                route.fulfill(
                    status=400,
                    content_type="application/json",
                    body=json.dumps(
                        {
                            "error": "target_validation_error",
                            "message": "Informe um nome de exibicao com pelo menos 3 caracteres.",
                            "field": "display_name",
                            "suggestion": "Digite um nome de exibicao com 3 caracteres ou mais.",
                            "detail": {
                                "code": "target_validation_error",
                                "message": "Informe um nome de exibicao com pelo menos 3 caracteres.",
                                "field": "display_name",
                                "suggestion": "Digite um nome de exibicao com 3 caracteres ou mais.",
                            },
                        },
                        ensure_ascii=False,
                    ),
                )
                return
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "targets": [
                            {"key": "flavio_valle", "label": "Flávio Valle", "primary": True},
                            {"key": "shakira", "label": "Shakira", "primary": False},
                        ],
                        "primaryKeys": ["flavio_valle"],
                    },
                    ensure_ascii=False,
                ),
            )

        def update_status(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"current": {"status": "idle"}, "recent": []}),
            )

        def live_results(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({"items": []}))

        page.route("**/api/csrf", csrf)
        page.route("**/api/targets**", targets)
        page.route("**/api/update/status", update_status)
        page.route("**/api/update/live-results**", live_results)

        try:
            page.goto(f"{local_server}/index.html", wait_until="domcontentloaded")
            page.wait_for_function("document.getElementById('loadingState')?.hidden === true", timeout=30000)
            page.locator("details.add-target-box").evaluate("el => { el.open = true; }")
            page.fill('#addTargetForm input[name="display_name"]', "Ana Teste")
            page.click('#addTargetForm button[type="submit"]')
            page.wait_for_selector("#addTargetMessage.is-error", timeout=10000)
            message = page.locator("#addTargetMessage").inner_text()
        finally:
            page.close()

        assert "Informe um nome de exibicao com pelo menos 3 caracteres." in message
        assert "Digite um nome de exibicao com 3 caracteres ou mais." in message
        assert "Não foi possível salvar este nome." not in message

    def test_live_results_target_outside_initial_targets_becomes_filterable(self, browser_ctx, local_server):
        """A live saved article should expose its target as a selectable filter."""
        page = browser_ctx.new_page()

        def targets(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "targets": [
                            {"key": "flavio_valle", "label": "Flávio Valle", "primary": True},
                        ],
                        "primaryKeys": ["flavio_valle"],
                    },
                    ensure_ascii=False,
                ),
            )

        def update_status(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"current": {"status": "idle"}, "recent": []}),
            )

        def live_results(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "items": [
                            {
                                "articleId": 99001,
                                "storyId": 99001,
                                "title": "Projeto Zeta salvo na Base atual",
                                "url": "https://example.com/projeto-zeta",
                                "sourceName": "Fonte Teste",
                                "publishedAt": "2026-05-19T12:00:00+00:00",
                                "savedAt": "2026-05-19T12:03:00+00:00",
                                "snippet": "Projeto Zeta entrou pelo overlay ao vivo.",
                                "summary": "Projeto Zeta entrou pelo overlay ao vivo.",
                                "publicationState": "saved",
                                "targetKeys": ["projeto_zeta"],
                                "targetLabels": {"projeto_zeta": "Projeto Zeta"},
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
            )

        page.route("**/api/targets**", targets)
        page.route("**/api/update/status", update_status)
        page.route("**/api/update/live-results**", live_results)

        try:
            page.goto(f"{local_server}/index.html", wait_until="domcontentloaded")
            page.wait_for_function("document.getElementById('loadingState')?.hidden === true", timeout=30000)
            page.wait_for_selector("#outrosFilters", timeout=10000)
            page.click("#outrosFilters summary")
            projeto_zeta = page.locator('[data-filter-target="projeto_zeta"]').first
            projeto_zeta.wait_for(state="visible", timeout=10000)
            text = projeto_zeta.inner_text()
            projeto_zeta.click()
            page.wait_for_selector("#flatStack .article-card:has-text('Projeto Zeta salvo na Base atual')", timeout=10000)
            active = projeto_zeta.evaluate("el => el.classList.contains('active')")
        finally:
            page.close()

        assert "Projeto Zeta" in text
        assert "1 história" in text
        assert active

    def test_manage_target_edit_stays_available_during_running_update(self, browser_ctx, local_server):
        """A running update should not block editing names for future/base sync."""
        page = browser_ctx.new_page()
        current_label = {"value": "Ana Teste"}

        def csrf(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"csrf": "test-csrf"}),
            )

        def targets(route):
            url = route.request.url
            rows = [
                {"key": "flavio_valle", "label": "Flávio Valle", "primary": True, "archived": False},
                {"key": "ana_teste", "label": current_label["value"], "primary": False, "archived": False},
            ]
            body = {"targets": rows, "primaryKeys": ["flavio_valle"]}
            if "include_archived=1" not in url:
                body["targets"] = [row for row in rows if not row.get("archived")]
            route.fulfill(status=200, content_type="application/json", body=json.dumps(body, ensure_ascii=False))

        def update_target(route):
            current_label["value"] = "Ana Nova"
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "key": "ana_teste",
                        "label": "Ana Nova",
                        "primary": False,
                        "archived": False,
                        "targetSync": {
                            "targetKey": "ana_teste",
                            "updatedCount": 0,
                            "mentionsInserted": 0,
                            "storiesTouched": 0,
                        },
                        "activeJobNotice": (
                            "Alteração salva agora. A atualização em andamento continua com os nomes "
                            "congelados no início; esta mudança vale para a Base atual e para as próximas rodadas."
                        ),
                    },
                    ensure_ascii=False,
                ),
            )

        def update_status(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "current": {
                            "id": "running-update",
                            "status": "running",
                            "progress": {"targetKeys": ["flavio_valle"]},
                        },
                        "recent": [],
                    }
                ),
            )

        def live_results(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({"items": []}))

        def route_targets(route):
            if route.request.method == "PATCH":
                update_target(route)
                return
            targets(route)

        page.route("**/api/csrf", csrf)
        page.route("**/api/targets**", route_targets)
        page.route("**/api/update/status", update_status)
        page.route("**/api/update/live-results**", live_results)

        try:
            page.goto(f"{local_server}/index.html", wait_until="domcontentloaded")
            page.wait_for_function("document.getElementById('loadingState')?.hidden === true", timeout=30000)
            page.locator("#manageTargetsBox").evaluate("el => { el.open = true; }")
            page.wait_for_selector('[data-target-edit="ana_teste"]:not([disabled])', timeout=10000)
            assert page.locator("#manageTargetsBlocked").is_hidden()
            page.click('[data-target-edit="ana_teste"]')
            name_input = page.locator('[data-manage-target-key="ana_teste"] input[name="display_name"]')
            name_input.wait_for(state="visible", timeout=10000)
            assert name_input.is_enabled()
            name_input.fill("Ana Nova")
            page.click('[data-manage-target-key="ana_teste"] button[type="submit"]')
            page.wait_for_selector("#manageTargetsMessage.is-ok", timeout=10000)
            message = page.locator("#manageTargetsMessage").inner_text()
        finally:
            page.close()

        assert "Nome extra atualizado." in message
        assert "A base atual foi conferida para esse nome." in message
        assert "continua com os nomes congelados" in message
        assert "Aguarde a atualização terminar" not in message

    def test_manage_target_archive_restore_stay_available_during_running_update(self, browser_ctx, local_server):
        """Archive/restore controls should stay usable while the active job uses its snapshot."""
        page = browser_ctx.new_page()
        rows = {
            "ana_teste": {
                "key": "ana_teste",
                "label": "Ana Teste",
                "primary": False,
                "archived": False,
            },
            "beta_antigo": {
                "key": "beta_antigo",
                "label": "Beta Antigo",
                "primary": False,
                "archived": True,
                "archive_reason": "Cadastro antigo.",
            },
        }

        def csrf(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"csrf": "test-csrf"}),
            )

        def targets(route):
            target_rows = [
                {"key": "flavio_valle", "label": "Flávio Valle", "primary": True, "archived": False},
                rows["ana_teste"],
                rows["beta_antigo"],
            ]
            if "include_archived=1" not in route.request.url:
                target_rows = [row for row in target_rows if not row.get("archived")]
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"targets": target_rows, "primaryKeys": ["flavio_valle"]}, ensure_ascii=False),
            )

        def archive(route):
            rows["ana_teste"] = {
                **rows["ana_teste"],
                "archived": True,
                "archive_reason": "Arquivado pelo painel de gerenciamento.",
            }
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        **rows["ana_teste"],
                        "activeJobNotice": (
                            "Alteração salva agora. A atualização em andamento continua com os nomes "
                            "congelados no início; esta mudança vale para a Base atual e para as próximas rodadas."
                        ),
                    },
                    ensure_ascii=False,
                ),
            )

        def restore(route):
            rows["beta_antigo"] = {**rows["beta_antigo"], "archived": False}
            rows["beta_antigo"].pop("archive_reason", None)
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        **rows["beta_antigo"],
                        "targetSync": {
                            "targetKey": "beta_antigo",
                            "updatedCount": 0,
                            "mentionsInserted": 0,
                            "storiesTouched": 0,
                        },
                        "activeJobNotice": (
                            "Alteração salva agora. A atualização em andamento continua com os nomes "
                            "congelados no início; esta mudança vale para a Base atual e para as próximas rodadas."
                        ),
                    },
                    ensure_ascii=False,
                ),
            )

        def route_targets(route):
            if route.request.method == "POST" and route.request.url.endswith("/archive"):
                archive(route)
                return
            if route.request.method == "POST" and route.request.url.endswith("/restore"):
                restore(route)
                return
            targets(route)

        def update_status(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"current": {"id": "running-update", "status": "running"}, "recent": []}),
            )

        def live_results(route):
            route.fulfill(status=200, content_type="application/json", body=json.dumps({"items": []}))

        page.route("**/api/csrf", csrf)
        page.route("**/api/targets**", route_targets)
        page.route("**/api/update/status", update_status)
        page.route("**/api/update/live-results**", live_results)

        try:
            page.goto(f"{local_server}/index.html", wait_until="domcontentloaded")
            page.wait_for_function("document.getElementById('loadingState')?.hidden === true", timeout=30000)
            page.locator("#manageTargetsBox").evaluate("el => { el.open = true; }")
            page.wait_for_selector('[data-target-archive-start="ana_teste"]:not([disabled])', timeout=10000)
            page.click('[data-target-archive-start="ana_teste"]')
            page.wait_for_selector('[data-target-archive-confirm="ana_teste"]:not([disabled])', timeout=10000)
            page.click('[data-target-archive-confirm="ana_teste"]')
            page.wait_for_selector("#manageTargetsMessage.is-ok", timeout=10000)
            archive_message = page.locator("#manageTargetsMessage").inner_text()

            page.locator("details.archived-targets-box").evaluate("el => { el.open = true; }")
            page.wait_for_selector('[data-target-restore="beta_antigo"]:not([disabled])', timeout=10000)
            page.click('[data-target-restore="beta_antigo"]')
            page.wait_for_function(
                "document.getElementById('manageTargetsMessage')?.textContent.includes('Nome restaurado')",
                timeout=10000,
            )
            restore_message = page.locator("#manageTargetsMessage").inner_text()
        finally:
            page.close()

        assert "Nome arquivado." in archive_message
        assert "continua com os nomes congelados" in archive_message
        assert "Aguarde a atualização terminar" not in archive_message
        assert "Nome restaurado. Ele já vale para a Base atual e para próximas rodadas." in restore_message
        assert "A base atual foi conferida para esse nome." in restore_message
        assert "continua com os nomes congelados" in restore_message
        assert "Aguarde a atualização terminar" not in restore_message

    def test_load_more_works(self, browser_ctx, local_server):
        """Load-more button should increase article count."""
        page = browser_ctx.new_page()
        page.goto(f"{local_server}/index.html", wait_until="networkidle")
        page.wait_for_function("document.getElementById('loadingState')?.hidden === true", timeout=30000)
        before = len(page.query_selector_all("#flatStack .article-card"))
        btn = page.query_selector(".load-more-btn")
        if btn:
            btn.click()
            page.wait_for_timeout(500)
        after = len(page.query_selector_all("#flatStack .article-card"))
        page.close()
        assert after > before
