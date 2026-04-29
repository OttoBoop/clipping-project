# Clipping Project — Reconstruction Plan

**Date:** 2026-03-30
**Goal:** Reconstruct working pipeline from corrupted recovery fragments, then run a real ingestion for target `flavio_valle` from 2026-03-27 to 2026-03-30.

---

## Current State

The recovered files have binary Codex log data interleaved with valid Python. We extracted:
- **Function/class signatures** — complete list of all functions, classes, dataclasses
- **Architecture** — how modules connect, data flow, CLI arguments
- **Partial code** — fragments of actual implementations (some functions are 80%+ intact)
- **Configuration** — collector types, target structure, database schema

What we do NOT have clean:
- Complete function bodies for most pipeline functions
- The exact HTML parsing selectors for each news source
- The exact URL patterns for each internal search target
- The runtime.json configuration

---

## Architecture (Recovered)

```
run_ingestion.py (CLI)
    │
    ├── pipeline/settings.py      — Target configs, source definitions
    ├── pipeline/http_utils.py    — HTTP fetch with retries, user-agent
    ├── pipeline/normalization.py — URL canonicalization
    ├── pipeline/collectors.py    — 12+ news source collectors
    ├── pipeline/matcher.py       — Keyword matching against targets
    ├── pipeline/database.py      — SQLite storage
    └── pipeline/ingest.py        — Orchestrator: collect → fetch → match → store
```

### Data Flow
```
1. run_ingestion.py parses CLI args → creates IngestionOptions
2. ingest.py selects collectors based on --collector flag
3. Each collector yields CandidateArticle objects (url, title, snippet, source)
4. ingest.py processes candidates:
   a. Preview match: check title/snippet for target keywords
   b. Full fetch: download article body if needed
   c. Body match: re-check full text for keywords
   d. Store: insert matched articles + mentions into SQLite
5. Results printed to console
```

---

## Files to Reconstruct

### 1. `data/targets.json` — Target Configuration
**Recovered info:**
- Primary target: `flavio_valle` with keywords "Flavio Valle", "Flávio Valle", "vereador Flavio"
- exact_aliases: ["Flavio Vale"]
- Structure: `{key, label, className, primary, keywords, exact_aliases}`

**Action:** Rewrite from known structure.

### 2. `pipeline/settings.py` — Source Definitions
**Recovered info:**
- `FLAVIO_INTERNAL_SEARCH_TARGETS` — list of InternalSearchTarget objects
- Sources: oglobo.globo.com, extra.globo.com, camara.rio, conib.org.br, odia.ig.com.br, r7.com
- RSS feeds for various news sites
- Sitemap URLs for CBN, agendadopoder, etc.
- `benchmark_day_limit` config values
- WordPress API endpoints

**Action:** Reconstruct with known sources. Some selectors may need testing.

### 3. `pipeline/http_utils.py` — HTTP Utilities
**Recovered signatures:**
- `fetch_url(url, *, timeout=8, headers=None) -> tuple[str, str]` (returns body, final_url)
- `post_json(url, payload, *, timeout=8) -> dict`
- `try_resolve_google_redirect(url) -> str`
- `_build_ssl_fallback_context() -> ssl.SSLContext`
- User-agent rotation
- Retry logic

**Action:** Rewrite from signatures. Standard HTTP utility code.

### 4. `pipeline/normalization.py` — URL/Text Normalization
**Recovered signatures:**
- `normalize_url(u: str) -> str` — canonicalize URLs (strip tracking params, lowercase, etc.)
- `canonicalize_url(url: str) -> str` — alias or extended version
- `clean_title(title: str) -> str` — strip HTML entities, extra whitespace

**Action:** Rewrite from signatures. Standard URL normalization.

### 5. `pipeline/matcher.py` — Keyword Matching
**Recovered code (mostly intact):**
- `@dataclass Target: key, label, display_name, keywords, exact_aliases, className, primary`
- `CitationMatcher(targets, *, exact_names_only=False)`
- `find_hits(text) -> list[MatchHit]` — scan text for keyword matches
- `MatchHit: target_key, keyword_matched, position`

**Action:** Rewrite — this is straightforward keyword matching.

### 6. `pipeline/database.py` — SQLite Storage
**Recovered schema:**
```sql
articles (id, url, title, source_name, source_type, published_at, discovered_at, snippet, full_text, summary)
mentions (article_id, target_key, target_name, keyword_matched, sentiment, sentiment_reason)
story_articles (article_id, story_id)
```
**Recovered methods:**
- `ClippingDB(db_path)` — context manager
- `insert_article(url, title, source_name, source_type, published_at, snippet, full_text) -> article_id`
- `insert_mention(article_id, target_key, target_name, keyword_matched)`
- `article_exists(url) -> bool` — deduplication check
- `list_articles_for_export(date_from, date_to, target_key) -> list[dict]`

**Action:** Rewrite from schema + method signatures.

### 7. `pipeline/collectors.py` — News Source Collectors
**Recovered collector types:**

| Collector | Method | Sources | How it works |
|-----------|--------|---------|-------------|
| `collect_google_news` | Google News RSS | news.google.com | Fetch RSS feed for query, parse entries |
| `collect_rss` | Standard RSS | Various | Fetch RSS/Atom feeds, parse with feedparser or xml.etree |
| `collect_wordpress_api` | WordPress REST API | agendadopoder.com.br | `GET /wp-json/wp/v2/posts?search=...` |
| `collect_internal_site_search` | Site-specific HTML | Globo, Câmara, CONIB, R7, Odia | Fetch search page, parse HTML for links |
| `collect_sitemap_daily` | XML sitemaps | CBN, various | Parse sitemap.xml, filter by date window |
| `collect_vejario_archive` | Archive page scraping | vejario.abril.com.br | Paginated archive browsing |
| `collect_camara_archive` | Câmara do Rio archive | camara.rio | Search + paginate |
| `collect_direct_scrape` | Google search + browser | Google | **SKIP — requires browser** |

**Recovered dataclass:**
```python
@dataclass
class CandidateArticle:
    url: str
    title: str
    source_name: str
    source_type: str  # 'rss', 'google_news', 'wordpress_api', etc.
    published_at: str | None
    snippet: str
    metadata: dict | None
```

**Recovered helpers:**
- `_within_window(published_at, date_from, date_to) -> bool`
- `_build_specialized_candidate(*, title, url, source_name, source_type, published_at, snippet, metadata) -> CandidateArticle`
- `_dedupe_candidates_by_url(candidates) -> list[CandidateArticle]`
- `_extract_internal_search_results(adapter, html_page, search_url) -> tuple[list, list]`
- `_collect_globo_internal_search(adapter, query, limit, timeout, date_from, date_to)`
- `_extract_camara_results(html_page, search_url, source_name)`
- `_extract_conib_results(html_page, search_url, source_name)`
- `_extract_vejario_results(html_page, search_url, source_name)`

**Action:** Reconstruct each collector. Google News RSS is straightforward. WordPress API is standard REST. Internal search requires testing HTML selectors (may need adjustment for each site). Sitemap parsing is standard XML.

### 8. `pipeline/ingest.py` — Orchestrator
**Recovered flow:**
1. Parse IngestionOptions from CLI args
2. Load targets from targets.json
3. Select collectors based on --collector flag
4. For each collector, generate `plans` list of (collector_name, query, candidates_batch)
5. Process each candidate:
   - Preview match: check title/snippet
   - If match or force_full_fetch: fetch full article body
   - Body match: re-check full text
   - If matched: insert into database
6. Deduplication by URL across all batches
7. Print summary

**Recovered key logic:**
- When collector="all" and target="flavio_valle", auto-injects internal_search batches
- `select_targets()` filters targets.json by --target arg
- `emit_candidate()` handles the accept/skip/error logging

**Action:** Reconstruct orchestrator. Most complex file but flow is clear.

### 9. `run_ingestion.py` — CLI Entry Point
**Recovered args:**
- `collector` (choices: all, rss, google_news, direct_scrape, wordpress_api, internal_search, sitemap_daily, vejario_archive, camara_archive)
- `--query` (optional custom search query)
- `--target` (default: "flavio_valle")
- `--date-from` / `--date-to` (date range)
- `--db` (database path, default: data/clipping.db)
- `--request-timeout` (default: 8)

**Action:** Rewrite — straightforward argparse.

---

## Test Run Plan

After reconstruction:
```bash
cd D:\recovery\clipping-project
python run_ingestion.py all --target flavio_valle --date-from 2026-03-27 --date-to 2026-03-30 --skip-direct-scrape
```

Expected behavior:
1. Google News RSS → search "Flavio Valle" → parse results
2. WordPress API → agendadopoder.com.br search
3. Internal search → Globo, Câmara, CONIB, R7, Odia
4. Sitemap daily → CBN, other sites → filter by date range
5. For each candidate: fetch body → match keywords → store in clipping.db
6. Print summary: X candidates found, Y matched, Z stored

---

## Dependencies

```
# requirements.txt
feedparser>=6.0      # RSS parsing
requests>=2.28       # HTTP (may use urllib instead)
```

Most functionality uses stdlib: `urllib`, `xml.etree`, `sqlite3`, `json`, `re`, `datetime`, `argparse`, `pathlib`, `ssl`, `html`.

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| HTML selectors for internal search are wrong | Test each source individually, fix selectors |
| Google News RSS format changed | Use standard RSS parsing, adapt if needed |
| Some sites block scraping | Use proper User-Agent, respect robots.txt |
| Date parsing differs by source | Support multiple formats (ISO, RFC822, Brazilian) |
| Missing edge case handling | Accept partial results, log errors, continue |

---

## Execution Order

1. Write `data/targets.json`
2. Write `pipeline/__init__.py`, `normalization.py`, `http_utils.py`
3. Write `pipeline/matcher.py`
4. Write `pipeline/database.py`
5. Write `pipeline/settings.py`
6. Write `pipeline/collectors.py`
7. Write `pipeline/ingest.py`
8. Write `run_ingestion.py`
9. Write `requirements.txt`
10. Install deps + test run
11. Fix issues iteratively
12. Commit + push working version
