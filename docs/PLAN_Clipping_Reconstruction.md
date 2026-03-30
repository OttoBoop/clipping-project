# Clipping Project Reconstruction - Implementation Plan

**Generated:** 2026-03-30
**Status:** Draft
**Discovery:** [DISCOVERY_Clipping_Reconstruction_Debug.md](DISCOVERY_Clipping_Reconstruction_Debug.md)
**Forensic Inventory:** [FORENSIC_INVENTORY.md](FORENSIC_INVENTORY.md)

---

## 1. Executive Summary

Reconstruct the Clipping Project — a Brazilian news monitoring pipeline for Vereador Flavio Valle — from SSD recovery artifacts. The previous reconstruction session produced simplified rewrites that ignored the original architecture. This plan takes a forensic-first approach: audit every recovered file, extract original code from corrupted fragments, clean and restore each module, and validate against the known-good old HTML snapshot (703 stories, 12+ sources).

---

## 2. Requirements Summary

### 2.1 Problem Statement
The original Clipping Project was lost when Linux was installed over a Windows NTFS partition. Recovery extracted files from Codex session logs, but those files are corrupted (escaped quotes, binary fragments, mixed content). A hasty reconstruction produced simplified rewrites missing half the original code (database.py: 114 vs 361 lines, ingest.py: 202 vs 426 lines). The reconstructed pipeline returns poor results (0 articles from Globo, junk from Camara) and generates a flat HTML list instead of the original's 703 grouped stories with AI summaries and offline filters.

### 2.2 Target Users
Primary user: Otavio (political advisor to Vereador Flavio Valle, EPGE/FGV). Uses the tool daily to monitor news mentions across 12+ Brazilian media sources. Technical enough to run Python scripts and review HTML output.

### 2.3 Success Criteria
- [ ] All 7+ collectors return real articles from their respective sources
- [ ] Pipeline ingests, deduplicates, matches keywords, and stores in SQLite correctly
- [ ] Rich HTML export generates story-grouped report with offline filters (matching old snapshot structure)
- [ ] Targeted validation: pipeline finds known articles from old HTML snapshot for each source
- [ ] Full E2E run produces non-trivial output (50+ articles from 5+ sources)

### 2.4 Explicitly Out of Scope
- `collect_direct_scrape` — was WIP pre-loss, skip for now
- AI summary generation (requires Anthropic API key setup — defer to after pipeline works)
- Wix embedding/deployment — focus on local pipeline and static HTML first
- Adding new sources beyond what the original had

### 2.5 Evidence of Readiness
- [ ] Each collector tested against a known article URL from old HTML snapshot
- [ ] Full pipeline run produces `data/clipping.db` with articles + mentions + story_articles
- [ ] Generated HTML report has story cards, filter buttons, article counts matching expectations
- [ ] All cleaned files pass Python syntax check (`python -c "import py_compile; py_compile.compile('file.py')"`)

---

## 3. Technical Architecture

### 3.1 System Overview
```
                          ┌──────────────────┐
                          │  run_ingestion.py │  CLI entry point
                          └────────┬─────────┘
                                   │
                          ┌────────▼─────────┐
                          │  pipeline/ingest  │  Orchestrator
                          │  - load_targets   │  - IngestionResult
                          │  - select_targets │  - process_candidates
                          │  - run_ingestion  │  - create_or_update_story
                          └────────┬─────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
     ┌────────▼───────┐  ┌───────▼────────┐  ┌────────▼───────┐
     │   collectors    │  │    matcher      │  │   database      │
     │  - google_news  │  │  - CitationMatch│  │  - ClippingDB   │
     │  - rss          │  │  - Target       │  │  - articles     │
     │  - wordpress    │  │  - MatchHit     │  │  - mentions     │
     │  - globo_api    │  │  - find_hits    │  │  - story_articles│
     │  - html_search  │  └────────────────┘  └─────────────────┘
     │  - sitemap      │
     │  - camara       │           ┌──────────────────┐
     │  - vejario      │           │  server.py        │  Static HTML generator
     │  - diariodorio  │           │  - prepare_snapshot│
     │  - temporealrj  │           │  - story template  │
     └────────────────┘           │  - offline JS      │
              │                    └──────────────────┘
     ┌────────▼───────┐
     │  http_utils     │
     │  - fetch_url    │
     │  - post_json    │
     └────────────────┘
```

### 3.2 Data Flow
1. **Collect:** Each collector fetches candidates from a news source → `CandidateArticle` list
2. **Deduplicate:** `normalize_url` + `host_of` remove duplicates
3. **Match:** `CitationMatcher.find_hits` checks each candidate against target keywords
4. **Process:** `process_candidates` fetches full text, applies matching, stores results
5. **Store:** `ClippingDB` inserts articles, mentions, and story_articles
6. **Export:** `server.py`/`prepare_snapshot` reads DB, groups into stories, generates self-contained HTML with offline JS filters

### 3.3 Technology Decisions
| Component | Technology | Rationale |
|-----------|------------|-----------|
| HTTP | `requests` library | Original used it; handles Globo's TLS correctly (urllib gets connection resets) |
| RSS | `feedparser` | Standard RSS parser, was in original |
| Database | SQLite | Portable, no setup, was in original |
| HTML export | Self-contained HTML + JS | Offline-capable, sharable via mobile, was in original |
| Testing | `pytest` | Was used in original tests |

### 3.4 Integration Points
| External System | How Connected | Notes |
|----------------|---------------|-------|
| Google News RSS | `feedparser` via RSS URL | No API key needed |
| Globo busca API | JSON API at `busca.globo.com/v1/search` | No auth, rate-limited |
| WordPress REST API | `/wp-json/wp/v2/posts` | Per-site with `query_variants` |
| Camara do Rio | HTML scraping `camara.rio.rj.gov.br` | `dl.search-results` selectors |
| Veja Rio | HTML scraping `vejario.abril.com.br` | `div.card .title` selectors |
| CONIB | HTML scraping `conib.org.br` | `article.uk-article` selectors |
| O Dia, R7 | HTML scraping via search pages | Site-specific selectors |
| CBN | XML sitemaps (daily URLs) | `/sitemap/cbn/YYYY/MM/DD_1.xml` |

### 3.5 Output and Failure Contracts
| Artifact | Owner | Proof Required | Blocked If |
|----------|-------|----------------|------------|
| Cleaned .py files | Wave 2-3 | `python -c "py_compile.compile('file.py')"` passes | Syntax errors remain |
| `data/clipping.db` | Wave 5 | Has rows in articles, mentions, story_articles tables | Pipeline crashes or returns 0 articles |
| Rich HTML report | Wave 5 | Contains `story-card` elements, filter buttons, >50 articles | Template rendering fails or missing story logic |
| Per-collector test | Wave 5 | Known article from old HTML found by collector | Collector returns 0 or wrong results |

---

## 4. Feature Breakdown

### Feature 1: Forensic Audit of from_patches Originals

**User Story:** As a developer, I want a complete per-file analysis of every recovered original so I know exactly what's recoverable and what needs rebuilding.

**Acceptance Criteria:**
- [ ] Every file in `CLIPPING_PROJECT/from_patches/` has been read and classified
- [ ] Every file in `CLIPPING_EXTRACTED/` has been checked for cleaner versions
- [ ] Per-file decision documented: use as-is / clean up / needs disk image / must rewrite
- [ ] All function names, classes, imports extracted from corrupted files
- [ ] Comparison table: from_patches lines vs current project lines vs extracted functions

**Tasks:**

| ID | Task | Dependencies | Effort | live_test | Proof Required | Blocked If | Status |
|----|------|-------------|--------|-----------|----------------|------------|--------|
| F1-T1 | Audit pipeline/ files (collectors, database, http_utils, ingest, matcher, settings) — read from_patches versions, classify corruption level, list all extractable functions | None | L | No | Audit table in FORENSIC_INVENTORY.md with per-file classification | Any file unread | ✅ |
| F1-T2 | Audit tools/ files (export, benchmark, prepare_wix, backfill, cbn_diagnostic, fix_encoding, pdf_generator) | None | M | No | Audit table for all tools | Any file unread | ✅ |
| F1-T3 | Audit test files (all 14 test files across from_patches + current project) | None | M | No | Audit table for all tests with extractable selectors/fixtures noted | Any file unread | ✅ |
| F1-T4 | Audit non-py files (targets.json, README, app.js, server.py) + check CLIPPING_EXTRACTED for cleaner versions | None | S | No | Comparison table: from_patches vs CLIPPING_EXTRACTED vs current | Any file unchecked | ✅ |
| F1-T5 | Cross-reference: extract ALL function/class names from ALL corrupted files, compare against current project, produce gap list | F1-T1, F1-T2, F1-T3 | M | No | Gap list: functions in originals but missing from project | Gap list incomplete | ✅ |
| MC-1 | Audit complete — user reviews gap list and per-file decisions | F1-T1..F1-T5 | — | No | User approves audit | User rejects or requests changes | ✅ |

**Tests Required (write BEFORE implementation):**

| What to Verify | Type | Human Needed? | Done When | Proof Artifact |
|----------------|------|---------------|-----------|----------------|
| Every from_patches file has been read | Manual checklist | Yes | All files appear in audit table | Updated FORENSIC_INVENTORY.md |
| Gap list is complete | Cross-reference | Yes — review gaps | No function in originals is missing from gap list | Gap list section in inventory |

---

### Feature 2: Clean and Restore Pipeline Core

**User Story:** As a developer, I want clean, working Python files for all pipeline modules, restored from the original code rather than rewritten from scratch.

**Acceptance Criteria:**
- [ ] All 7 pipeline/*.py files pass syntax check
- [ ] All original functions/classes from from_patches are present
- [ ] Escaped quotes (`\"`) cleaned to normal quotes
- [ ] Binary/Codex fragments removed
- [ ] Missing modules (normalization.py, __init__.py) created if not in originals
- [ ] `run_ingestion.py` CLI works

**Tasks:**

| ID | Task | Dependencies | Effort | live_test | Proof Required | Blocked If | Status |
|----|------|-------------|--------|-----------|----------------|------------|--------|
| F2-T1 | Clean pipeline/settings.py — un-escape quotes, restore full config from from_patches (34 lines), add missing sources from current (73 lines) | MC-1 | S | No | `py_compile` passes, all InternalSearchTarget entries present | Syntax errors | ✅ [pending-verification] |
| F2-T2 | Clean pipeline/http_utils.py — merge from_patches (77 lines) with current requests-based version (76 lines) | MC-1 | S | No | `py_compile` passes, `fetch_url`+`post_json`+`try_resolve_google_redirect` present | Syntax errors | ✅ [pending-verification] |
| F2-T3 | Create pipeline/normalization.py — check if in from_patches, otherwise keep current (56 lines) | MC-1 | S | No | `py_compile` passes, `normalize_url`+`canonicalize_url`+`clean_title` present | Missing functions | ✅ [pending-verification] |
| F2-T4 | Clean pipeline/matcher.py — restore from from_patches (116 lines vs current 61) | MC-1 | S | No | `py_compile` passes, `Target`+`MatchHit`+`CitationMatcher` present with all original fields | Missing fields | ✅ [pending-verification] |
| F2-T5 | Clean pipeline/database.py — restore from from_patches (361 lines vs current 114), preserve all original queries including `has_ai_summary`, `COALESCE`, multi-target support | MC-1 | L | No | `py_compile` passes, all original methods present, `story_articles` + `articles` + `mentions` tables with all original columns | Missing methods or columns | ✅ [pending-verification] |
| F2-T6 | Clean pipeline/collectors.py — restore from from_patches (696 lines vs current 521), add adapter pattern, restore per-site selectors from test fixtures (Camara `dl.search-results`, Veja Rio `div.card .title`, CONIB `article.uk-article`) | MC-1, F2-T1, F2-T2 | XL | No | `py_compile` passes, all collectors present including missing ones (`collect_diariodorio_site`, `collect_temporealrj_site`), adapter pattern used | Any collector function missing | ⬜ |
| F2-T7 | Clean pipeline/ingest.py — restore from from_patches (426 lines vs current 202), add `IngestionResult`, `process_candidates`, `create_or_update_story`, `select_targets`, `ordered_unique`, `FLAVIO_QUERY_VARIANTS`, progress_callback | MC-1, F2-T4, F2-T5, F2-T6 | L | No | `py_compile` passes, all functions present, `IngestionResult` dataclass has `stories_touched` | Any architecture piece missing | ⬜ |
| F2-T8 | Clean run_ingestion.py — restore CLI from from_patches (15 lines) + current (60 lines), merge best of both | MC-1, F2-T7 | S | No | `py_compile` passes, CLI runs with `--help` | CLI broken | ⬜ |

**Wave 2.5: Restore Pipeline Core from 63MB Codex Session Log**

The F2-T1..T8 tasks above produced simplified rewrites, not true restorations.
A complete clean copy of the original export_mobile_snapshot.py (1247 lines, 30 functions)
was recovered from an `apply_patch` block in `D:\recovery\YOUR_FILES\recovered_224598MB_63334KB.py`.
The same source likely contains original versions of all pipeline modules.
Wave 2.5 extracts and restores those originals.

| ID | Task | Dependencies | Effort | live_test | Proof Required | Blocked If | Status |
|----|------|-------------|--------|-----------|----------------|------------|--------|
| F2-T5b | Restore original database.py from 63MB Codex log — recover `story_with_articles()`, full query set, original 361-line version | F2-T5 | L | No | `py_compile` passes, `story_with_articles` method exists, line count ≥300 | Original not found in Codex log | ⬜ |
| F2-T1b | Restore original settings.py from 63MB Codex log — recover `WORDPRESS_API_SITES`, `SITEMAP_DAILY_SOURCES`, `VEJARIO_ARCHIVE_TARGETS`, `get_active_targets`, `build_wordpress_queries_for_site`, `FLAVIO_INTERNAL_SEARCH_QUERIES` | F2-T1 | M | No | `py_compile` passes, all constants importable | Original not found in Codex log | ⬜ |
| F2-T2b | Restore original http_utils.py from 63MB Codex log — recover `canonicalize_url` and any other missing functions | F2-T2 | S | No | `py_compile` passes, `canonicalize_url` importable | Original not found in Codex log | ⬜ |
| F2-T6b | Restore original collectors.py from 63MB Codex log — recover original API signatures matching what benchmark/export expect | F2-T1b, F2-T2b | XL | No | `py_compile` passes, collector signatures match benchmark_sources_vs_excel.py calls | Original not found in Codex log | ⬜ |
| F2-T7b | Restore original ingest.py from 63MB Codex log — recover original `process_candidates` signature, full `IngestionOptions`, `FLAVIO_QUERY_VARIANTS` | F2-T5b, F2-T6b | L | No | `py_compile` passes, `process_candidates` signature matches benchmark calls | Original not found in Codex log | ⬜ |

**Tests Required:**

| What to Verify | Type | Human Needed? | Done When | Proof Artifact |
|----------------|------|---------------|-----------|----------------|
| All pipeline files compile | Unit | No | `py_compile` passes for all 8 files | Zero compile errors |
| settings.py has all sources | Unit | No | All InternalSearchTarget entries from old HTML sources present | Test asserts ≥7 targets |
| database.py creates all tables | Unit | No | SQLite tables match original schema | Test creates DB and checks schema |
| collectors.py has all collector functions | Unit | No | Each function importable | Test imports each collector |
| ingest.py has IngestionResult | Unit | No | `from pipeline.ingest import IngestionResult` works | Import test |
| matcher.py handles exact_aliases | Unit | No | `CitationMatcher` matches "Flavio Vale" as alias | Test with alias input |

---

### Feature 3: Clean and Restore Tools

**User Story:** As a developer, I want the tools (HTML export, snapshot generator, benchmarks) restored to match the original rich output.

**Acceptance Criteria:**
- [ ] `server.py` (static HTML generator) produces story-card based HTML
- [ ] `tools/export_mobile_snapshot.py` produces useful basic export
- [ ] `tools/prepare_wix_clipping_snapshot.py` functional or documented as partial
- [ ] `data/targets.json` has all 4 original targets
- [ ] All tool files pass syntax check

**Tasks:**

| ID | Task | Dependencies | Effort | live_test | Proof Required | Blocked If | Status |
|----|------|-------------|--------|-----------|----------------|------------|--------|
| F3-T1 | Restore server.py — extract HTML template from corrupted server.py (from_patches 313 lines + current 313 lines), reconstruct `prepare_snapshot` function, story card template, offline JS filter logic | MC-1, F2-T5, F2-T7 | XL | No | `py_compile` passes, generates HTML with `story-card` elements and `data-filter-target` buttons | No story cards in output |⬜ |
| F3-T2 | Restore data/targets.json — add Pedro Duarte, Bernardo Rubiao, Pedro Angelito with keywords from old HTML chip analysis | MC-1 | S | No | JSON valid, 4 targets with keywords and exact_aliases | Missing targets | ✅ [pending-verification] |
| F3-T3 | Restore tools/export_mobile_snapshot.py — keep as simpler alternative export, ensure it uses restored database queries | F2-T5 | S | No | `py_compile` passes, generates HTML from DB | Syntax error | ⬜ |
| F3-T4 | Restore tools/prepare_wix_clipping_snapshot.py — extract from fragments, document what's recoverable | MC-1 | M | No | Either functional .py or documented STUB with notes | Unknown state | ⬜ |
| F3-T5 | Restore tools/benchmark_sources_vs_excel.py — extract 12 function signatures from corrupted 708-line version, clean what's recoverable | MC-1 | L | No | `py_compile` passes or documented as partial with extracted functions | Unknown state | ⬜ |
| F3-T6 | Clean up repo — archive corrupted stubs to `raw_recovery/`, remove wrong-content files, update requirements.txt | F3-T1..F3-T5 | M | No | No corrupted files in main directories, `raw_recovery/` has originals | Corrupted files still in main dirs | ⬜ |

**Tests Required:**

| What to Verify | Type | Human Needed? | Done When | Proof Artifact |
|----------------|------|---------------|-----------|----------------|
| server.py generates story HTML | Integration | Yes — visual compare | HTML contains `story-card`, `data-story-id`, filter buttons | Generated HTML file |
| targets.json has 4 targets | Unit | No | JSON loads, 4 entries, each has keywords | Test loads and counts |
| export_mobile_snapshot.py runs | Integration | No | Generates non-empty HTML from test DB | HTML file > 1KB |

---

### Feature 4: Cross-Reference Validation

**User Story:** As a developer, I want proof that no original function or capability was missed during restoration.

**Acceptance Criteria:**
- [ ] Every function name found in corrupted originals exists in restored code
- [ ] Every import in restored code resolves
- [ ] Every source from old HTML has a corresponding collector
- [ ] DB schema matches all references across all files

**Tasks:**

| ID | Task | Dependencies | Effort | live_test | Proof Required | Blocked If | Status |
|----|------|-------------|--------|-----------|----------------|------------|--------|
| F4-T1 | Function cross-reference — grep all function/class names from corrupted originals, verify each exists in restored files | F2-T8, F3-T6 | M | No | Cross-reference table: function → file → present(Y/N) | Any function marked N without justification | ⬜ |
| F4-T2 | Import validation — `python -c "from pipeline import collectors, database, ingest, matcher, normalization, settings"` and all tools | F2-T8, F3-T6 | S | No | All imports succeed | Any import fails | ⬜ |
| F4-T3 | Source coverage check — compare sources in old HTML (diariodorio, agendadopoder, vejario, oglobo, odia, conib, cbn, extra, r7) against collector functions | F2-T6 | S | No | Every old HTML source has a collector | Source without collector | ⬜ |
| MC-2 | All files restored — user reviews cross-reference, approves | F4-T1..F4-T3 | — | No | User approves | User finds gaps | ⬜ |

**Tests Required:**

| What to Verify | Type | Human Needed? | Done When | Proof Artifact |
|----------------|------|---------------|-----------|----------------|
| All imports work | Unit | No | Zero ImportErrors | Import test script |
| All sources covered | Manual | Yes | Every source in old HTML maps to a collector | Coverage table |

---

### Feature 5: Targeted Live Validation

**User Story:** As a user, I want proof that each collector can find real articles that the original pipeline found.

**Acceptance Criteria:**
- [ ] For each source in old HTML: pick a known article URL + date, run that collector, verify it appears
- [ ] Full pipeline E2E run produces ≥50 articles from ≥5 sources
- [ ] Generated HTML report has story groupings

**Tasks:**

| ID | Task | Dependencies | Effort | live_test | Proof Required | Blocked If | Status |
|----|------|-------------|--------|-----------|----------------|------------|--------|
| F5-T1 | Extract test oracle — parse old HTML snapshot, extract article URLs grouped by source with dates | MC-2 | M | No | JSON/dict of {source: [{url, title, date}]} for ≥5 sources | Old HTML unparseable | ⬜ |
| F5-T2 | Validate Globo family (O Globo, Extra) — run collector for known articles | F5-T1 | M | Yes | Collector returns ≥1 known article | 0 results | ⬜ |
| F5-T3 | Validate WordPress (diariodorio, agendadopoder) — run collector for known articles | F5-T1 | M | Yes | Collector returns ≥1 known article | 0 results | ⬜ |
| F5-T4 | Validate HTML scrapers (O Dia, CONIB, Veja Rio, Camara) — run collector for known articles | F5-T1 | M | Yes | Each collector returns ≥1 known article with proper filtering | Junk results or 0 results | ⬜ |
| F5-T5 | Validate CBN sitemap — run collector for known articles | F5-T1 | S | Yes | Collector returns ≥1 known article | 0 results | ⬜ |
| F5-T6 | Validate Google News RSS — run collector for known articles | F5-T1 | S | Yes | Collector returns ≥1 article | 0 results | ⬜ |
| F5-T7 | Full E2E pipeline run — all collectors, all targets, recent date range | F5-T2..F5-T6 | L | Yes | `data/clipping.db` has ≥50 articles from ≥5 sources | DB empty or <50 articles | ⬜ |
| F5-T8 | Generate rich HTML report — run server.py/export on E2E results | F5-T7, F3-T1 | M | Yes | HTML file with `story-card` elements, filter buttons, matches old snapshot structure | Flat list or empty | ⬜ |
| F5-T9 | Push to GitHub — commit all restored files, push to OttoBoop/clipping-project | F5-T8 | S | No | `git push` succeeds | Push fails | ⬜ |

**Tests Required:**

| What to Verify | Type | Human Needed? | Done When | Proof Artifact |
|----------------|------|---------------|-----------|----------------|
| Globo collector returns articles | Live | Yes | ≥1 known article found | Console output showing matched article |
| WordPress collector returns articles | Live | Yes | ≥1 known article found | Console output |
| HTML scrapers return articles | Live | Yes | ≥1 known article per source, no junk | Console output |
| Full pipeline produces rich HTML | E2E + Visual | Yes | HTML has stories, filters, ≥50 articles | Generated HTML file compared to old |

---

## 5. Test Strategy

### 5.1 Testing Pyramid
- **Unit Tests:** Syntax checks (`py_compile`), import checks, schema validation, target/matcher logic
- **Integration Tests:** Each collector against live sources, DB read/write roundtrip, export generation
- **E2E Tests:** Full pipeline run → DB → HTML export, compared against old snapshot oracle

### 5.2 TDD Checklist (Per Task)
```
For EACH task, BEFORE writing implementation:
1. [ ] Write failing test describing expected behavior
2. [ ] Verify test fails for the RIGHT reason
3. [ ] Commit failing test with message: "test: [description]"
4. [ ] Write MINIMUM code to pass test
5. [ ] Verify test passes
6. [ ] Refactor if needed (tests MUST stay green)
7. [ ] Commit with message: "feat: [description]"
```

**Note:** For Wave 1 (audit) and Wave 2-3 (cleaning), TDD means: write a compile/import test first, then clean the file until it passes. For Wave 5 (validation), TDD means: write a test that expects a specific article from a specific source, then fix the collector until it finds it.

### 5.3 Testing Commands
```bash
# Run all tests
cd D:/recovery/clipping-project && python -m pytest tests/ -v

# Run single test
python -m pytest tests/test_specific.py -v

# Syntax check all files
python -c "import py_compile, glob; [py_compile.compile(f, doraise=True) for f in glob.glob('**/*.py', recursive=True)]"

# Quick pipeline smoke test
python run_ingestion.py all --target flavio_valle --date-from 2026-03-28 --date-to 2026-03-30
```

---

## 6. Dependency & Parallelism Analysis

### 6.1 Task Dependency Graph
```
F1-T1 ──┐
F1-T2 ──┼──> F1-T5 ──> MC-1
F1-T3 ──┤                │
F1-T4 ──┘                │
                    ┌─────┼──────────────┐
                    │     │              │
                 F2-T1  F2-T2  F2-T3   F3-T2
                 F2-T4  F2-T5           │
                    │     │              │
                    └──┬──┘              │
                       │                 │
                    F2-T6 ──> F2-T7 ──> F2-T8
                                │
                          ┌─────┼──────┐
                          │     │      │
                        F3-T1 F3-T3  F3-T4
                          │          F3-T5
                          │            │
                          └──────┬─────┘
                                 │
                              F3-T6
                                 │
                    F4-T1 ──┐    │
                    F4-T2 ──┼────┘
                    F4-T3 ──┘
                        │
                      MC-2
                        │
                     F5-T1
                        │
              ┌────┬────┼────┬────┐
              │    │    │    │    │
           F5-T2 F5-T3 F5-T4 F5-T5 F5-T6
              │    │    │    │    │
              └────┴────┼────┴────┘
                        │
                     F5-T7 ──> F5-T8 ──> F5-T9
```

### 6.2 Parallelism Reasoning

| Task Group | Tasks | Why Parallel? |
|------------|-------|---------------|
| **Batch A: Audit** | F1-T1, F1-T2, F1-T3, F1-T4 | Independent file reads — each audits a different directory |
| **Batch B: Pipeline cleanup (independent modules)** | F2-T1, F2-T2, F2-T3, F2-T4, F2-T5, F3-T2 | Each modifies a different file with no shared imports |
| **Batch C: Collectors (depends on settings+http)** | F2-T6 | Sequential — needs settings and http_utils done first |
| **Batch B2: Restore originals (independent modules)** | F2-T5b, F2-T1b, F2-T2b | Parallel — independent files, each extracted from 63MB Codex log |
| **Batch B3: Restore originals (depends on settings+http)** | F2-T6b | Sequential — collectors needs restored settings + http_utils |
| **Batch B4: Restore originals (depends on db+collectors)** | F2-T7b | Sequential — ingest needs restored database + collectors |
| **Batch D: Tools (depends on pipeline)** | F3-T1, F3-T3, F3-T4, F3-T5 | Partially parallel — each tool is independent but needs pipeline |
| **Batch E: Collectors validation** | F5-T2, F5-T3, F5-T4, F5-T5, F5-T6 | Parallel — each tests a different collector against different sources |
| **Batch F: E2E** | F5-T7, F5-T8, F5-T9 | Sequential — each depends on previous |

### 6.3 Task Dependency Table

| Task | Description | Depends On | Unblocks | Status |
|------|-------------|------------|----------|--------|
| F1-T1 | Audit pipeline/ from_patches files | None | F1-T5 | ✅ |
| F1-T2 | Audit tools/ from_patches files | None | F1-T5 | ✅ |
| F1-T3 | Audit test files from_patches | None | F1-T5 | ✅ |
| F1-T4 | Audit non-py + CLIPPING_EXTRACTED comparison | None | F1-T5 | ✅ |
| F1-T5 | Cross-reference gap list | F1-T1, F1-T2, F1-T3, F1-T4 | MC-1 | ✅ |
| MC-1 | ⊕ Audit complete — user reviews | F1-T5 | F2-T1..F2-T5, F2-T8, F3-T2 | ✅ |
| F2-T1 | Clean settings.py | MC-1 | F2-T6 | ✅ [pending-verification] |
| F2-T2 | Clean http_utils.py | MC-1 | F2-T6 | ✅ [pending-verification] |
| F2-T3 | Create/clean normalization.py | MC-1 | F2-T7 | ✅ [pending-verification] |
| F2-T4 | Clean matcher.py | MC-1 | F2-T7 | ✅ [pending-verification] |
| F2-T5 | Clean database.py (rewrite) | MC-1 | F2-T5b, F2-T6, F2-T7, F3-T1, F3-T3 | ✅ [pending-verification] |
| F2-T6 | Clean collectors.py (rewrite) | MC-1, F2-T1, F2-T2 | F2-T6b, F2-T7, F4-T3 | ✅ [pending-verification, needs-human-review] |
| F2-T7 | Clean ingest.py (rewrite) | MC-1, F2-T3, F2-T4, F2-T5, F2-T6 | F2-T7b, F2-T8 | ✅ [pending-verification] |
| F2-T8 | Clean run_ingestion.py | F2-T7 | F3-T6, F4-T1, F4-T2 | ✅ [pending-verification] |
| F2-T5b | Restore original database.py from Codex log | F2-T5 | F2-T7b, F3-T6 | ⬜ |
| F2-T1b | Restore original settings.py from Codex log | F2-T1 | F2-T6b | ⬜ |
| F2-T2b | Restore original http_utils.py from Codex log | F2-T2 | F2-T6b | ⬜ |
| F2-T6b | Restore original collectors.py from Codex log | F2-T1b, F2-T2b | F2-T7b, F4-T3 | ⬜ |
| F2-T7b | Restore original ingest.py from Codex log | F2-T5b, F2-T6b | F3-T6 | ⬜ |
| F3-T1 | Restore server.py (HTML generator) | MC-1, F2-T5, F2-T7 | F3-T6, F5-T8 | ✅ [pending-verification] |
| F3-T2 | Restore targets.json (4 targets) | MC-1 | F3-T6 | ✅ [pending-verification] |
| F3-T3 | Restore export_mobile_snapshot.py from Codex log | F2-T5 | F3-T6 | ✅ [pending-verification] |
| F3-T4 | Restore prepare_wix_clipping_snapshot.py | MC-1 | F3-T6 | ✅ [pending-verification] |
| F3-T5 | Restore benchmark_sources_vs_excel.py | MC-1 | F3-T6 | ✅ [pending-verification] |
| F3-T6 | Cleanup repo — archive corrupted files | F2-T8, F2-T7b, F3-T1..F3-T5 | F4-T1, F4-T2 | ⬜ |
| F4-T1 | Function cross-reference check | F2-T8, F3-T6 | MC-2 | ⬜ |
| F4-T2 | Import validation | F2-T8, F3-T6 | MC-2 | ⬜ |
| F4-T3 | Source coverage check | F2-T6b | MC-2 | ⬜ |
| MC-2 | ⊕ All files restored — user reviews | F4-T1, F4-T2, F4-T3 | F5-T1 | ⬜ |
| F5-T1 | Extract test oracle from old HTML | MC-2 | F5-T2..F5-T6 | ⬜ |
| F5-T2 | Validate Globo collectors | F5-T1 | F5-T7 | ⬜ |
| F5-T3 | Validate WordPress collectors | F5-T1 | F5-T7 | ⬜ |
| F5-T4 | Validate HTML scrapers | F5-T1 | F5-T7 | ⬜ |
| F5-T5 | Validate CBN sitemap | F5-T1 | F5-T7 | ⬜ |
| F5-T6 | Validate Google News RSS | F5-T1 | F5-T7 | ⬜ |
| F5-T7 | Full E2E pipeline run | F5-T2..F5-T6 | F5-T8 | ⬜ |
| F5-T8 | Generate rich HTML report | F5-T7, F3-T1 | F5-T9 | ⬜ |
| F5-T9 | Push to GitHub | F5-T8 | — | ⬜ |

---

## 7. Implementation Phases

### Phase 1: Forensic Audit (Batch A — parallel)

| Batch | Tasks | Parallel? | Rationale |
|-------|-------|-----------|-----------|
| A | F1-T1, F1-T2, F1-T3, F1-T4 | Yes | Independent file reads |
| A' | F1-T5 | No | Needs all audit results |

- [ ] F1-T1: Audit pipeline/ from_patches
- [ ] F1-T2: Audit tools/ from_patches
- [ ] F1-T3: Audit test files
- [ ] F1-T4: Audit non-py + CLIPPING_EXTRACTED
- [ ] F1-T5: Cross-reference gap list
- [ ] MC-1: User reviews audit

### Phase 2: Clean Pipeline Core (Batch B — partially parallel)

| Batch | Tasks | Parallel? | Rationale |
|-------|-------|-----------|-----------|
| B1 | F2-T1, F2-T2, F2-T3, F2-T4, F2-T5, F3-T2 | Yes | Independent files |
| B2 | F2-T6 | No | Needs settings + http_utils |
| B3 | F2-T7 | No | Needs everything above |
| B4 | F2-T8 | No | Needs ingest |

- [ ] F2-T1..F2-T5, F3-T2: Clean independent modules (parallel)
- [ ] F2-T6: Clean collectors.py
- [ ] F2-T7: Clean ingest.py
- [ ] F2-T8: Clean run_ingestion.py

### Phase 2.5: Restore Pipeline Originals from 63MB Codex Log (Batch B2-B4)

F2-T1..T8 produced simplified rewrites, not true restorations. The 63MB Codex session
log (`D:\recovery\YOUR_FILES\recovered_224598MB_63334KB.py`) contains complete original
versions — proven by successful recovery of export_mobile_snapshot.py (1247 lines, 30 functions).

| Batch | Tasks | Parallel? | Rationale |
|-------|-------|-----------|-----------|
| B2 | F2-T5b, F2-T1b, F2-T2b | Yes | Independent files, each extracted from Codex log |
| B3 | F2-T6b | No | Collectors needs restored settings + http_utils |
| B4 | F2-T7b | No | Ingest needs restored database + collectors |

- [ ] F2-T5b: Restore database.py (original 361 lines → `story_with_articles()`, richer queries)
- [ ] F2-T1b: Restore settings.py (`WORDPRESS_API_SITES`, `get_active_targets`, etc.)
- [ ] F2-T2b: Restore http_utils.py (`canonicalize_url`)
- [ ] F2-T6b: Restore collectors.py (original API signatures matching benchmark/export)
- [ ] F2-T7b: Restore ingest.py (original `process_candidates` signature, full `IngestionOptions`)

### Phase 3: Restore Tools (Batch C — partially parallel)

| Batch | Tasks | Parallel? | Rationale |
|-------|-------|-----------|-----------|
| C1 | F3-T1, F3-T3, F3-T4, F3-T5 | Yes | Independent tool files |
| C2 | F3-T6 | No | Needs all tools done |

- [ ] F3-T1: Restore server.py
- [ ] F3-T3: Restore export_mobile_snapshot.py
- [ ] F3-T4: Restore prepare_wix_clipping_snapshot.py
- [ ] F3-T5: Restore benchmark_sources_vs_excel.py
- [ ] F3-T6: Cleanup repo

### Phase 4: Cross-Reference (Batch D — parallel)

| Batch | Tasks | Parallel? | Rationale |
|-------|-------|-----------|-----------|
| D | F4-T1, F4-T2, F4-T3 | Yes | Independent validation checks |

- [ ] F4-T1: Function cross-reference
- [ ] F4-T2: Import validation
- [ ] F4-T3: Source coverage
- [ ] MC-2: User reviews

### Phase 5: Live Validation (Batch E — partially parallel)

| Batch | Tasks | Parallel? | Rationale |
|-------|-------|-----------|-----------|
| E0 | F5-T1 | No | Needs MC-2 |
| E1 | F5-T2, F5-T3, F5-T4, F5-T5, F5-T6 | Yes | Independent collector tests |
| E2 | F5-T7, F5-T8, F5-T9 | No | Sequential E2E chain |

- [ ] F5-T1: Extract test oracle
- [ ] F5-T2..F5-T6: Validate each collector group (parallel)
- [ ] F5-T7: Full E2E run
- [ ] F5-T8: Generate rich HTML
- [ ] F5-T9: Push to GitHub

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| from_patches files too corrupted to clean | Medium | High | Fall back to disk image search (D:\ssd recovery\laptop ssd.001). Extract more fragments using keyword search. |
| Globo API blocks requests | Medium | Medium | Test with different User-Agent headers, check if API requires specific referrer. The original code worked — find what made it work. |
| Original collector logic unrecoverable | Low | High | Use test fixtures (HTML selectors from test_internal_site_search_collectors.py) to reconstruct collector logic. |
| Sites changed HTML structure since original | Medium | Medium | Compare current site HTML against test fixtures. Update selectors if needed, document changes. |
| Story grouping logic too complex to recover | Medium | High | server.py has 250+ lines of template. Between that and the JS in old HTML, the logic is reconstructable. |
| Python not installed on current machine | High | Medium | Need to install Python 3.x before any code can run. Check PATH. |

---

## 9. Open Questions

- [ ] Is Python installed and working? (audit showed `python.exe` not found at expected PATH)
- [ ] Does the user have an Anthropic API key for AI summaries? (deferred but needed eventually)
- [ ] What date ranges should the targeted validation use? (extract from old HTML)
- [ ] Are there more Codex session logs beyond what was already extracted from the disk image?
- [ ] The 62MB file `D:\recovery\YOUR_FILES\recovered_224598MB_63334KB.py` — should we mine it for more code?

---

## 10. Approval Checklist

- [ ] Requirements reviewed by: _____________ Date: _________
- [ ] Architecture reviewed by: _____________ Date: _________
- [ ] Plan approved by: _____________ Date: _________

---

## 11. Change Log

### Decision Ledger

- 2026-03-30: [PLAN_Clipping_Reconstruction.md](D:/recovery/clipping-project/docs/PLAN_Clipping_Reconstruction.md) remains the task and dependency authority; [FORENSIC_INVENTORY.md](D:/recovery/clipping-project/docs/FORENSIC_INVENTORY.md) remains the provenance authority; [DISCOVERY_Clipping_Reconstruction_Debug.md](D:/recovery/clipping-project/docs/DISCOVERY_Clipping_Reconstruction_Debug.md) remains the architectural and intent guardrail.
- 2026-03-30: Prior Batch B2 completion claims for `F2-T5b`, `F2-T1b`, and `F2-T2b` remain withdrawn because those edits were reconstructions, not verified original recoveries.
- 2026-03-30: The only allowed provenance labels remain `recovered verbatim`, `recovered and cleaned`, `reconstructed from evidence`, and `not yet recovered`.
- 2026-03-30: `F2-T5b` is the only active implementation task. `F2-T1b` and `F2-T2b` remain open but deferred until the `F2-T5b` evidence pass is fully cataloged.
- 2026-03-30: Compatibility or test green is not sufficient to mark a `restore original` task complete.
- 2026-03-30: `F2-T5b` evidence-pass result is `NO-GO` for runtime merge at this time. Recovered fragments are strong for `story_with_articles()` and partial export/query surfaces, but the surrounding `database.py` base is still too contaminated and incomplete for a faithful replacement.
- 2026-03-30: Any future compatibility/scaffold changes for `database.py` are explicitly deferred. They are not part of `F2-T5b` unless the task is later reclassified away from strict original recovery.
- 2026-03-30: `F2-T5b` extraction pass 2 improved the evidence base: the file head through `list_story_context()` is now treated as `recovered and cleaned`, `list_articles_for_export()` has a cleaner patch fragment, and the large recovered `.py` bundle is explicitly classified as contaminated rather than clean source proof.
- 2026-03-30: With `F2-T5b` extraction pass 2 exhausted and still `NO-GO`, `F2-T5b` remains open but blocked. The next original-plan recovery lane can now advance to `F2-T1b` and `F2-T2b`.

| Date | Change | Author |
|------|--------|--------|
| 2026-03-30 | Initial plan created from discovery + forensic inventory | Claude Opus 4.6 |
| 2026-03-30 | F3-T3 restored: original export_mobile_snapshot.py (1247 lines) from 63MB Codex log | Claude Opus 4.6 |
| 2026-03-30 | F3-T4, F3-T5 restored from Codex log + corrupted from_patches | Claude Opus 4.6 |
| 2026-03-30 | Added Wave 2.5 (F2-T1b..T7b): restore pipeline originals from 63MB Codex log. F2 rewrites were placeholders, not restorations. Restructured dependency table accordingly. | Claude Opus 4.6 |
| 2026-03-30 | Correction: prior Codex Batch B2 completion claim for F2-T5b, F2-T1b, and F2-T2b was withdrawn. Those edits were evidence-based reconstructions, not verified original recoveries, so the tasks were reopened. | Codex |
| 2026-03-30 | Provenance-only restart of Wave 2.5: cataloged current evidence for F2-T5b/F2-T1b/F2-T2b in FORENSIC_INVENTORY before any new code edits. Database remains partial-block recovery only; settings/http now have candidate artifacts but are still not accepted as clean originals. | Codex |
| 2026-03-30 | Completed the deeper artifact-first evidence pass for F2-T5b. Result: `NO-GO` for runtime merge; `story_with_articles()` is recoverable as a fragment, but the surrounding `database.py` base and neighboring query bodies still lack a clean file-level recovery. No runtime code changes were made. | Codex |
| 2026-03-30 | Completed `F2-T5b` extraction pass 2. Decision remained `NO-GO`: the base section through `list_story_context()` is now stronger and `list_articles_for_export()` has a cleaner fragment, but `list_articles()` and `list_articles_by_ids()` still block a faithful stitched original. Runtime `pipeline/database.py` was not edited, and non-original compatibility changes remain deferred. | Codex |
