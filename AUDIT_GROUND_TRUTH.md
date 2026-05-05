# AUDIT_GROUND_TRUTH

Generated: 2026-05-04 by Iris.
Updated: 2026-05-05 — Q1, Q2, Q4 resolutions absorbed (see "Resolutions log" at bottom).
Phase 1.7 of /tech-debt-audit (project override).

Classifies every top-level file/dir in this repo as **LIVE** (reachable from production entry points), **LEGACY** (recovery-era, deprecated, or path-pattern matched), or **UNCLEAR** (flagged in Open Questions). Phase 2 of the audit skips LEGACY items unless they expose security risks.

## Entry points

- **Production (Render)**: `render.yaml` startCommand → `uvicorn web_app.app:app` → [`web_app/app.py`](web_app/app.py)
- **Local CLI (Otavio)**: [`run_ingestion.py`](run_ingestion.py)
- **Tests**: pytest via [`conftest.py`](conftest.py) over [`tests/`](tests/)
- **Tool scripts**: invoked manually or by `web_app/jobs.py` (export only)

## Classification table

| Path | Class | Reason |
|---|---|---|
| `web_app/` | **LIVE** | All 6 files imported transitively by `web_app/app.py` (FastAPI entry) |
| `pipeline/` | **LIVE** | Imported by `web_app/jobs.py` and `run_ingestion.py` |
| `assets/clipping.css`, `assets/clipping.js` | **LIVE** | Mounted by `web_app/app.py:149` via StaticFiles |
| `assets/clipping-data.json` (1.4M), `assets/clipping-raw-texts.json` (4.4M) | **LIVE** | Runtime data served by dashboard |
| `index.html` | **LIVE** | Served by `web_app/app.py:163` |
| `run_ingestion.py` | **LIVE** | Documented CLI entry in README |
| `render.yaml` | **LIVE** | Render Blueprint |
| `requirements.txt` | **LIVE** | buildCommand `pip install -r requirements.txt` |
| `conftest.py` | **LIVE** | pytest configuration |
| `tests/test_admin_ui.py`, `test_targets_jobs.py`, `test_export_mobile_snapshot_pages.py`, `test_pages_performance.py`, `test_f5_live_validation.py`, `test_forensic_audit_completeness.py`, `test_live_audit_script.py`, `test_sprint_regression_harness.py`, `test_bak_comparison.py` | **LIVE** | Test code under active development (5+ recent commits each) |
| `tests/test_collectors_restore.py`, `test_f2t8_f3t1.py`, `test_f3_tools.py`, `test_f4_validation.py`, `test_ingest_restore.py`, `test_wave25_original_restore.py`, `test_wave2_pipeline_restore.py` | **UNCLEAR** | Recovery-phase tests (F2-F5 task IDs match `historical/PLAN_Clipping_Reconstruction.md`); kept around for forensic-audit-completeness, but not exercised by current development. Flag in Open Questions. |
| `tools/export_mobile_snapshot.py` | **LIVE** | Imported by `web_app/jobs.py`, `tests/test_targets_jobs.py`, `tools/prepare_wix_clipping_snapshot.py` |
| `tools/classify_articles.py` | **LIVE** | AI batch categorizer added recently (commit 489c639); standalone CLI |
| `tools/live_audit.py` | **LIVE** | Production audit script; has companion test `tests/test_live_audit_script.py` |
| `tools/prepare_wix_clipping_snapshot.py` | **LEGACY** (resolved 2026-05-05) | Last commit `5586b9c feat: publish pages-first clipping bundle` — pages bundle replaced Wix path. Zero "Wix" mentions in README/docs/md documents. Recommend `git mv` to `legacy_scripts/`. |
| `tools/run_parallel_non_direct_ingestion.py` | **LIVE** (resolved 2026-05-05) | Documented in `docs/PIPELINE.md` with example invocation (`--target flavio_valle --max-workers 12`). Otavio's parallel-backfill helper. Missing docstrings (covered by F046). |
| `tools/validate_oracle.py` | **LEGACY** | Validates `data/test_oracle.json` against `historical/VALIDATION_ORACLE.md`; recovery-era forensics |
| `tools/benchmark_sources_vs_excel.py` | **LEGACY** | "vs Excel" implies pre-Render baseline benchmark; last modified Mar 31; standalone |
| `tools/build_antisemitism_comparison_report.py` | **LEGACY** | 1358 LOC standalone script; one-off report builder; not in production path |
| `data/clipping.db` | **LIVE** | Runtime SQLite; gitignored but present locally |
| `data/targets.json` | **LIVE** | Loaded by `web_app/db_admin.py` |
| `data/test_oracle.json` | **LEGACY** | Recovery-era oracle data, paired with `tools/validate_oracle.py` |
| `data/backfill_*.log`, `data/backfill_*.txt`, `data/parallel_runs/`, `data/backups/`, `data/tmp_*.db`, `data/reports/` | **LEGACY** | Local artifacts; .gitignore covers `data/*.log`, `data/backfill_*.txt`, `data/tmp_*.db`, `data/parallel_runs/`, `data/backups/`. `data/reports/` HTML snapshots are not gitignored — they appear in git changelog (3 entries in top-25 churn). |
| `docs/PIPELINE.md`, `docs/LONG_TERM_GOALS_FOR_THE_CLIPPING_ONLINE_PROJECT.md` | **LIVE** | Linked from README as current operational reference |
| `md documents/ATLAS_CLAUDE_COORDINATION.md`, `ATLAS_IRIS_ASYNC.md`, `IRIS_OPERATING_RULES.md`, `ORCHESTRATORS_FRAMEWORK_FOR_THE_CLIPPING_PROJECT.md`, `GENERAL_UNDERSTANDING_OF_OUR_GOALS_IN_THIS_PROJECT.md` | **LIVE** | Active orchestration coordination (8-14 changes each in last 6mo); README links them as current |
| `md documents/ATLAS_ORCHESTRATOR_HANDOFF.md` | **LEGACY** (resolved 2026-05-05) | The document's own header confirms: "this was Atlas's first rough checkpoint... Use these as the current entrypoints: ORCHESTRATORS_FRAMEWORK + GENERAL_UNDERSTANDING + RENDER_RESTART_NOTES". Recommend `git mv "md documents/ATLAS_ORCHESTRATOR_HANDOFF.md" historical/ATLAS_ORCHESTRATOR_HANDOFF.md`. **Move requires** updating two referencers: `README.md:106-108` and `md documents/GENERAL_UNDERSTANDING_OF_OUR_GOALS_IN_THIS_PROJECT.md`. |
| `md documents/RENDER_RESTART_NOTES.md` | **LIVE** (resolved 2026-05-05) | 8 changes in 6mo confirms it's the active operational log for Render restarts (Q-004 etc.). The "notes" name is misleading — it's the Render coordination doc. Keep. |
| `historical/` (11 markdown files) | **LEGACY** | `historical/README.md:3-4` explicit: "**not** active guidance for the current project" |
| `raw_recovery/corrupted_root/`, `raw_recovery/corrupted_tools/` (12 files) | **LEGACY** | Path matches `*recovery*`. `corrupted_*` prefix self-documents. No imports |
| `server.py` (436 LOC) | **LEGACY** | Standalone HTML snapshot generator. NOT in `render.yaml` startCommand. Last modified Mar 31. Header comment says recovered from Codex fragments. |
| `serve_static.py` (33 LOC) | **LEGACY** | SimpleHTTPRequestHandler fallback. NOT in `render.yaml`. No imports anywhere. |
| `office_docs/` (91 MB, 70+ files) | **LEGACY** | **HARD LEGACY**. Filenames like `f424460288.pptx`, `f424660992.xlsx` are temp file hashes. NOT mentioned in README. NOT in `.gitignore`. NOT imported. NOT referenced by any tool. Cold corner — never touched in 6 months. Looks like accidental commit of MS Office temp files. Should be removed and gitignored. |
| `__pycache__/` at repo root | **LEGACY** | Build artifact; .gitignore covers it; if present, residual local cache |
| `.venv_playwright/` | **LIVE** | Local dev venv; .gitignore covers it; safe to ignore |
| `.claude/skills/clipping/SKILL.md` | **LIVE** | Active skill referenced in README |
| `.claude/skills/tech-debt-audit/SKILL.md` | **LIVE** | This skill (project override) |
| `.gitignore`, `.git/` | **LIVE** | VCS metadata |
| `README.md` | **LIVE** but **DRIFTED** | Active doc but lines 137-142 list only `feedparser` and `requests` as Requirements and claim "Most logic uses the standard library" — both contradicted by `requirements.txt` (8 deps) and `web_app/` (FastAPI). Pre-Render text. |

## Summary (after 2026-05-05 resolutions)

- **LIVE**: ~40 paths (web_app/, pipeline/, assets/, index.html, render.yaml, requirements.txt, conftest.py, run_ingestion.py, 9 active tests, **4 LIVE tools** including `run_parallel_non_direct_ingestion.py`, docs/, 5 active md documents incl. RENDER_RESTART_NOTES, runtime data)
- **LEGACY**: ~11 paths (`raw_recovery/`, `historical/`, `server.py`, `serve_static.py`, **`office_docs/` pending Q-007**, 4 legacy tools incl. `prepare_wix_clipping_snapshot.py`, `data/test_oracle.json`, `md documents/ATLAS_ORCHESTRATOR_HANDOFF.md`)
- **UNCLEAR**: ~7 paths (7 recovery-era tests still need decision — Otavio chose "move to tests/historical/ skip-by-default" on 2026-05-05; will be resolved by F034 fix)

## Resolutions log

- **2026-05-05** — Q1: `tools/run_parallel_non_direct_ingestion.py` → LIVE (documented in `docs/PIPELINE.md`).
- **2026-05-05** — Q2: `tools/prepare_wix_clipping_snapshot.py` → LEGACY (Wix path superseded by pages bundle per commit `5586b9c`).
- **2026-05-05** — Q4: `md documents/ATLAS_ORCHESTRATOR_HANDOFF.md` → LEGACY (own header says it's superseded; 2 referencers need update on move).
- **2026-05-05** — `md documents/RENDER_RESTART_NOTES.md` → LIVE confirmed (active operational doc despite "notes" name).
- **Pending Q-007** — `office_docs/` (91 MB) status: Atlas needs to confirm whether anything local references the contents. Currently kept as LEGACY in this table but Iris will not recommend `git mv` until Atlas's A-007.

## Critical observations from the ground truth

1. **`office_docs/` = 91 MB of git-tracked junk** — looks like an accidental commit of Word/Excel/PPT temp files (filenames are content hashes). Highest-priority quick win.
2. **README.md is drifted** — its "Requirements" and "Most logic uses the standard library" claims are pre-Render fossils. Already noted; will appear as a high-priority Documentation drift finding in Phase 2.
3. **Recovery-era surface is large but isolated** — `historical/` and `raw_recovery/` are clean separations. The risk lives in the 7 UNCLEAR recovery tests (`test_*_restore.py`, `test_f2t8_f3t1.py`, etc.) that may be exercised by CI and slowing test runs without providing real signal.
4. **`tools/` has 3 LEGACY scripts that the README does NOT call out** — easy to mistake for active code.
