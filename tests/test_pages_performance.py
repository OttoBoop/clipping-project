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

        # 1. Navigate
        page.goto(f"{local_server}/index.html", wait_until="domcontentloaded")
        snapshots.append(snapshot_metrics(page, "DOM loaded (shell only)"))

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
