# Forensic Inventory — Clipping Project File States

**Date:** 2026-03-30
**Analyst:** Claude Opus 4.6 (forensic session)
**Scope:** Every .py file in D:\recovery\clipping-project\ plus key non-code files

---

## Summary

| Category | Count | Files |
|----------|-------|-------|
| RECONSTRUCTED | 9 | pipeline/collectors.py, database.py, http_utils.py, ingest.py, matcher.py, normalization.py, settings.py, run_ingestion.py, tools/export_mobile_snapshot.py |
| RECOVERED_CORRUPTED | 12 | server.py, tools/backfill_google.py, tools/benchmark_sources_vs_excel.py, tools/cbn_search_diagnostic.py, tools/fix_encoding.py, tests/test_flavio_query_expansion.py, test_http_utils.py, test_odia_r7_site_collectors.py, test_internal_site_search_collectors.py, test_run_ingestion_dedup.py, test_cbn_source_recovery.py, test_source_recovery_collectors.py |
| STUB | 5 | pipeline/__init__.py, tools/benchmark_auto_vs_excel.py, tools/prepare_wix_clipping_snapshot.py, tests/test_internal_site_search_ingest.py, tests/test_wordpress_site_collectors.py |
| WRONG_CONTENT | 5 | tools/generate_flavio_valle_print_pdf.py (CLAUDE.md), tests/test_direct_scrape_windows.py, test_export_mobile_snapshot.py, test_globo_family_diagnostic.py, test_google_news_collector.py |
| RECOVERED_FRAGMENT | 1 | tests/test_benchmark_sources_vs_excel.py |
| RECOVERED_VALID | 1 | data/targets.json |

---

## Detailed File Inventory

### Pipeline Files

| # | File | Classification | Lines | First 5 Lines | Assessment |
|---|------|---------------|-------|---------------|------------|
| 1 | `pipeline/__init__.py` | **STUB** | 0 | *(empty)* | Expected — just a package marker. OK as-is. |
| 2 | `pipeline/collectors.py` | **RECONSTRUCTED** | 521 | `"""News source collectors..."""` / `import html as html_mod` / `import json` / `import re` / `import time` | Fresh rewrite on 2026-03-30. Contains 11 functions + 1 dataclass. Covers Google News, RSS, WordPress, Globo API, HTML search, sitemap, Camara, Veja Rio. Missing: `collect_direct_scrape`, site-specific extractors (Camara HTML, CONIB, Veja Rio selectors), `_extract_internal_search_results`. Architecture matches original but **simplified** — original had per-site adapter objects. Must rewrite to match original architecture. |
| 3 | `pipeline/database.py` | **RECONSTRUCTED** | 114 | `"""SQLite database..."""` / `import sqlite3` / `from pathlib import Path` / `class ClippingDB:` | Fresh rewrite. Schema matches recovered notes exactly (articles, mentions, story_articles). 7 methods. Clean and functional. Missing: some advanced query methods from original. Usable as-is for basic pipeline. |
| 4 | `pipeline/http_utils.py` | **RECONSTRUCTED** | 76 | `"""HTTP utilities..."""` / `import json` / `import random` / `import re` / `import warnings` | Fresh rewrite. Contains `fetch_url`, `post_json`, `try_resolve_google_redirect`. Missing from original: `_build_ssl_fallback_context`, retry logic, more sophisticated error handling. Functional but simplified. |
| 5 | `pipeline/ingest.py` | **RECONSTRUCTED** | 202 | `"""Main ingestion orchestrator..."""` / `import json` / `from dataclasses import dataclass, field` / `from pathlib import Path` | Fresh rewrite. Contains `IngestionOptions`, `load_targets`, `run_ingestion`. Architecture matches: collect -> dedupe -> match -> store. Missing: `process_candidates` (referenced in tests), per-source query variants, forced terms, progress callbacks, budget control. Simplified from original. |
| 6 | `pipeline/matcher.py` | **RECONSTRUCTED** | 61 | `"""Keyword matching..."""` / `from dataclasses import dataclass, field` / `@dataclass` / `class Target:` | Fresh rewrite. `Target`, `MatchHit`, `CitationMatcher` with `find_hits`. Clean, matches known signatures. Very close to original (simple module). Usable as-is. |
| 7 | `pipeline/normalization.py` | **RECONSTRUCTED** | 56 | `"""URL and text normalization..."""` / `import html as html_mod` / `import re` / `from urllib.parse import...` | Fresh rewrite. `normalize_url`, `canonicalize_url`, `clean_title`. Standard URL normalization. Functional. |
| 8 | `pipeline/settings.py` | **RECONSTRUCTED** | 73 | `"""Source configurations..."""` / `from dataclasses import dataclass` / `@dataclass` / `class InternalSearchTarget:` | Fresh rewrite. Contains 7 search targets (O Globo, Extra, CBN, O Dia, R7, CONIB, Diario do Rio), WordPress hosts, RSS feeds (empty list), sitemap configs (CBN only). Missing from original: ~164 lines of richer config, RSS feed entries, more sitemap sources, benchmark configs. |

### Root Files

| # | File | Classification | Lines | First 5 Lines | Assessment |
|---|------|---------------|-------|---------------|------------|
| 9 | `run_ingestion.py` | **RECONSTRUCTED** | 60 | `#!/usr/bin/env python3` / `"""CLI entry point..."""` / `import argparse` / `import sys` / `from datetime import...` | Fresh rewrite. Clean argparse CLI matching recovered signatures. Functional. |
| 10 | `server.py` | **RECOVERED_CORRUPTED** | 313 | `exact_aliases = row.get(\"exact_aliases\", [])` / `if isinstance(exact_aliases, str):` / `exact_aliases = [part.strip()...` | **Heavily corrupted.** First ~37 lines contain real Python fragments from the original server (alias parsing, collector routing, API endpoint code). Lines 38+ are binary Codex telemetry data (tokio-tungstenite traces, SSE events, base64 data) with occasional embedded code fragments. `file` command reports "data" (not valid text). Contains HTML/CSS diff fragments toward the end. **Extractable: alias parsing logic, collector routing dict, allowed collectors list, archive_sources logic, CSS for rich HTML export.** Cannot be cleaned — must be rewritten using extracted fragments as reference. |

### Tool Files

| # | File | Classification | Lines | First 5 Lines | Assessment |
|---|------|---------------|-------|---------------|------------|
| 11 | `tools/backfill_google.py` | **RECOVERED_CORRUPTED** | 228 | Same content as `tools/cbn_search_diagnostic.py` — starts with grep output listing general_scraper files: `C:\Users\Admin\.vscode\general_scraper\...browser_engine.py:12:from playwright...` | **Wrong content interleaved.** Contains grep output from a Codex file-search operation, NOT Python code. The content is a listing of Playwright-related references across the general_scraper project. Has a binary corruption byte on line 14. Not original code. Must be fully rewritten. |
| 12 | `tools/benchmark_auto_vs_excel.py` | **STUB** | 0 (1 line, content: `path = re.sub(...)`) | Single line of regex code: `path = re.sub(r"(?:/(?:n\|r\|rn))+$", "", path, flags=re.I)` | Tiny fragment. Not useful alone. Must be rewritten. |
| 13 | `tools/benchmark_sources_vs_excel.py` | **RECOVERED_CORRUPTED** | 708 | `FLAVIO_QUERY_VARIANTS,` / `raw_candidates = source_module.collect(...)` / `raw_urls = {normalize_url(...)}` / `raw_urls = {url for url in...}` / `raw = str(url or \"\").strip()` | **`file` reports "data"** — binary corruption mixed in. First few lines are real Python fragments (import references, URL processing). Has a large base64/JSON blob on line 6. Contains 12 def/class signatures. **Extractable: `main()`, `build_cbn_run_dir()`, `source_uses_sitemap_fast_path()`, `prepare_snapshot()`, `expand_excel_days()`, `_clean_embedded_text()`, `_json_string_to_text()`, `_collect_text_values()`, `extract_embedded_article_text()`.** Significant original logic recoverable but needs careful extraction line-by-line. |
| 14 | `tools/cbn_search_diagnostic.py` | **RECOVERED_CORRUPTED** | 228 | Identical content to backfill_google.py — grep output listing general_scraper Playwright files | Same corrupted content as backfill_google.py. Both are grep results from a Codex search operation. Not original code. Must be fully rewritten. |
| 15 | `tools/export_mobile_snapshot.py` | **RECONSTRUCTED** | 148 | `#!/usr/bin/env python3` / `"""Export clipping results..."""` / `import argparse` / `import sys` / `from datetime import datetime` | Fresh rewrite. Full HTML report generator with template, source grouping, badge rendering. 4 functions: `format_date`, `generate_html`, `main`, plus HTML_TEMPLATE. Functional. The original was richer (story cards, AI summaries, filter buttons per the corrupted test evidence). This is a simplified version. |
| 16 | `tools/fix_encoding.py` | **WRONG_CONTENT** | 1 | A single very long line (39,885 chars) containing JSON job status data | Content is a JSON blob starting with `{"job_id": "5d0ee326fe", "status": "completed"...}` — this is a Codex session/job result, not Python code. File size is 40KB. Must be fully rewritten. |
| 17 | `tools/generate_flavio_valle_print_pdf.py` | **WRONG_CONTENT** | 58 | `"story-card",` / `"has_story_cards": "story-card" in html_doc,` | Contains 2 lines of Python dict fragments, NOT a PDF generator. These fragments reference story-card HTML detection. The original was ~8.2KB per recovery notes. Must be fully rewritten. |
| 18 | `tools/prepare_wix_clipping_snapshot.py` | **STUB** | 1 | `"story-card",` / `"has_story_cards": "story-card" in html_doc,` | 2 lines of orphaned dict fragments. Not useful. Must be rewritten. |

### Test Files

| # | File | Classification | Lines | First 5 Lines | Assessment |
|---|------|---------------|-------|---------------|------------|
| 19 | `tests/test_benchmark_sources_vs_excel.py` | **RECOVERED_FRAGMENT** | 1 (2 lines) | `from pipeline.matcher import CitationMatcher` / `matcher=CitationMatcher([], exact_names_only=True),` | Tiny fragment — just an import and one usage line. Original was 1007+ lines. Must be rewritten. |
| 20 | `tests/test_cbn_source_recovery.py` | **RECOVERED_CORRUPTED** | 114 | `import sys` / `from pathlib import Path` / `project_root = Path(__file__)...` / `sys.path.insert(0, ...)` / `import pipeline.collectors as collectors` | **Mostly valid Python** for the first ~50 lines. Contains 3 test functions: `test_collect_sitemap_daily_cbn_skips_query_prefilter`, `test_citation_matcher_exact_names_only_supports_explicit_aliases`, `test_process_candidates_accepts_flavio_vale_alias`. First test has valid XML fixture and monkeypatch setup. API signatures reference `collectors.collect_sitemap_daily(queries=..., ...)` which differs from the reconstructed version. **Good reference for original API.** Likely cleanable with moderate effort. |
| 21 | `tests/test_direct_scrape_windows.py` | **WRONG_CONTENT** | 2 | `monkeypatch.setattr(ingest, \"collect_internal_site_search\"...)` / `monkeypatch.setattr(ingest, \"collect_diariodorio_site\"...)` | Fragment of monkeypatch setup from a different test. References `collect_diariodorio_site` and `collect_temporealrj_site` — functions that existed in the original but are missing from reconstruction. Not useful as a test file. |
| 22 | `tests/test_export_mobile_snapshot.py` | **WRONG_CONTENT** | 2 | `https://conib.org.br/eventos/combate-ao-antissemitismo` / `https://www.conib.org.br/pesquisar.html?searchword=...` | Contains 2 URLs and a JSON fragment — not Python test code. Not useful. |
| 23 | `tests/test_flavio_query_expansion.py` | **RECOVERED_CORRUPTED** | 361 | *(blank line)* / `def test_run_ingestion_wordpress_api_uses_site_specific_variants_and_dedupes(monkeypatch):` | **Substantial recoverable code.** Contains 12 function definitions including: WordPress variant dedup test, internal search pagination tests, Camara archive pagination test, and **3 HTML render functions** (`render_filter_buttons`, `render_story_index`, `render_article_card`). These render functions are likely from the original export tool, not tests — they were embedded via Codex patches. Some lines have escaped quotes (`\"`). **High recovery value** — reveals original export HTML generation architecture (story cards, filter buttons, article cards with labels). |
| 24 | `tests/test_globo_family_diagnostic.py` | **WRONG_CONTENT** | 2 | `Success. Updated the following files:` / `M C:\Users\Admin\.vscode\docs\The Clipping project\tests\test_source_recovery...` | Codex apply_patch success message. Not code. |
| 25 | `tests/test_google_news_collector.py` | **WRONG_CONTENT** | 2 | `Success. Updated the following files:` / `M c:\Users\Admin\.vscode\docs\The Clipping project\pipeline\collectors.py` | Codex apply_patch success message. Not code. |
| 26 | `tests/test_http_utils.py` | **RECOVERED_CORRUPTED** | 84 | Lists general_scraper file paths, then binary corruption, then Codex system prompt text | Content is a directory listing of general_scraper modules, followed by binary/base64 data, then fragments of the Codex agent system prompt ("You should not add comments like..."). Not original test code. Must be fully rewritten. |
| 27 | `tests/test_internal_site_search_collectors.py` | **RECOVERED_CORRUPTED** | 72 | `items = collectors.collect_internal_site_search(` / `queries=[\"Flavio Valle\"],` / `adapters=[adapter],` | **Significant recoverable code.** Contains parametrized test for HTML host search extraction (Veja Rio, Camara, CONIB) with real HTML fixtures and expected URLs. Has binary corruption mid-file (lines 66+). 1 proper test function + parametrize data. **Reveals original HTML selectors** for Veja Rio (card/title), Camara (dl.search-results), CONIB (article.uk-article). **High recovery value.** |
| 28 | `tests/test_internal_site_search_ingest.py` | **STUB** | 1 (2 lines) | `monkeypatch.setattr(ingest, "collect_diariodorio_site"...)` / `monkeypatch.setattr(ingest, "collect_temporealrj_site"...)` | Same fragment as test_direct_scrape_windows. References missing collectors. Not useful alone. |
| 29 | `tests/test_odia_r7_site_collectors.py` | **RECOVERED_CORRUPTED** | 84 | Same content as test_http_utils.py — directory listing + binary + Codex system prompt | Identical corruption pattern. Not original test code. Must be rewritten. |
| 30 | `tests/test_run_ingestion_dedup.py` | **RECOVERED_CORRUPTED** | 269 | `<h3 class=\"catItemTita": "C:\Windows\System32\Drivers\DriverData"...` / `<h3 class=\"catItemTitle\">...` | Starts with a corrupted mix of HTML fragment and Windows environment variables JSON. Then has valid test code: `test_collect_sitemap_daily_can_disable_prefilter_and_use_sitemap_day_membership` with XML fixture, monkeypatch setup. **Extractable:** sitemap daily test with `prefilter_queries: False` and `window_by_sitemap_day: True` config options. Also references Camara HTML selectors (`catItemTitle`). |
| 31 | `tests/test_source_recovery_collectors.py` | **RECOVERED_CORRUPTED** | 169 | `url="https://diariodorio.com/primeira-materia-sobre-flavio-valle/?utm_source=x"` / `url="https://diariodorio.com/..."` | **Mostly valid.** Contains WordPress dedup test data and 3 test functions: `test_collect_sitemap_daily_can_disable_prefilter_and_use_sitemap_day_membership`, `test_diagnose_url_row_reports_extractor_loss_when_name_only_exists_in_script`, `test_diagnose_url_row_marks_site_content_gap_when_name_absent`. References `diagnose_url_row` function not in reconstruction. **Medium recovery value.** |
| 32 | `tests/test_wordpress_site_collectors.py` | **RECOVERED_CORRUPTED** | 4 | CSS diff fragments: `i:+      font-weight: 700;` / `+      color: var(--accent);` | Contains CSS from the rich HTML export template (CSS custom properties like `--accent`, `--muted`, `--panel-strong`). Not test code. Reveals original export styling. |

### Non-.py Files

| # | File | Classification | Lines | Assessment |
|---|------|---------------|-------|------------|
| 33 | `data/targets.json` | **RECOVERED_VALID** | 21 | Clean JSON with flavio_valle target, 6 keywords, 2 exact_aliases. Functional. Original had 28 entries per recovery notes — only primary target survived. |
| 34 | `RECOVERY_NOTES.md` | **RECOVERED_VALID** | 84 | Documentation from 2026-03-29. Lists what was recovered, what's known to exist. Accurate reference. |
| 35 | `RECONSTRUCTION_PLAN.md` | **RECONSTRUCTED** | 245 | Written 2026-03-30. Detailed plan with architecture, signatures, execution order. Good reference. |
| 36 | `requirements.txt` | **RECONSTRUCTED** | 2 | `feedparser>=6.0` / `requests>=2.28`. Minimal — original likely had more deps. |
| 37 | `README.md` | **RECOVERED_CORRUPTED** | 47 | Contains real documentation about testing set, benchmarks, commands. **Usable.** References `TESTING_SET.md`, `CLIPPING CATALOGUE.md`, `tools/benchmark_sources_vs_excel.py`, `tools/globo_family_diagnostic.py`. |
| 38 | `EXPORT_HTML_OFFLINE.md` | **RECOVERED_VALID** | 15 | Short guide for offline HTML export. References original paths. |
| 39 | `FUTURE_IDEAS.md` | **WRONG_CONTENT** | 2 | Contains Windows volume serial number output, not ideas. |
| 40 | `MISSING_NEWS_ANALYSIS.md` | **RECOVERED_VALID** | 15 | Status update referencing benchmark tooling, pointing to CLIPPING CATALOGUE.md. |
| 41 | `docs/DISCOVERY_Clipping_Reconstruction_Debug.md` | **RECONSTRUCTED** | 130 | Discovery questionnaire started but incomplete (0/9 categories). Contains key design decision: "Reconstruct, don't rebuild." |

---

## Extractable Code from Corrupted Files

### server.py (313 lines)
**Extractable fragments:**
- Alias parsing logic (lines 1-15): `exact_aliases = row.get("exact_aliases", [])` with string/list handling
- Collector routing dict (lines 16-21): mapping short names to full collector names
- Allowed collectors list (lines 23-36): full list including `direct_scrape`
- `archive_sources = ordered_unique([candidate.source_name...])` pattern
- CSS diff fragments for rich HTML export (lines 64+): card styling, badge styling, story cards, article cards with `--accent`, `--panel-strong`, `--ai-bg` custom properties

### tools/benchmark_sources_vs_excel.py (708 lines)
**Extractable functions (12 defs):**
- `main() -> int` — CLI entry point
- `build_cbn_run_dir(run_id, source_module) -> Path`
- `source_uses_sitemap_fast_path(source_module, *, cbn_fast_path="auto") -> bool`
- `prepare_snapshot(args: argparse.Namespace) -> dict[str, Any]`
- `expand_excel_days(days: set[str], *, start_date, end_date, padding: int) -> set[str]`
- `_clean_embedded_text(value: str) -> str`
- `_json_string_to_text(value: str) -> str`
- `_collect_text_values(node) -> list[str]`
- `extract_embedded_article_text(raw_html: str) -> str`
- References to `SourceModule`, `FLAVIO_QUERY_VARIANTS`, `IngestionResult`, `process_candidates`

### tests/test_flavio_query_expansion.py (361 lines)
**Extractable functions (12 defs):**
- `test_run_ingestion_wordpress_api_uses_site_specific_variants_and_dedupes` — complete test with monkeypatch
- `test_collect_internal_site_search_globo_api_paginates_and_marks_body_validation` — Globo API test
- `test_collect_camara_archive_paginates_and_stops_when_window_ends` — Camara pagination test
- **`render_filter_buttons(target_rows, active_targets) -> str`** — from original export tool
- **`render_story_index(stories, visible_story_ids) -> str`** — from original export tool
- **`render_article_card(article, label_by_key) -> str`** — from original export tool
- API references: `WORDPRESS_API_SITES` (list of dicts with `source_name`, `base_url`, `query_variants`)

### tests/test_internal_site_search_collectors.py (72 lines)
**Extractable:**
- **Original HTML selectors** for 3 sites:
  - Veja Rio: `div.card .title` structure, `span.date-post`, `infiniteScroll` pagination
  - Camara do Rio: `dl.search-results`, `dt.result-title`, `dd.result-text`, `link[rel=next]` pagination
  - CONIB: `article.uk-article`, `h2 > a`, `a.next` pagination
- Parametrized test structure with `(host, search_url, html_page, expected_url, expected_next)`
- Adapter-based architecture: `_adapter(host)` factory pattern

### tests/test_cbn_source_recovery.py (114 lines)
**Extractable:**
- CBN sitemap test with XML fixture
- Original API: `collectors.collect_sitemap_daily(queries=[...], sources=[...], date_from, date_to, limit_per_source)`
- `test_citation_matcher_exact_names_only_supports_explicit_aliases` — matcher test
- `test_process_candidates_accepts_flavio_vale_alias` — ingestion test with monkeypatch

### tests/test_source_recovery_collectors.py (169 lines)
**Extractable:**
- Sitemap daily config with `prefilter_queries: False`, `window_by_sitemap_day: True` options
- `diagnose_url_row` function references (from benchmark/diagnostic tools)
- WordPress URL dedup test data with UTM parameter stripping

### tests/test_run_ingestion_dedup.py (269 lines)
**Extractable:**
- Camara HTML selectors: `h3.catItemTitle`, `strong > a` pattern
- `collect_sitemap_daily` with `prefilter_queries` and `window_by_sitemap_day` config
- Dedup logic test data

### tests/test_wordpress_site_collectors.py (4 lines)
**Extractable:**
- CSS custom properties from original export: `--accent`, `--muted`, `--panel-strong`, `--ai-bg`
- CSS for `h1, h2, h3`, `.hero p`, `.meta-row`, `.stats`, `.story-grid`, `.article-stack`, `.story-articles`

---

## Key Findings: Original vs Reconstructed Architecture

The corrupted files reveal that the original architecture was **significantly richer** than the 2026-03-30 reconstruction:

### 1. Adapter Pattern (Original) vs Direct Functions (Reconstructed)
- Original `collectors.py` used an **adapter pattern**: `InternalSearchTarget` objects had per-site extraction methods
- Tests reference `_adapter(host)` factory, `adapters=[adapter]` parameter
- Reconstructed version uses simpler direct function calls

### 2. Missing Collectors
- `collect_diariodorio_site` — dedicated Diario do Rio collector
- `collect_temporealrj_site` — dedicated Tempo Real RJ collector
- `collect_direct_scrape` — Google search + browser (WIP, was being skipped)

### 3. Missing Pipeline Features
- `story_with_articles` — story/export database query used by original export path
- `process_candidates` — standalone function (tests reference it directly)
- `SourceModule` class — used by benchmark tool
- `FLAVIO_QUERY_VARIANTS` — per-source query variants
- `WORDPRESS_API_SITES` — richer WordPress config (list of dicts with `query_variants`)
- `SITEMAP_DAILY_SOURCES`, `VEJARIO_ARCHIVE_TARGETS`, `CAMARA_ARCHIVE_TARGET` — broader settings surface referenced by recovered tools/tests
- `get_active_targets`, `build_wordpress_queries_for_site`, `FLAVIO_INTERNAL_SEARCH_QUERIES` — settings helpers/constants referenced by recovered tools/tests
- `canonicalize_url` in `pipeline/http_utils.py` — compatibility symbol expected by benchmark/tooling
- `forced_terms`, `forced_terms_mode` — query forcing options
- `budget_seconds` — time budget for ingestion runs
- `progress_callback` — progress reporting during ingestion
- `IngestionResult` dataclass — structured result reporting

### 4. Missing Export Features
- `render_filter_buttons` — target filter UI
- `render_story_index` — story grouping with expandable sections
- `render_article_card` — rich article cards with multi-target labels
- Story cards, AI summaries, and `--ai-bg` styling
- The export was much richer than the simple list in the reconstruction

### 5. Missing Tools
- `tools/globo_family_diagnostic.py` — URL-by-URL diagnostic (referenced in README but not in file listing)
- `diagnose_url_row` function — per-URL fetch/extraction analysis

---

## Recovery Priority Recommendations

### Priority 1 — High Value, Moderate Effort (extract from corrupted)
1. **test_internal_site_search_collectors.py** — HTML selectors for Veja Rio, Camara, CONIB are invaluable
2. **test_flavio_query_expansion.py** — WordPress variant test + 3 render functions for export
3. **test_cbn_source_recovery.py** — original API signatures, CBN test
4. **benchmark_sources_vs_excel.py** — 12 function signatures + some implementation

### Priority 2 — Must Rewrite (no recoverable code)
1. **server.py** — original was 313 lines with REST API + rich HTML export
2. **tools/fix_encoding.py** — completely wrong content
3. **tools/backfill_google.py** and **tools/cbn_search_diagnostic.py** — completely wrong content
4. **tools/generate_flavio_valle_print_pdf.py** — only 2-line fragment
5. **tools/prepare_wix_clipping_snapshot.py** — only fragment

### Priority 3 — Enhance Reconstructed Files
1. **pipeline/collectors.py** — add adapter pattern, per-site extractors, missing collectors
2. **pipeline/ingest.py** — add `process_candidates`, `SourceModule`, progress callbacks, budget
3. **pipeline/settings.py** — add richer configs, RSS feeds, more sitemaps
4. **tools/export_mobile_snapshot.py** — add story cards, filter buttons, AI summaries

---

## Raw Recovery Source (D:\recovery\YOUR_FILES\)

**Total files:** ~190 recovered text/code fragments (978MB)
**Clipping-related .py files found:** 8 files with matches for clipping keywords
**Key files:**
- `recovered_224598MB_63334KB.py` (62MB) — Codex session log with embedded Python code, imports like `from pipeline.collectors import collect_internal_site_search, collect_wordpress_api, collect_google_news`
- `recovered_211143MB_842KB.py` (842KB) — 718 matches for clipping/pipeline/collector terms
- `recovered_210651MB_525KB.py` (525KB) — 342 matches
- `recovered_209790MB_359KB.py` (359KB) — 355 matches

These large files contain **interleaved Codex telemetry + actual code** and are the primary source for further extraction. The 62MB file in particular likely contains most of the original codebase embedded in Codex apply_patch operations.

---

## from_patches Original Files Audit

### Source Directories Comparison

The recovered files exist in 3 locations:
- `D:\recovery\CLIPPING_PROJECT\from_patches\` — primary extraction (26 files, mostly binary-corrupted)
- `D:\recovery\CLIPPING_EXTRACTED\` — secondary extraction (19 files, smaller fragments)
- `D:\recovery\clipping-project\` — current project (33 .py files, mix of reconstructed and corrupted)

**Key finding:** The from_patches files are LARGER but MORE CORRUPTED than the current project files. They contain original code interleaved with binary Codex telemetry (WebSocket traces, OTEL spans). File sizes are hugely inflated (e.g., collectors.py: 67KB from_patches vs 20KB current; database.py: 104KB vs 4KB).

**Strategy:** from_patches files are PRIMARY even though corrupted. The approach is:
1. Take each from_patches file as the base
2. Strip binary/Codex telemetry (lines with `TRACE`, `codex_api`, base64 blobs, `tokio-tungstenite`, etc.)
3. Fix escaped quotes (`\"` → `"`)
4. Fill gaps where corruption destroyed code (using reconstructed version + test fixtures as reference)
5. Result = cleaned original code, not a simplified rewrite with some patterns merged in

### from_patches Pipeline Files (F1-T1)

| File | from_patches lines | Current lines | from_patches corruption | Extractable content |
|------|-------------------|---------------|------------------------|---------------------|
| pipeline/collectors.py | 696 (67KB) | 521 | Heavy — 58 Codex telemetry lines, 15 base64 blobs. ~350 clean Python lines. | 15 functions: `collect_extra_site`, `collect_wordpress_site`, `collect_odia_site`, `collect_r7_site`, `_parse_sitemap_index_entries`, `_parse_unix_timestamp`, `_day_key_from_iso`, `_r7_day_from_sitemap_url`, `_clean_html_fragment`, `_host_matches`, `_parse_pt_br_datetime`, `summarize_rows`, `write_reports`, `main`, `append_sitemap_entries`. Key regexes: `VEJARIO_DATE_RE`, `CAMARA_RESULT_RE`, `CONIB_ARTICLE_RE`, `CONIB_NEXT_RE`, `CAMARA_NEXT_RE`. References `EXTRA_SITE_SOURCE`, `ODIA_SITE_SOURCE`, `R7_SITE_SOURCE`, `DIARIO_DO_RIO_SITE_SOURCE`, `TEMPO_REAL_RJ_SITE_SOURCE`. |
| pipeline/database.py | 361 (104KB!) | 114 | Very heavy — only 79 clean lines of 1 method survive. Lines 80-361 are pure Codex telemetry. | Only `list_articles_for_export` method with complex SELECT: `has_ai_summary`, `GROUP_CONCAT`, multi-target JOIN. Class definition, __init__, connect, insert_article, insert_mention, upsert_story ALL LOST. Schema recoverable from SQL. |
| pipeline/http_utils.py | 77 (8KB) | 76 | Mixed — **MISNAMED FILE.** Contains text extraction functions, NOT HTTP utils. Lines 1-59 recoverable, 60-77 are duplicates+binary. | 4 functions: `_clean_embedded_text`, `_json_string_to_text`, `_collect_text_values`, `extract_embedded_article_text`. 3 regexes: `SCRIPT_BLOCK_RE`, `LDJSON_BLOCK_RE`, `JSON_TEXT_VALUE_RE`. These belong in a text extraction module, not http_utils. |
| pipeline/ingest.py | 426 (29KB) | 202 | Mixed — cross-file contamination. Lines 1-30 + 69-170 are unique ingest logic. Lines 31-68 are HTML template from report module. Lines 196-425 are DUPLICATED collector functions. | Unique: `select_targets`, `scope_labels`, `output_path_for_args`, `build_html`. `IngestionResult` referenced with `stories_touched`. Candidate processing with `force_full_fetch`, `exact_body_only`, `require_published_extraction`. Contamination: report HTML templates + collector duplicates mixed in. |
| pipeline/matcher.py | 116 (7KB) | 61 | Mixed — **MISNAMED FILE.** Contains HTML report rendering, NOT matcher logic. Lines 7-90 recoverable. Line 91+ pure binary. | 2 functions: `render_article_card(article, *, target_labels, show_story_link)`, `build_html(date_from, date_to, filtered_stories, ...)`. References `SENTIMENT_LABEL`, `host_from_url`, `render_text_block`, `target_badges`, `fmt_dt`. Lines 1-6 have exact_aliases fragment from actual matcher. |
| pipeline/settings.py | 34 (3KB) | 73 | Heavy — only ~20 clean lines. | Partial site source dicts: `EXTRA_SITE_SOURCE`, `ODIA_SITE_SOURCE`, `R7_SITE_SOURCE` with `benchmark_day_limit` values. Must rewrite — values recoverable from collectors.py references. |

### CRITICAL: Cross-File Contamination in from_patches

The Codex patch extraction process mixed content from different modules into wrong files:

| from_patches filename | Actual content | Real module |
|----------------------|----------------|-------------|
| `pipeline/matcher.py` | `render_article_card`, `build_html` (HTML report rendering) | Should be in report/export module |
| `pipeline/http_utils.py` | `extract_embedded_article_text`, text cleaning functions | Should be in a text extraction module |
| `pipeline/ingest.py` lines 31-68 | HTML story template with `__SID__`, `__TITLE__` placeholders | Should be in report/export module |
| `pipeline/ingest.py` lines 196-425 | `collect_r7_site`, `collect_odia_site`, sitemap parsing | Should be in collectors.py |

**Implication:** When cleaning from_patches files, code must be sorted into the CORRECT module, not just cleaned in place.

### from_patches Tools Files (F1-T2)

| File | from_patches lines | Current lines | Best source | Notes |
|------|-------------------|---------------|-------------|-------|
| tools/export_mobile_snapshot.py | 117 (MISLABELED — actually prepare_wix content) | 148 (clean, valid Python) | **Current** | from_patches contains `build_snapshot_artifact`, `validate_snapshot_html`, `prepare_snapshot` — really from prepare_wix_clipping_snapshot.py |
| tools/benchmark_sources_vs_excel.py | 49 (stub, 2 functions) | 708 (corrupted, 12 function defs) | **Current** | Functions: `resolve_candidate_limit`, `wordpress_site_runner` (from_patches); `main`, `prepare_snapshot`, `expand_excel_days`, `extract_embedded_article_text` etc. (current) |
| tools/benchmark_auto_vs_excel.py | 2 (stub) | 0 (stub) | **NONE** | Both are single regex line — completely lost |
| tools/prepare_wix_clipping_snapshot.py | 10 (stub, has `capture()` + playwright import) | 2 (stub) | **from_patches** | `from playwright.sync_api import sync_playwright`, `capture()` function |
| tools/backfill_google.py | N/A | 228 (WRONG FILE — grep output) | **LOST** | Must rewrite or recover from disk image |
| tools/cbn_search_diagnostic.py | N/A | 228 (WRONG FILE — grep output) | **LOST** | Must rewrite or recover from disk image |
| tools/fix_encoding.py | N/A | 1 (WRONG FILE — JSON job log) | **LOST** | Must rewrite or recover from disk image |
| tools/generate_flavio_valle_print_pdf.py | N/A | 58 (WRONG FILE — CLAUDE.md) | **LOST** | Must rewrite or recover from disk image |
| server.py | 313 (code fragments + binary from line 37) | 313 (same content) | **from_patches** | Has target parsing, collector routing, HTML template + JS filters. Needs heavy reconstruction. |
| run_ingestion.py | 15 (stub — argparse choices only) | 60 (clean, valid Python) | **Current** | from_patches only has collector choices list |
| app.js | 23 (11 lines JS + binary) | 4300 bytes (same, binary-corrupted) | **from_patches** | First 11 lines have collector state/UI code |

### Completely Lost Tools (no recoverable version exists)

| Tool | What it did | Recovery options |
|------|------------|------------------|
| `tools/backfill_google.py` | Google News backfill | Search disk image, or rewrite from architecture knowledge |
| `tools/cbn_search_diagnostic.py` | CBN diagnostic | Search disk image, or rewrite |
| `tools/fix_encoding.py` | Encoding fixes | Search disk image, or rewrite |
| `tools/generate_flavio_valle_print_pdf.py` | PDF generation (~8.2KB original) | Search disk image |
| `tools/benchmark_auto_vs_excel.py` | Auto benchmark | Search disk image |

### from_patches Test Files (F1-T3)

| File | from_patches lines | Current lines | Key extractable content |
|------|-------------------|---------------|------------------------|
| test_flavio_query_expansion.py | 166 | 361 | WordPress variant tests, 3 render functions (render_filter_buttons, render_story_index, render_article_card) |
| test_source_recovery_collectors.py | 169 | 169 | WordPress dedup tests, `diagnose_url_row` references |
| test_benchmark_sources_vs_excel.py | 81 | 1 | `SourceModule`, `IngestionResult`, `process_candidates` test |
| test_http_utils.py | 46 | 84 | Both corrupted — different junk content |
| test_cbn_source_recovery.py | 16 | 114 | Current has more — CBN sitemap test, matcher alias test |
| test_internal_site_search_ingest.py | 15 | 1 | from_patches has monkeypatch references to `collect_diariodorio_site`, `collect_temporealrj_site` |
| test_internal_site_search_collectors.py | 1 | 72 | Current has HTML selectors for Veja Rio, Camara (`dl.search-results`), CONIB (`article.uk-article`) |
| test_wordpress_site_collectors.py | 4 | 4 | CSS custom properties from export template |
| test_direct_scrape_windows.py | 2 | 2 | References to `collect_diariodorio_site`, `collect_temporealrj_site` |
| test_globo_family_diagnostic.py | 1 | 2 | Codex log message (not useful) |
| tests/unit/test_wix_clipping_iframe.py | 4 | N/A | Binary-corrupted, not recoverable |

### Non-.py Files Comparison (F1-T4)

| File | from_patches | CLIPPING_EXTRACTED | Current | Best | Notes |
|------|-------------|-------------------|---------|------|-------|
| data/targets.json | 78B fragment | 72B fragment | 421B, 1 target | Current | Original had **28 targets**, all versions incomplete |
| README.md | 2532B corrupted | 1491B clean | 1491B clean | Current = EXTRACTED | Both clean copies are identical |
| app.js | 4300B corrupted | N/A | 4300B corrupted | Neither | JS ops dashboard, binary-corrupted |
| MISSING_NEWS_ANALYSIS.md | N/A | 790B clean | 790B clean | Current = EXTRACTED | Identical |
| FUTURE_IDEAS.md | N/A | 85B garbage | Clean | Current | EXTRACTED version has Windows volume serial |
| EXPORT_HTML_OFFLINE.md | N/A | N/A | Clean | Current | Only copy |
| RECOVERY_NOTES.md | N/A | N/A | Clean | Current | Only copy |

### Files in from_patches but NOT in current project

| File | Status |
|------|--------|
| `tests/unit/test_wix_clipping_iframe.py` | Binary-corrupted, not recoverable |

### Missing Original Functions (Cross-Reference Gap List)

Functions found in corrupted originals and still missing from current reconstructed code:

| Function/Class | Found in | Purpose | Priority |
|----------------|----------|---------|----------|
| `IngestionResult` (dataclass) | ingest.py, benchmark | Structured result with `stories_touched`, `errors` | HIGH |
| `process_candidates` | ingest.py, tests | Standalone candidate processing function | HIGH |
| `create_or_update_story` | server.py, ingest.py | Story grouping logic | HIGH |
| `select_targets` | ingest.py | Target selection with validation | MEDIUM |
| `ordered_unique` | ingest.py | Dedup utility preserving order | MEDIUM |
| `FLAVIO_QUERY_VARIANTS` | benchmark, ingest | Per-source query expansion | MEDIUM |
| `render_filter_buttons` | test_flavio_query_expansion | HTML filter button generation | HIGH |
| `render_story_index` | test_flavio_query_expansion | Story navigation HTML | HIGH |
| `render_article_card` | test_flavio_query_expansion | Rich article card HTML | HIGH |
| `prepare_snapshot` | benchmark | Static HTML snapshot generator | HIGH |
| `extract_embedded_article_text` | benchmark | Article text extraction from HTML | MEDIUM |
| `_clean_embedded_text` | benchmark | Text cleaning utility | LOW |
| `_json_string_to_text` | benchmark | JSON to text conversion | LOW |
| `_collect_text_values` | benchmark | Value extraction utility | LOW |
| `source_uses_sitemap_fast_path` | benchmark | CBN sitemap optimization | LOW |
| `normalize_url` | normalization (exists) | URL normalization | EXISTS |
| `host_of` | benchmark | Host extraction from URL | MEDIUM |
| `SourceModule` (class) | benchmark | Per-source module abstraction | MEDIUM |
| `collect_diariodorio_site` | tests | Dedicated Diario do Rio collector | MEDIUM |
| `collect_temporealrj_site` | tests | Dedicated Tempo Real RJ collector | LOW |
| `diagnose_url_row` | test_source_recovery | Per-URL diagnostic function | LOW |
| `_adapter(host)` | tests | Per-site adapter factory pattern | MEDIUM |
| `html_to_article_text` | test_http_utils | Extract LD+JSON articleBody from HTML | MEDIUM |
| `fetch_full_article_text` | test_cbn_source_recovery | `(url, request_timeout=10)` -> `(url, title, published_at)` | MEDIUM |
| `classify_failure_bucket` | test_source_recovery | Diagnostic function from globo_family_diagnostic | LOW |
| `get_flavio_matcher` | test_source_recovery | Convenience factory for matcher | LOW |
| `resolve_candidate_limit` | test_benchmark | Candidate limit configuration | LOW |
| `build_source_modules` | test_benchmark | Build SourceModule list from config | LOW |

### API Signature Mismatches (Reconstructed vs Original)

Functions that EXIST but have WRONG signatures:

| Function | Current signature | Original signature (from tests) | Impact |
|----------|------------------|--------------------------------|--------|
| `run_ingestion` | `(options)` | `(source_type, options=)` | HIGH — different call pattern |
| `collect_sitemap_daily` | `(configs, date_from, date_to, query, timeout)` | `(queries=, sources=, date_from=, date_to=, limit_per_source=, request_timeout=)` | HIGH — completely different params |
| `collect_internal_site_search` | `(targets, query, ...)` | `(queries=, adapters=, ...)` | HIGH — adapter pattern vs direct |
| `collect_wordpress_api` | `(hosts, query, ...)` | `(query, *, source_name, base_url)` per site | HIGH — batch vs per-site |
| `IngestionOptions` fields | `collector, target_keys, custom_query, date_from, date_to, db_path, request_timeout, skip_direct_scrape` | `target_keys, custom_query, date_from, date_to, max_candidates_per_source, max_process_seconds, request_timeout_seconds` | MEDIUM — different field names and purposes |

---

## Wave 2.5 Provenance Audit (Reopened Tasks)

This section records the current evidence status for the reopened Wave 2.5 tasks.
Labels used here are strict:

- `recovered verbatim`
- `recovered and cleaned`
- `reconstructed from evidence`
- `not yet recovered`

### F2-T5b — `pipeline/database.py`

| Field | Value |
|------|-------|
| Task status | `open` |
| Best current label | `not yet recovered` for the full file |
| Strongest recovered evidence | Re-running [`reconstruct_db.py`](D:/recovery/reconstruct_db.py) against the 63MB recovery bundle yields a clean-ish 220-line base extraction through `list_story_context`, while [`block_swa_la.txt`](D:/recovery/block_swa_la.txt) and [`block_bf.txt`](D:/recovery/block_bf.txt) preserve the later `story_with_articles()` cluster |
| Stitch evidence | [`extract_db8.py`](D:/recovery/extract_db8.py), [`extract_db9.py`](D:/recovery/extract_db9.py), and [`stitch_db.py`](D:/recovery/stitch_db.py) all explicitly describe reconstructing the full file by stitching multiple log windows |
| Corrupted artifact evidence | [`database.py`](D:/recovery/CLIPPING_PROJECT/from_patches/pipeline/database.py) begins mid-method inside `list_articles_for_export`, so it is not a clean original file |
| Current workspace gap | Current [`database.py`](D:/recovery/clipping-project/pipeline/database.py) lacks `story_with_articles()`, `list_articles()`, `list_articles_by_ids()`, and the richer story/query surface expected by the recovered export path |
| Interpretation | The second extraction pass materially improves the base-file evidence: the file head through `list_story_context` now looks `recovered and cleaned`, and `list_articles_for_export()` has a much cleaner patch fragment than before. Even so, the full class tail is still not recoverable as a faithful stitched original without unresolved gaps. |
| Next action | Keep `F2-T5b` open. Defer any non-original compatibility/scaffold changes and only move on to `F2-T1b`/`F2-T2b` after documenting that `database.py` remains blocked by missing source. |

#### F2-T5b evidence matrix

| Surface | Best source(s) | Confidence label | Current evidence | Notes |
|---------|----------------|------------------|------------------|-------|
| Base/schema/connect section through `list_story_context()` | [`reconstruct_db.py`](D:/recovery/reconstruct_db.py) extraction window `7121728` | `recovered and cleaned` | Re-running the extractor yields a clean-ish 220-line base with `SCHEMA_SQL`, `utc_now_iso()`, `ClippingDB.__init__`, `connect()`, `_init_schema()`, `insert_article_if_new()`, `insert_mentions()`, `list_recent_stories()`, and `list_story_context()` before contamination resumes | Stronger than the older [`database_base.py`](D:/recovery/database_base.py) artifact, which is itself contaminated mid-method |
| `story_with_articles()` | [`swa_block.txt`](D:/recovery/swa_block.txt), [`block_swa_la.txt`](D:/recovery/block_swa_la.txt) | `recovered and cleaned` | Full method body is present across overlapping fragments with matching SQL and payload structure | Depends on the unrecovered surrounding class body still being recovered |
| `list_articles()` | [`block_swa_la.txt`](D:/recovery/block_swa_la.txt), [`block_big.txt`](D:/recovery/block_big.txt) | `not yet recovered` | Query head, selected fields, and some output keys are visible, but a clean standalone body has not been isolated from contaminated windows | Proven nearby, but still not faithful enough to merge as original source |
| `list_articles_for_export()` | [`patch_0.txt`](D:/recovery/patch_0.txt), [`database.py`](D:/recovery/CLIPPING_PROJECT/from_patches/pipeline/database.py) | `recovered and cleaned` fragment | The clean patch fragment preserves the method head, the full filtering logic, most SQL fields, and most payload mapping before contamination hits the tail of `has_ai_summary` / `summary_source` | Stronger proof of the original export shape, but still not enough to certify the full file |
| `list_articles_by_ids()` | [`recovered_224598MB_63334KB.py`](D:/recovery/YOUR_FILES/recovered_224598MB_63334KB.py) | `not yet recovered` | The large recovered bundle shows the method name and some field lines, but that file is contaminated with agent commentary, tool-call payloads, and unrelated patch text | Still blocked on a clean direct extraction of the method body |

#### F2-T5b contamination boundaries confirmed in pass 2

- [`recovered_224598MB_63334KB.py`](D:/recovery/YOUR_FILES/recovered_224598MB_63334KB.py) is not a clean source file. It contains prior agent commentary, `apply_patch` payloads, SSE traces, and unrelated document text, so it cannot be treated as direct original-code proof by itself.
- [`database_base.py`](D:/recovery/database_base.py) remains useful as a hint artifact, but it contaminates mid-method and is weaker than the live extraction path inside [`reconstruct_db.py`](D:/recovery/reconstruct_db.py).
- [`patch_0.txt`](D:/recovery/patch_0.txt) is cleaner than the older `from_patches` database fragment and is now the best artifact for `list_articles_for_export()`.

#### F2-T5b proven query/result shape

The following are supported by recovered code rather than only by downstream inference:

- `story_with_articles()` returns a list of story dicts ordered by `temperature DESC, updated_at DESC`
- Each story payload includes `id`, `title`, `summary`, `targets`, `temperature`, `createdAt`, `updatedAt`, `flagged`, `notes`, and `articles`
- Each nested article payload includes `id`, `title`, `url`, `source`, `publishedAt`, `sentiment`, `summary`, `snippet`, `hasAiSummary`, and `summarySource`
- Recovered article/export queries compute AI-summary state from `mentions.sentiment_reason = 'anthropic_batch'`
- Recovered export/article query surfaces include `article_id`, `url`, `title`, `source_name`, `source_type`, `published_at`, `snippet`, `full_text`, `summary`, `has_ai_summary`, `target_keys`, `target_names`, `keywords`, and `story_id`

#### F2-T5b go/no-go decision

| Decision | Value |
|----------|-------|
| Code integration result | `NO-GO` |
| Date | `2026-03-30` |
| Runtime code edited? | `No` |
| Why no merge? | The base section through `list_story_context()` is now much stronger, and `story_with_articles()` plus `list_articles_for_export()` have usable fragments, but `list_articles()`, `list_articles_by_ids()`, and the surrounding tail of the class still lack a clean faithful recovery. Replacing [`database.py`](D:/recovery/clipping-project/pipeline/database.py) now would still require invention around unrecovered methods. |
| Task outcome | `F2-T5b remains open` |
| Honest baseline | Current [`database.py`](D:/recovery/clipping-project/pipeline/database.py) remains the workspace baseline until a cleaner stitched original can be proven |
| Deferred note | Future compatibility/scaffold changes may still be needed later, but they are explicitly deferred and are not part of `F2-T5b` |
| Next extraction target | If we revisit `database.py`, the remaining high-value target is a clean direct extraction of `list_articles_by_ids()` and the tail of `list_articles()`; otherwise the original plan can now advance to `F2-T1b` and `F2-T2b` with `F2-T5b` explicitly blocked |

### F2-T1b — `pipeline/settings.py`

| Field | Value |
|------|-------|
| Task status | `open` |
| Best current label | `reconstructed from evidence` |
| Strongest recovered evidence | [`settings_FINAL.py`](D:/recovery/settings_FINAL.py) (359 lines) contains `WORDPRESS_API_SITES`, `SITEMAP_DAILY_SOURCES`, `VEJARIO_ARCHIVE_TARGETS`, `CAMARA_ARCHIVE_TARGET`, `FLAVIO_INTERNAL_SEARCH_QUERIES`, `build_wordpress_queries_for_site()`, and `get_active_targets()` |
| Stitch evidence | [`extract_settings_final.py`](D:/recovery/extract_settings_final.py) explicitly states the file was assembled from two log offsets (`58530383` and `3338291`) and manually inserted `build_wordpress_queries_for_site()` plus `exact_aliases` |
| Corrupted artifact evidence | [`settings.py`](D:/recovery/CLIPPING_PROJECT/from_patches/pipeline/settings.py) and [`settings.py`](D:/recovery/CLIPPING_EXTRACTED/patches/pipeline/settings.py) are fragmentary/cross-contaminated and cannot be treated as clean originals |
| Current workspace gap | Current [`settings.py`](D:/recovery/clipping-project/pipeline/settings.py) lacks `WORDPRESS_API_SITES`, `SITEMAP_DAILY_SOURCES`, `VEJARIO_ARCHIVE_TARGETS`, `CAMARA_ARCHIVE_TARGET`, `FLAVIO_INTERNAL_SEARCH_QUERIES`, `get_active_targets()`, and `build_wordpress_queries_for_site()` |
| Interpretation | The missing settings surface is real and well-evidenced, but the best current candidate is a stitched recovery, not a verbatim original module. |
| Next action | Keep `F2-T1b` open. Use `settings_FINAL.py` as evidence for symbols and structure, not as proof of verbatim recovery. |

### F2-T2b — `pipeline/http_utils.py`

| Field | Value |
|------|-------|
| Task status | `open` |
| Best current label | `recovered and cleaned` candidate, but not yet accepted as the original file |
| Strongest recovered evidence | [`http_utils_FINAL.py`](D:/recovery/http_utils_FINAL.py) (289 lines) is a self-contained candidate with `fetch_url()`, `post_json()`, `try_resolve_google_redirect()`, `canonicalize_url()`, `html_to_article_text()`, and related helpers |
| Contamination evidence | [`http_utils.py`](D:/recovery/CLIPPING_PROJECT/from_patches/pipeline/http_utils.py) is not a clean HTTP module; it contains embedded-text extraction code and Codex/log contamination |
| Cross-file contamination evidence | [`database_base.py`](D:/recovery/database_base.py) and [`database_raw_extract.py`](D:/recovery/database_raw_extract.py) also contain `canonicalize_url()` and HTTP/text helper code, showing that some recovered log windows mixed multiple modules together |
| Current workspace gap | Current [`http_utils.py`](D:/recovery/clipping-project/pipeline/http_utils.py) lacks `canonicalize_url()` and the richer helper surface present in the recovered candidate (`html_to_article_text()`, `extract_html_title()`, `extract_published_at()`) |
| Interpretation | There is a plausible recovered `http_utils` candidate, but file-level provenance is still weaker than a clean single-source recovery. We should not mark `F2-T2b` complete until that provenance is tightened. |
| Next action | Keep `F2-T2b` open. Treat `http_utils_FINAL.py` as the best current candidate for future comparison, not as final proof. |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-03-30 | Initial forensic inventory — 32 .py files + 9 non-py files classified |
| 2026-03-30 | Added from_patches audit: pipeline, tools, tests, non-py files, cross-reference gap list (F1-T1..F1-T4) |
| 2026-03-30 | Correction: prior Codex Batch B2 claims for `pipeline/database.py`, `pipeline/settings.py`, and `pipeline/http_utils.py` were withdrawn. Those changes were evidence-based reconstructions, not verified original recoveries, so F2-T5b/F2-T1b/F2-T2b remain open. |
| 2026-03-30 | Added Wave 2.5 provenance audit for F2-T5b/F2-T1b/F2-T2b: database remains partial-block recovery only; settings is a stitched reconstruction candidate; http_utils has a strong candidate but still needs provenance tightening. |
| 2026-03-30 | Completed the deeper artifact-first evidence pass for F2-T5b. Result: `NO-GO` for runtime merge; `story_with_articles()` is recoverable as a fragment, but the surrounding `database.py` base and neighboring query bodies still lack a clean file-level recovery. No runtime code changes were made. |
| 2026-03-30 | F2-T5b extraction pass 2 tightened the decision artifact: the base section through `list_story_context()` is now `recovered and cleaned`, `list_articles_for_export()` has a cleaner patch fragment, the large recovered `.py` bundle was explicitly classified as contaminated, and the final result remains `NO-GO` for runtime merge. |
