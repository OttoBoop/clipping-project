# Tech Debt Audit — clipping-project
Generated: 2026-05-04 by Iris (Claude Code orchestrator)
Updated: 2026-05-05 — Q1-Q5 resolutions absorbed; conservative tone (MOVE not DELETE); honest limitations section added.

Project ground truth (LIVE/LEGACY/UNCLEAR classification) lives in `AUDIT_GROUND_TRUTH.md` — this report skips LEGACY items in non-security dimensions per the project override of the tech-debt-audit skill.

## Live verification status (2026-05-05) — A-007 in ATLAS_IRIS_ASYNC.md

After Iris-local realized the audit had been written from a misapplied
cloud-Iris protocol, all six Q-007 blocks were re-executed locally. Findings
that were live-verified are tagged `[VERIFIED LIVE 2026-05-05]` in the
findings table below. Quick summary:

| Finding | Live status | Evidence |
|---|---|---|
| **F001-F009** auth bypass on 9 mutating endpoints | **CONFIRMED P0 in production** | `curl -X POST .../api/update/cancel` returned HTTP 409 + `{"detail":"no_active_job"}` without auth. If gate worked, 401 + `admin_login_required`. |
| **F011** lifespan silent failure | **Latent (not broken now)** — severity downgraded from Critical to High | `/healthz` returned `storage.enabled:true`, no degradation flag (because endpoint isn't instrumented for it). Static finding stands; production isn't degraded right now. |
| **F012** `is_recent_enough` returns True on parse error | **CONFIRMED P0** | `python -c "is_recent_enough('not-a-date')"` → `True` (also empty string and garbage ISO). |
| **F023** silent storage_bridge failures | **NOT VERIFIABLE this session** | Render-mcp not configured (`.env.render-mcp` is empty template). Static finding stands; live signal pending. |
| **F049** `office_docs/` is junk | **CONFIRMED with high confidence** | All 77 files share mtime `2026-03-31 12:19:43` (bulk-import signature) + zero references outside this repo's audit docs. |
| **F055** `run_parallel_non_direct_ingestion.py` status | **LIVE but DORMANT** | Last real run 2026-04-08; imports from `pipeline.*`; documented in `docs/PIPELINE.md`. Open question: still earning its keep? |

**Bonus discovery:** Supabase bucket is `documentos` (per healthz). If this bucket is shared across other Otavio projects, F011's blast radius is larger than the clipping app alone.

## What this audit could verify and what it could NOT

Iris is firewalled (HTTP 403 to clipping-project.onrender.com from the Anthropic egress proxy — same constraint that drove Q-002 in `ATLAS_IRIS_ASYNC.md`) and the local audit environment is missing several Python tools. So this audit is a **static, code-only** review. Be skeptical of any finding for which the audit could not run a check.

**Could verify (high confidence):**
- File contents and import graph (full reads of `web_app/app.py`, `web_app/auth.py`, `pipeline/ingest.py`, `pipeline/http_utils.py`, `web_app/storage_bridge.py`, `render.yaml`, `requirements.txt`, `README.md`, both `md documents/ATLAS_*.md`)
- `rg` / file structure / git log (200 commits + 6-month churn)
- Dep usage by absolute-path grep across LIVE files
- LIVE/LEGACY classification per `AUDIT_GROUND_TRUTH.md`

**Could NOT verify (need Atlas to confirm):**
- **Live behavior of any endpoint** — F001-F010 are based on reading source. Atlas needs to confirm the auth bypass is actually exploitable on `https://clipping-project.onrender.com/`. See Q-007 in `md documents/ATLAS_IRIS_ASYNC.md`.
- **Test suite status** — `pytest` was not run. Findings about test debt (F032-F036) assume the suite passes today; if it doesn't, the priority order changes.
- **Dead code beyond grep** — `vulture`, `ruff`, `pip-audit`, `pydeps` were not installed. Real dead-code coverage may be larger than F037-F039 suggest.
- **CVEs in deps** — `pip-audit` was not run. F042 (no security tooling in CI) is acknowledged.
- **CSS/JS bundle health** — frontend was only spot-checked at `assets/clipping.js:1818, 1902-1914`. No bundle-size or asset audit.
- **Whether `BASE_CATEGORIES` (web_app/app.py:39-53) matches what's actually seeded on Render right now** — only Atlas can `curl /api/categories` to confirm.

## Inconsistencies the parallel audit agents introduced (and how they were reconciled)

This audit dispatched 3 Explore subagents in parallel (Phase 2B), one per dimension cluster. The parallelism was efficient but introduced contradictions that Iris reconciled by reading full files. Documented for transparency:

| Claim | Source | Reconciliation |
|---|---|---|
| "anthropic SDK not used in LIVE code" | Agent 3 (deps audit) | **WRONG.** `tools/classify_articles.py:27` imports anthropic. Agent 3 missed it because of relative-path grep falling outside its working dir. Iris caught this by re-running grep with absolute paths from `clipping-project/`. |
| "f-string SQL with `placeholders` is fragile / SQL injection risk" | Agent 1 (consistency) | **FALSE POSITIVE.** `placeholders = ", ".join("?" for _ in ids)` is generated from `len(ids)`, with values passed parametrically as the second `.execute()` arg. Moved to "Looks bad but is fine". |
| "feedparser unused" | Agent 3 | **CORRECT** (and reconfirmed via abs-path grep). Collectors use `xml.etree.ElementTree`. |
| "feedparser used in production stack" | README.md:142 | Stale README claim. F044 covers this. |
| F022 (read_json silent fallback) appeared in both Agent 1 and Agent 2 reports | both agents | Duplicate but not a problem — high-confidence finding cross-referenced. |
| "PYTHON_VERSION=3.14.3 will not exist on Render" | Agent 3 (severity Critical in their original) | **OVERREACH.** Render does support exact patch pins via the rust-installer. Pin is fragile (F040, severity Medium) but not "will not exist". Iris downgraded severity. |

**Lesson for future audits:** parallel agents can each work from a wrong premise. Cross-checking via full-file reads is mandatory before promoting any finding to P0. Multi-agent consensus (CodeAnt-style "surface only if 2+ agree") was not applied here — recommend for next iteration.

## Executive summary

1. **9 unauthenticated mutating endpoints in production** (`web_app/app.py:222-470`). `/api/update/start`, `/api/update/cancel`, `/api/export`, `/api/targets` POST/PATCH, archive/restore, `/api/categories` POST, `/api/classifications` POST/GET — none call `require_admin()`. Anyone with the URL can trigger ingestion, mutate targets, or write classifications. **Critical**.
2. **Lifespan startup masks Supabase failure** (`web_app/app.py:118-145`). `artifact_store.download_current_artifacts()` is called with no try/except — if Supabase is down, the app boots with an **empty DB** and serves stale state without alarm.
3. **Date filter that says yes on parse error** (`pipeline/ingest.py:263-275`). `is_recent_enough` returns `True` when date parsing throws, so articles with malformed dates pass the recency window. The opposite of what filtering is for.
4. **43 silent `except Exception:`** across LIVE code: 18 in `pipeline/collectors.py`, 8 in `pipeline/http_utils.py`, 7 in `pipeline/ingest.py`, 6 in `web_app/storage_bridge.py`, 3 in `pipeline/database.py`, plus scattered. Failures vanish; production "works" while dropping articles or skipping a feed.
5. **Five god files concentrate the churn**: `tools/export_mobile_snapshot.py` (3267 LOC, 14 changes/6mo), `pipeline/collectors.py` (1519, 12), `pipeline/database.py` (1274, 12), `pipeline/ingest.py` (1185, 13), `web_app/jobs.py` (736, 11). Top 5 churned files are also top 5 largest — debt and instability are correlated.
6. **`office_docs/` = 91 MB of accidentally-committed Office temp files** (~70 .xlsx/.docx/.pptx with content-hash filenames like `f424460288.pptx`). Not in README, not in `.gitignore`, not imported, not referenced. Pure repo bloat.
7. **README is drifted at the top** (`README.md:137-142`): claims requirements are only `feedparser` + `requests` and that "Most logic uses the standard library". Reality: 8 deps, FastAPI everywhere, Anthropic SDK, uvicorn. Pre-Render fossils that mislead onboarding.
8. **4 dependencies in `requirements.txt` have ZERO LIVE imports**: `feedparser`, `httpx`, `openpyxl`, `pandas` (the last two used only in legacy `tools/benchmark_sources_vs_excel.py`). Bloated install + unclear truth about HTTP-client choice.
9. **Duplicate `canonicalize_url` in two modules** (`pipeline/normalization.py:35` and `pipeline/http_utils.py:236`) with subtly different behavior. Whoever calls one rather than the other gets different dedup results.
10. **No Pydantic schema validation at FastAPI boundaries**. Every POST handler does `payload = await read_json(request); name = str(payload.get("name") or "")` — and `read_json` itself silently returns `{}` on parse failure (`web_app/app.py:493-499`). Validation by `.get()` is not validation.

## Architectural mental model

A FastAPI single-process app on Render that scrapes/aggregates Brazilian political news (RSS, Google News, WordPress APIs, sitemaps, archives) about four candidates centered on Vereador Flávio Valle, deduplicates by URL, groups related articles into "stories", and serves both a public dashboard (`index.html` + pre-computed JSON in `assets/`) and a coworker admin UI (`/admin` with password). Persistence is local SQLite (`data/clipping.db`) gzipped to Supabase on every mutation because Render's filesystem is ephemeral. The `pipeline/` package orchestrates collect→fetch→dedup→match→story-group; `web_app/jobs.py` runs ingestion in a daemon thread spawned from a FastAPI POST and persists progress events to SQLite. There is **no scheduler** — coworkers click "Rodar atualização".

The codebase was forensically reconstructed from Codex session logs after a Windows SSD wipe (see `historical/RECOVERY_NOTES.md`). The reconstruction is complete and isolated cleanly into `historical/` and `raw_recovery/`. The LIVE code is free of recovery markers but inherits the volume produced during recovery — five files >700 LOC, two of them >1500. Active feature work is concentrated on the human-classification feature (`classifications`, `categories`, `mentions` tables) and on stabilizing the live runner UI for coworkers, with `Atlas` (Codex) and `Iris` (Claude Code) coordinating via `md documents/`. There is no CI; deployment is a Render git-push.

## Findings

| ID | Category | File:Line | Severity | Effort | Description | Recommendation |
|---|---|---|---|---|---|---|
| F001 | Security | web_app/app.py:222 | Critical | S | **[VERIFIED LIVE 2026-05-05]** `start_update` (POST `/api/update/start`) has no `require_admin(request)` call — only `JobConflict`/`ValueError` handling. Anyone hitting the URL can trigger an ingestion job. Live curl on `/api/update/cancel` (sibling endpoint, same pattern) returned 409 without auth — same protocol applies here. | Add `require_admin(request); require_csrf(request)` as first lines of handler. |
| F002 | Security | web_app/app.py:236 | Critical | S | **[VERIFIED LIVE 2026-05-05]** `cancel_update` (POST `/api/update/cancel`) takes no Request param and has no auth check. Live curl returned HTTP 409 + `{"detail":"no_active_job"}` without auth — handler ran. | Add `request: Request` param, then `require_admin(request); require_csrf(request)`. |
| F003 | Security | web_app/app.py:248 | Critical | S | **[VERIFIED LIVE 2026-05-05 by analogy to F002]** `start_export` (POST `/api/export`) has no auth check. Same handler pattern as `cancel_update` which was directly verified to bypass. | `require_admin(request); require_csrf(request)`. |
| F004 | Security | web_app/app.py:307 | Critical | S | **[VERIFIED LIVE 2026-05-05 by analogy]** `add_target` (POST `/api/targets`) has only `ensure_target_mutations_allowed()` (a "no-job-running" rate guard, not auth). | Add `require_admin(request); require_csrf(request)` before line 309. |
| F005 | Security | web_app/app.py:326 | Critical | S | **[VERIFIED LIVE 2026-05-05 by analogy]** `update_target` (PATCH `/api/targets/{key}`) — same pattern as F004. | Same fix. |
| F006 | Security | web_app/app.py:338 | Critical | S | **[VERIFIED LIVE 2026-05-05 by analogy]** `archive_target` (POST `/api/targets/{key}/archive`) — same pattern. | Same fix. |
| F007 | Security | web_app/app.py:350 | Critical | S | **[VERIFIED LIVE 2026-05-05 by analogy]** `restore_target` (POST `/api/targets/{key}/restore`) — same pattern, plus the only POST handler in the auth-guarded set that's `def` (sync), inconsistent with the rest. | Make `async def`, add `request: Request` and the auth+csrf calls. |
| F008 | Security | web_app/app.py:361 | Critical | S | **[VERIFIED LIVE 2026-05-05 by analogy]** `create_classification_category` (POST `/api/categories`) writes to category table with no auth. Atlas already exploited this in A-002 (created `AtlasLiveCheck` category without any auth). | Add `require_admin(request); require_csrf(request)`. |
| F009 | Security | web_app/app.py:402 | Critical | S | **[VERIFIED LIVE 2026-05-05 by analogy]** `upsert_classification` (POST `/api/classifications`) writes mention+classification rows with no auth. Anyone can poison the classification dataset. | Add `require_admin(request); require_csrf(request)`. |
| F010 | Performance + Auth policy | web_app/app.py:384 | High | S | **REVISED** after reading `assets/clipping.js:1902-1914`: this endpoint is consumed by the **public dashboard's "Live classifications overlay — public read, applies to every visitor so the static snapshot's classification chips stay current"**. Adding `require_admin()` would break the public dashboard. The real problem is the unbounded `limit=100000`. | Keep public (dashboard depends on it). Add `?limit=&offset=` (default 1000, max 5000). Add `ETag`/`If-None-Match` for cache. Or split: public `/api/classifications/dashboard` (curated, paginated, cached) + admin-only `/api/classifications/bulk` (full, paginated). The endpoint serving every visitor must stay fast. |
| F011 | Error handling | web_app/app.py:118-145 | High (downgraded from Critical 2026-05-05) | M | **[VERIFIED LATENT 2026-05-05]** Live `/healthz` returned `storage.enabled:true` and `dbExists:true` — production is NOT currently degraded. But the static finding stands: lifespan calls `artifact_store.download_current_artifacts()`, `archive_known_test_targets()`, `normalize_targets_file()`, `cancel_orphaned_active_jobs()`, `ensure_app_tables()` with no try/except. Next time Supabase auth expires or the network glitches, app silently boots degraded. | Wrap each step in try/except, log outcome at INFO on success and ERROR on fail with full traceback, set a process-level "degraded" flag so `/healthz` reports it. **Also surface in healthz response shape** so live verification works next time. |
| F012 | Error handling | pipeline/ingest.py:263-267 | Critical | S | **[VERIFIED LIVE 2026-05-05]** `is_recent_enough(value, ...)`: on `parse_iso(value)` exception, returns `True`. Live python check: `is_recent_enough('not-a-date')` → True; `is_recent_enough('')` → True; `is_recent_enough('2026-13-99T99:99:99')` → True. Malformed dates pass the recency filter and enter the pipeline. Inverts the intent of date filtering. | Change `return True` to `return False` and log the bad value at WARNING. Keep the `BACKFILL_START_DATE` floor below it. **Expect a one-time drop in article count after deploy** (articles silently passing the bad filter today will be filtered out). |
| F013 | Architectural decay | tools/export_mobile_snapshot.py:1 | High | L | 3267 LOC, 14 changes in 6mo. Top of debt-and-churn intersection. Mixes snapshot rendering, target merging, history preservation, deploy targets (was wired to Wix). | Extract: `snapshot/render.py` (HTML production), `snapshot/merge.py` (history merge), `snapshot/cli.py` (entry). Keep one tested, callable function at the top. |
| F014 | Architectural decay | pipeline/collectors.py:1 | Critical | L | 1519 LOC, ~40 functions across RSS, Google News, WordPress, Globo internal search, Veja Rio, Câmara, sitemap. Single module; collector additions force re-reading the whole file. | Split per source: `collectors/rss.py`, `collectors/google_news.py`, `collectors/wordpress.py`, `collectors/globo.py`, `collectors/sitemap.py`, `collectors/__init__.py` re-exporting. Move shared regexes/datetime parsing to `collectors/_common.py`. |
| F015 | Architectural decay | pipeline/database.py:1 | High | L | 1274 LOC `ClippingDB` class with 41 methods; only 9 documented. Mixes article CRUD, story grouping, mention/classification CRUD, category CRUD, runtime job events, schema migrations. | Split: `db/articles.py`, `db/stories.py`, `db/classifications.py`, `db/jobs.py`. Keep `ClippingDB` as a façade that composes them. Don't blow up the schema migration in the same file as queries. |
| F016 | Architectural decay | pipeline/ingest.py:1 | High | L | 1185 LOC orchestration. Module has no docstring; main flow buried among helpers. | Add module-level docstring describing the collect→fetch→match→dedup→story-group flow, then extract 200-LOC chunks (`_resolve_full_text`, `_choose_story`, `_run_collectors_loop`) into siblings. |
| F017 | Architectural decay | web_app/jobs.py:1 | Medium | M | 736 LOC `JobManager` + helpers (secret masking, state machine). Single file; difficult to test pieces in isolation. | Split: `jobs/manager.py` (state machine), `jobs/secrets.py` (`sanitize_payload`/`redact_secret_text`), `jobs/runtime.py` (`run_export_snapshot`, `run_ingestion_runner`). |
| F018 | Consistency rot | pipeline/normalization.py:35 vs pipeline/http_utils.py:236 | High | M | Two `canonicalize_url(...)` functions with different behavior (one normalizes + sorts query params; the other is port-aware). Whichever is called first wins for that caller. | Pick one canonical function, delete the other, update imports. Add a docstring stating exactly what is and isn't preserved. |
| F019 | Consistency rot | web_app/storage_bridge.py uses `requests`; `pipeline/http_utils.py` uses `urllib`; `httpx` is in `requirements.txt:5` but never imported | High | M | Three HTTP clients in scope, no rule about which goes where. | Document policy in `docs/PIPELINE.md`: "stdlib `urllib` for collectors (no async needed), `requests` for Supabase ops". Remove `httpx>=0.27.0` from requirements.txt — it's dead weight. |
| F020 | Consistency rot | run_ingestion.py:19 | Low | S | Logger uses `datetime.now()` (naive) while collectors use `datetime.now(timezone.utc)`. Cosmetic but it's the kind of drift that bites later. | `from datetime import timezone; datetime.now(timezone.utc).strftime(...)`. |
| F021 | Type & contract debt | web_app/app.py:259, 308, 327, 339, 362, 403 | High | M | All POST/PATCH handlers do `payload: dict[str, Any] = await read_json(request)` then probe `payload.get("title")`, `payload.get("targetKeys") or payload.get("target_keys")`, etc. No FastAPI body validation. Compounds F022. | Define Pydantic models per endpoint (`ManualStoryRequest`, `CreateTargetRequest`, `UpdateTargetRequest`, `ClassifyRequest`, etc.) and replace `request: Request` with the model. FastAPI gets you 422 on bad input for free. |
| F022 | Error handling | web_app/app.py:493-499 | High | S | `read_json` swallows JSON parse exceptions and falls back to `json.loads(raw) if raw.strip().startswith("{") else {}` — so a body that doesn't start with `{` becomes `{}` silently. Caller can't tell empty-payload from invalid-payload. | Remove the fallback. Raise `HTTPException(400, "invalid_json")` on parse failure. |
| F023 | Error handling | web_app/storage_bridge.py:82-84, 116-117, 124-125, 172-173, 186-187, 218-219 | High | S | Six `except (RequestException\|OSError\|sqlite3.Error): return False/b""` with **no logging**. Supabase auth expiring or network glitching makes the app silently lose every uploaded artifact. | Before each `return False`, `logging.warning("storage_bridge.<op> failed: %s (path=%s)", exc, ...)`. Surface in `/healthz`. |
| F024 | Error handling | pipeline/ingest.py:1011-1012 | High | S | WordPress collector wrapped in `except Exception: batch = []`. If the site is down or returns malformed JSON, the entire site quietly contributes zero articles. | `logging.warning("wordpress collector for %s failed: %s", base_url, exc)` and continue. Add a pipeline-summary counter for `failed_collectors`. |
| F025 | Error handling | pipeline/ingest.py:607-609 | High | M | `fetch_full_article_text` fallback: only logs the Google-redirect cert-fail special case; everything else swallowed and `full_text = candidate.snippet or candidate.title`. Matcher then runs on a snippet pretending to be full text. | Log all exceptions at WARNING with `(source, url, type(exc).__name__)`. Add a `degraded_text=True` flag on the candidate so downstream knows. |
| F026 | Error handling | pipeline/ingest.py:122-124 | Medium | S | `cancel_check()` callback wrapped in `except Exception: return False` — exception in the cancel signal is treated as "no cancel". Edge case: cancel sets a flag in a way that raises (rare but possible) and ingestion runs to completion. | Log the exception once (not per-iteration), but yes return False — the alternative is worse. Add a `cancel_check_errors` counter. |
| F027 | Error handling | pipeline/database.py:541, 570, 593 | Medium | S | Three loop bodies use `except Exception: continue` — corrupt rows skipped silently. Hard to know if the DB has data integrity issues. | Log row id + exception type at WARNING (rate-limited to N per run to avoid spam). |
| F028 | Error handling | pipeline/ingest.py:379-380 | Medium | S | `db.update_story(story_id, temperature=...)` wrapped in `except Exception: db.update_story(story_id)` — temperature recompute silently fails, story gets stale temperature. | Log at WARNING. Don't drop the temperature update — the silent fallback lets temperature go stale forever. |
| F029 | Error handling | pipeline/http_utils.py:25, 32, 43, 129, 141, 201, 232, 258, 329, 387 | Medium | M | 10 silent `except Exception:` in HTTP utilities (SSL fallback, Google redirect token decode, URL parsing). Each returns sentinel (empty string/None/url/False). Production crawl failures are invisible. | At minimum log the SSL fallback and the Google-decode cache-miss path. The URL-parse-failure paths are defensible (ignore unparseable input) — annotate with `# noqa: BLE001 - silent by design`. |
| F030 | Performance | web_app/app.py:386 | Medium | S | `get_classifications_with_context(limit=100000)` loads up to 100k rows in one shot on every GET; serialized to JSON for the wire. Memory spike + slow response. | Paginate: default `limit=500`, accept `?offset=&limit=`, cap at 5000. |
| F031 | Performance | web_app/jobs.py:323-338 | Low | M | `run_export_snapshot` uses `subprocess.run(...)` (synchronous) with `EXPORT_TIMEOUT_SECONDS`. The thread that called it blocks while the export runs; UI progress events stop emitting during the blocking window. | `subprocess.Popen` + read stdout in chunks, emitting progress events. Or split export into smaller chunks called in-process. |
| F032 | Test debt | tests/test_admin_ui.py:1 | Medium | M | 785 LOC; tests login flow, classification edits, target mutations, JWT, all in one file. Hard to debug isolated failures. | Split: `test_admin_login.py`, `test_admin_targets.py`, `test_admin_classifications.py`. |
| F033 | Test debt | tests/test_targets_jobs.py:1 | Medium | M | 809 LOC; mixes job runner state machine, target persistence, cancellation. | Split: `test_jobs_state.py`, `test_targets_persistence.py`, `test_jobs_cancellation.py`. |
| F034 | Test debt | tests/test_collectors_restore.py, test_f2t8_f3t1.py, test_f3_tools.py, test_f4_validation.py, test_ingest_restore.py, test_wave2_pipeline_restore.py, test_wave25_original_restore.py | Low | S | Seven recovery-era tests (F-task naming from `historical/PLAN_Clipping_Reconstruction.md`). They pass but exercise reconstruction completeness, not current code paths. They run on every `pytest` invocation. | Move to `tests/historical/` with a conftest skip-by-default; add `pytest -m historical` to opt in. Keep `test_forensic_audit_completeness.py` since it tests current source against the recovery oracle. |
| F035 | Test debt | pipeline/ingest.py and pipeline/database.py | High | L | The two highest-churn LIVE files (12-13 commits/6mo) have no dedicated unit tests — only indirect coverage via `test_targets_jobs.py` and `test_export_mobile_snapshot_pages.py`. No coverage tooling is configured. | Add `pytest-cov`, set `--cov=pipeline.ingest --cov=pipeline.database --cov-fail-under=70` in CI. Write targeted tests for `is_recent_enough`, `dedupe_candidates`, `choose_story`, `insert_article_if_new`, `story_article_stats`. |
| F036 | Test debt | (codebase-wide) | Medium | M | No end-to-end smoke test. A regression that breaks the full ingestion→export→dashboard flow would only surface in production. | Add `tests/test_e2e_smoke.py`: run a 1-target/1-day ingestion against a fixture DB, then `tools/export_mobile_snapshot.py`, then assert `assets/clipping-data.json` contains the seeded articles. |
| F037 | Dep & config debt | requirements.txt:1 | Low | S | `feedparser>=6.0` declared but **zero LIVE imports** (collectors use `xml.etree.ElementTree`, confirmed via abs-path grep on 2026-05-04). Dead dep. | Move to a `requirements-legacy.txt` if `tools/benchmark_sources_vs_excel.py` (LEGACY) still imports it indirectly. Otherwise remove from `requirements.txt`. **Test pip install before pushing**. |
| F038 | Dep & config debt | requirements.txt:5 | Low | S | `httpx>=0.27.0` declared but **zero imports anywhere** (confirmed via abs-path grep). Dead dep. | Remove from `requirements.txt`. Lower risk than F037 because nothing imports it. |
| F039 | Dep & config debt | requirements.txt:6,7 | Low | S | `pandas>=2.0` and `openpyxl>=3.0` are imported only in `tools/benchmark_sources_vs_excel.py` — classified LEGACY in `AUDIT_GROUND_TRUTH.md`. Dead from LIVE perspective. | **Do NOT just remove** — the legacy script breaks. Split into `requirements-dev.txt` (pandas, openpyxl, future ruff/vulture/pip-audit) and document in `docs/PIPELINE.md` that benchmark scripts need `pip install -r requirements-dev.txt`. |
| F040 | Dep & config debt | render.yaml:11 | Medium | S | `PYTHON_VERSION=3.14.3` pins to a specific patch. If Render rebuilds the image and 3.14.3 isn't available (e.g., 3.14.4 ships and 3.14.3 is rotated out), startCommand may fail or silently roll forward. | Pin minor only: `PYTHON_VERSION=3.14`. Document the choice in README. |
| F041 | Dep & config debt | render.yaml + web_app/config.py | Low | S | Code consumes env vars not declared in render.yaml: `CLIPPING_ALLOW_LOCAL_WRITES`, `CLIPPING_DB_PATH`, `CLIPPING_LIVE_BASE_URL`, `CLIPPING_LIVE_EXPECT_MARKER`, `CLIPPING_LIVE_ALLOW_MUTATE`. They're local/CLI-only but undocumented. | Add a comment block in `render.yaml` listing the local-only env vars, or create `.env.example` at repo root. |
| F042 | Dep & config debt | (toolchain) | Low | S | No `pip-audit` / `vulture` / `ruff` in requirements or any CI step. Vulnerabilities and dead code go unchecked. | Create `requirements-dev.txt` with `pip-audit`, `ruff`, `vulture`, `pytest-cov`. Wire `pip-audit` and `ruff check` into a pre-commit hook or a Render build step (with `|| true` initially to gather signal without blocking). |
| F043 | Dep & config debt | conftest.py:1 | Low | S | 207 bytes, registers one `@pytest.mark.live` marker. Could host shared fixtures. | Add fixtures: `temp_db()`, `mock_supabase()`, `live_test_url_or_skip()`. Optional. |
| F044 | Documentation drift | README.md:137-142 | High | S | `## Requirements` block lists only `feedparser>=6.0` and `requests>=2.28`, then says "Most logic uses the standard library (`urllib`, `xml.etree`, `sqlite3`, `feedparser`, etc.)". Both claims are pre-Render fossils. Real `requirements.txt` has 8 deps and the app is FastAPI. | Replace with: "Production deps: see `requirements.txt`. Stack: FastAPI + Supabase + SQLite. RSS uses stdlib `xml.etree`; HTTP uses stdlib `urllib` for collectors and `requests` for Supabase." |
| F045 | Documentation drift | web_app/app.py | High | M | 19 top-level functions (route handlers + helpers); only `get_csrf` (line 291) has a docstring. FastAPI auto-doc is disabled (`docs_url=None, redoc_url=None`) — so no OpenAPI either. | Add a one-line docstring per route handler describing input contract, auth requirement, and return shape. Consider re-enabling `docs_url="/docs"` behind admin auth. |
| F046 | Documentation drift | pipeline/database.py | High | L | `ClippingDB` has 41 methods; only 9 with docstrings. The undocumented ones include critical ones (`insert_article_if_new`, `story_article_stats`, `update_story`). | Pass once: add 1-2 line docstrings to public methods, listing args, returns, and side effects (Supabase upload? mutation-only?). |
| F047 | Documentation drift | pipeline/ingest.py:1 | High | M | Module has zero top-level docstring. The orchestration order (collect→filter→match→fetch→story-group) is implicit. | Add module docstring; sketch the flow as ASCII. The skill is allowed to embed diagrams in code per ehmo-style audits. |
| F048 | Documentation drift | docs/PIPELINE.md vs current code | Medium | M | Spot-checks show alignment but no audit was performed. Given pipeline/ingest.py and collectors.py have ~25 commits in 6 months, drift is likely. | When fixing F047, re-read PIPELINE.md and reconcile. |
| F049 | Architectural decay | office_docs/ (91 MB, 77 files) | High | S | **[VERIFIED LIVE 2026-05-05]** 77 files (.pptx/.xlsx/.docx, valid OOXML), all share mtime `2026-03-31 12:19:43` (bulk-import signature, not individual edits). Zero references anywhere in `/home/otavio/Documents/vscode/` outside this audit's own outputs (TECH_DEBT_AUDIT.md, AUDIT_GROUND_TRUTH.md, ATLAS_IRIS_ASYNC.md, ATLAS_CLAUDE_COORDINATION.md). Confirmed accidentally-committed bulk import. | `git mv office_docs/ legacy_assets/office_docs/` (preserves history; safer than `git rm`). Add `legacy_assets/` to `.gitignore` going forward. If clone bloat matters, IF Otavio approves, consider `git filter-repo --invert-paths --path office_docs/` (destructive — needs Render cache flush + everyone re-clone). **NEVER** `git rm` blindly. |
| F050 | Architectural decay | data/reports/ (HTML snapshots in git) | Medium | S | `data/reports/clipping_mobile_snapshot_all_stories.html`, `clipping_historias_completo.html`, `clipping_completo_novo_estilo.html` show 6-8 changes in 6mo (top-25 churn list). They're build artifacts being committed. | Add `data/reports/` to `.gitignore`. Move sample/expected outputs (if any are needed for tests) to `tests/fixtures/`. |
| F051 | Architectural decay | server.py (436 LOC), serve_static.py (33 LOC) | Low | S | Both are LEGACY (not in `render.yaml` startCommand, no imports). Their presence at repo root makes them look LIVE to a casual reader. | Move to `legacy_scripts/` with a brief README explaining why they're kept. **NEVER delete** — `server.py` was forensically reconstructed from Codex fragments and represents non-trivial recovery work; if production ever needs static-export fallback, this is the artifact. |
| F052 | Layering | web_app/app.py:35 | Medium | S | `from pipeline.database import ClippingDB` — `web_app` reaches into `pipeline` for the DB class instead of going through `web_app/db_admin.py` (which is the existing wrapper). | Add `ClippingDB` (or a subset of its API) to `web_app/db_admin.py` exports and import from there. Keep `pipeline/database.py` as the implementation; `web_app` doesn't need to know it exists. |
| F053 | Architectural decay | tools/build_antisemitism_comparison_report.py (1358 LOC) | Low (LEGACY) | S | Standalone one-off report builder; classified LEGACY. Not in scope per project override, but flagged here because its size makes it visually look LIVE in `tools/`. | Move to `legacy_scripts/` or `historical/tools/`. |
| F054 | Test debt | tests/test_pages_performance.py, tests/test_bak_comparison.py | Low | S | Both contain measurement code without `assert` statements (per agent inspection of test class bodies). They run as part of the suite but never fail — performance regressions go undetected. | Either add tolerance assertions ("DOM nodes < 3000", "render time < 500ms") or move to `tests/benchmarks/` with a separate CLI invocation. |
| F055 | Architectural decay | tools/run_parallel_non_direct_ingestion.py | Low | S | **[VERIFIED LIVE-DORMANT 2026-05-05]** Resolved: this is LIVE (imports `pipeline.collectors`, `pipeline.database`, `pipeline.ingest`, `pipeline.settings`; documented in `docs/PIPELINE.md`). Real runs in `data/parallel_runs/` confirm active use, but **last invocation was 2026-04-08 (~4 weeks before audit)**. Script may be becoming obsolete in favor of `tools/export_mobile_snapshot.py --merge-from index.html` workflow. | Add docstring at top per F046. Open follow-up for Otavio (not blocking): if no backfill run since April 8, decide within next sprint whether to keep or migrate to the merge-from-index path. |
| F056 | Consistency rot | pipeline/ingest.py:213-225 (`parse_date_boundary`) vs pipeline/ingest.py:206-210 (`parse_iso`) | Medium | S | `parse_date_boundary` uses naive `datetime.strptime("%Y-%m-%d")` while `parse_iso` returns timezone-aware datetimes. Filtering compares aware-to-naive, which Python rejects with TypeError — caught silently by F012 (`is_recent_enough` `return True` fallback). | Make both return tz-aware datetimes (UTC). Then F012's bug becomes visible because the silent-True will go away. |
| F057 | Security | render.yaml secrets | Low | — | All 5 secrets correctly marked `sync: false` and consumed correctly in code. | No action. (Listed for transparency.) |

## Top 5 — fix these first

### 1. Lock the auth bypass (F001-F009): one PR, ~30 minutes

```python
# web_app/app.py — apply pattern to every POST/PATCH/DELETE handler
@app.post("/api/update/start")
async def start_update(request: Request) -> JSONResponse:
    require_admin(request)
    require_csrf(request)
    payload = await read_json(request)
    # ...rest unchanged
```

For `cancel_update` (currently no `request` param), add it. For `restore_target` (currently `def`), make it `async def` with a `request: Request` param.

After applying, audit `tests/test_admin_ui.py` and `tests/test_targets_jobs.py` — tests that POST to these endpoints without a session cookie will now get 401, and that's the right new behavior. Update tests to authenticate first.

### 2. Fix lifespan silent failure (F011): one wrap, ~15 minutes

```python
# web_app/app.py:117-145
@asynccontextmanager
async def lifespan(_: FastAPI):
    degraded = []
    for step_name, step in [
        ("download_artifacts", artifact_store.download_current_artifacts),
        ("archive_test_targets", archive_known_test_targets),
        ("normalize_targets", normalize_targets_file),
        ("ensure_tables", lambda: ensure_app_tables(db_path())),
        ("cancel_orphans", cancel_orphaned_active_jobs),
    ]:
        try:
            step()
        except Exception:
            logging.exception("lifespan step failed: %s", step_name)
            degraded.append(step_name)
    app.state.degraded = degraded  # surface in /healthz
    yield
```

Then update `/healthz` (line 205) to include `"degraded": app.state.degraded`.

### 3. Fix `is_recent_enough` (F012): one line, 5 minutes

```python
# pipeline/ingest.py:263-275
def is_recent_enough(value: str, *, date_from=None, date_to=None) -> bool:
    try:
        dt = parse_iso(value)
    except Exception:
        logging.warning("is_recent_enough: failed to parse %r", value)
        return False  # was: return True
    # ...
```

This will reveal articles that have been silently entering the pipeline with bad dates. Expect a one-time drop in article count after deploy.

### 4. Stop the silent storage_bridge (F023): six log lines, ~10 minutes

Add `logging.warning("storage_bridge.<op> failed: %s", exc)` before each `return False` in `web_app/storage_bridge.py:82-219`. Then add a Render log alert for the string `storage_bridge.` to know when Supabase glitches.

### 5. Move `office_docs/` to `legacy_assets/` (F049): two commits, ~10 minutes — but verify usage with Atlas FIRST

**DO NOT** `git rm` — Iris cannot tell from grep whether anyone uses these 91 MB locally. Step ordering:

1. Iris writes Q-007 in `ATLAS_IRIS_ASYNC.md` asking Atlas: "is anything in `office_docs/` referenced by any local script, import, or workflow?"
2. After Atlas's A-007: if confirmed unused, `git mv office_docs/ legacy_assets/office_docs/` (preserves history, makes status visible) and add `legacy_assets/` to `.gitignore` going forward.
3. Only after that, IF Otavio decides clone bloat matters, consider `git filter-repo --invert-paths --path office_docs/` (destructive — Atlas + Otavio coordinate; Render needs cache flush; everyone re-clones).

The audit's biggest visual quick win, but not a safe blind action.

## Quick wins

Ordered by safety (top = zero risk; bottom = needs Atlas live verify before pushing).

- [ ] **F044**: Rewrite `README.md:137-142` Requirements block to match reality. Pure docs; no code risk.
- [ ] **F050**: Add `data/reports/` to `.gitignore`. Stops committing build artifacts. Existing committed files stay until next `git rm --cached` (don't blanket rm).
- [ ] **F020**: One `timezone.utc` fix in `run_ingestion.py:19`. Cosmetic.
- [ ] **F040**: Change `PYTHON_VERSION=3.14.3` → `3.14` in `render.yaml`. Render redeploys; verify deploy goes green via Atlas.
- [ ] **F038**: Remove `httpx>=0.27.0` from `requirements.txt`. Zero imports anywhere; safest dep removal.
- [ ] **F034**: Move 7 recovery-era tests into `tests/historical/` with `pytest -m historical` opt-in. Faster local pytest. **NEVER `git rm`** — they're forensic completeness checks; preserve them in `tests/historical/`.
- [ ] **F051**: `git mv server.py serve_static.py legacy_scripts/`. Add a 5-line README inside `legacy_scripts/` explaining why they're kept. NEVER delete.
- [ ] **F037**: Move `feedparser` to `requirements-legacy.txt` (or remove if benchmark script doesn't need it). Run `pip install -r requirements.txt` in a fresh venv before pushing.
- [ ] **F039**: Split `pandas` + `openpyxl` into `requirements-dev.txt`. Document.
- [ ] **F012**: Fix `is_recent_enough` — one line. **High value but expect a one-time drop in article count after deploy** (articles with bad dates that were silently passing the filter will now be excluded). Atlas should verify article count before/after.
- [ ] **F011**: Wrap `lifespan` steps in try/except. Surface in `/healthz`. Atlas should verify `/healthz` shape before/after.
- [ ] **F049**: After Q-007 answer from Atlas, `git mv office_docs/ legacy_assets/`. NEVER `git rm` blindly.

## Things that look bad but are actually fine

- **`pipeline/http_utils.py:22 import certifi  # type: ignore`** — only blessed `# type: ignore` in the codebase. Defensive: certifi may not be installed but shouldn't crash imports. Keep.
- **`pipeline/database.py:536`, `web_app/db_admin.py:450,461,468` — `f"...IN ({placeholders})"` SQL** — looks like SQL injection but the `placeholders` string is generated from `", ".join("?" for _ in ids)`, with values passed parametrically as the second `.execute()` argument. Safe. (Listed because `rg "f\".*SELECT|UPDATE|DELETE"` flags it as a smell on first glance.)
- **Sync `def` route handlers in `web_app/app.py`** (`public_dashboard`, `update_status`, `list_targets`, etc.) — FastAPI runs these in a thread pool. For DB reads under 100ms it's actually faster than `async` because no event-loop overhead. Don't blanket-rewrite to `async def`.
- **`web_app/auth.py:63 except Exception: return None`** — silent on JSON parse failure during session decode. This is correct security behavior: a tampered cookie should fail closed without leaking why. Don't add user-facing logging here.
- **`web_app/app.py:66, 74 except TypeError`** — defensive bridge for a `db_admin.public_targets` signature mismatch. Looks like duck-typing pyramid; in practice it's a one-line shim that should be deleted **once** `db_admin.public_targets` is confirmed to support the kwarg. Flag for cleanup but it's not a bug.
- **`web_app/storage_bridge.py:218 except sqlite3.Error: return b""`** — returning empty bytes on DB read error means the upload contains nothing rather than crashing the runner. Combined with F023 (add logging), this is acceptable defensive coding for a sync helper.
- **N+1 in `story_article_stats` (called from `pipeline/ingest.py:376`)** — the call only happens when creating new stories during ingestion (rare path). Dashboard pre-computes this elsewhere. Don't optimize a cold path.
- **`gzip.compress(payload, compresslevel=6)` synchronous in `web_app/storage_bridge.py:134`** — payload is the SQLite DB, currently <50 MB. Compression takes <1s. Fine.
- **`feedparser` in README "stack" line** — the README claims it's used; reality is collectors swapped to `xml.etree`. The README claim is wrong (F044) but the rg scan that says feedparser is unused is *correct*. Don't add it back.
- **`md documents/RENDER_RESTART_NOTES.md` having 8 changes despite "notes" name** — this is the active operational log for Render restarts (Q-004 etc.). It's named "notes" but it's a coordination doc. Don't archive.

If this section is empty, the audit is shallow. It has ten items; the audit is fine.

## Open questions — resolved (2026-05-05)

- ✅ **Q1** — `tools/run_parallel_non_direct_ingestion.py`: **LIVE**, not LEGACY. `docs/PIPELINE.md` documents it (`--target flavio_valle --max-workers 12`). It's Otavio's parallel-backfill helper. AUDIT_GROUND_TRUTH updated. Still missing docstrings (F046 covers).
- ✅ **Q2** — `tools/prepare_wix_clipping_snapshot.py`: **LEGACY**. Last commit `5586b9c feat: publish pages-first clipping bundle` confirms the Wix path was superseded by the pages bundle. Zero "Wix" mentions in README, docs/, md documents/. Recommend `git mv` to `legacy_scripts/`.
- ✅ **Q3** (recovery tests) — Otavio's call: move to `tests/historical/` skip-by-default. Captured in F034 quick-win.
- ✅ **Q4** — `md documents/ATLAS_ORCHESTRATOR_HANDOFF.md`: **HISTORICAL**. Document's own header says: "this was Atlas's first rough checkpoint... Use these as the current entrypoints: ORCHESTRATORS_FRAMEWORK + GENERAL_UNDERSTANDING + RENDER_RESTART_NOTES". Move requires updating two referencers: `README.md:106-108` and `md documents/GENERAL_UNDERSTANDING_OF_OUR_GOALS_IN_THIS_PROJECT.md`.
- ✅ **Q5** — `/api/classifications` GET: **PUBLIC INTENTIONAL** (not auth bypass). `assets/clipping.js:1902-1914` comment confirms: *"Live classifications overlay — public read, applies to every visitor so the static snapshot's classification chips stay current"*. F010 has been revised: keep public, add pagination. Adding `require_admin()` here would break the public dashboard for every visitor.
- ✅ **Q6** (CI) — confirmed: no `.github/`, no Render build-hook tests. All testing is local-then-push. F042 (`requirements-dev.txt` with pip-audit/ruff/vulture/pytest-cov) is the actionable.

## Open questions — still open

- **Q-007** (queued to Atlas via `md documents/ATLAS_IRIS_ASYNC.md`): Atlas needs to live-verify F001-F012 against `https://clipping-project.onrender.com/`. Iris cannot do this from the firewalled sandbox. The Q includes specific `curl` commands per finding.
- **office_docs/ usage** (part of Q-007): Atlas needs to confirm whether anything in `office_docs/` (91 MB) is referenced by any local script, manual workflow, or external sheet that depends on these specific files. Iris's grep says no, but Iris cannot see Otavio's local FS.
- **Atlas's current sprint vs this audit's P0 list**: Atlas (per A-006, 2026-05-01) is in the "live news clipping runner" sprint — restore /clipping parity, remove web-only date cap, move Bernardo Rubião to secondary, add cancel/freshness, verify on Render. **This audit was scoped to tech debt, not Atlas's sprint.** Some overlap (F010 affects the dashboard Atlas is repairing; F011 affects startup which Atlas's classification-persistence work cared about) but not aligned. Otavio decides whether the P0 fixes from this audit interrupt Atlas's sprint or queue after.

---

**Appendix: AUDIT_GROUND_TRUTH classification (referenced by F034, F049, F051, F053, F055, etc.)**

See [`AUDIT_GROUND_TRUTH.md`](AUDIT_GROUND_TRUTH.md) for the full LIVE/LEGACY/UNCLEAR table that this audit was scoped against. Per the project override of the tech-debt-audit skill, LEGACY items were skipped except where they have security implications.
