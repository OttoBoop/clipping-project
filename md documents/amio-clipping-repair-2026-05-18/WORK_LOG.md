# Work Log - Amio Clipping Repair Loop

_Created 2026-05-18 by Amio/Codex. Append-only unless correcting a factual typo
in the current entry._

This log records what happened, what was verified, what was inherited, and what
the next loop must remember. It exists specifically because Otavio asked for a
log before implementation.

## 2026-05-18 - Documentation loop started

### User Prompt Anchors

Otavio's instructions that define this loop:

> "crie uma nova pasta no clipping project (e pelo amor de Deus, faça os ocmiits. Ele deve falar desses dois objetivos. Crie um .md com os objetivos de longo prazo, pra você se lembrar deles quando as coisas travam, e um segundo .md com um log do que você fez até agora."

> "Também notei que as notícias não estão sendo automaticamente salvas no site assim que são encontradas. Eu quero que assim que uma notícia seja encontrada, ela aparece na base em baixo do site."

> "Olha, tudo isso vai demandar mais perguntas. Coopere comigo para eu te explciar melhor os objetivos."

> "E tem um problema extra. Eu consegui adicionar um nome  e aí o filtro não funcionou. A porra dos sistemas não está conectado. Parte chave do loop é checar cada sistema, criando .mds próprios, e checando que as conexões funcionam."

> "Mano, na verda, que merda de plano é esse. Você não falou porra nenhuma dos .mds, dos loops. Tá cheio de coisa específica."

> "Você cirou um plano que é de implementação, não um plano pra criar os documentos de longo prazo, que vão permitir o loop, que vão permitir esse tipo de plano de curto prao."

> "quando eu mandar \"implement plan\", é pra você tar opronto para escrever os dois documentos, e depois começar o loop."

### Correction

I made the wrong move before this documentation pass. I treated the requested
plan as a direct implementation plan for site code. That was wrong because the
actual first deliverable was the loop memory:

- long-term goals;
- work log;
- short-term loop scaffold;
- connection checklist;
- commit/worktree discipline.

This log records that failure so the next agent does not repeat it.

### Inherited Worktree State

Fresh status at the start of this docs-first pass showed an already dirty
worktree on `master...origin/master`.

Tracked changes already present before this docs pass:

```text
 M README.md
 M assets/clipping-data.json
 M data/reports/performance_benchmark.md
 D docs/LONG_TERM_GOALS_FOR_THE_CLIPPING_ONLINE_PROJECT.md
 D docs/PIPELINE.md
 M "md documents/05-05-26-Iris-Shakira goals.md"
 M "md documents/Who_Is_Doing_What-WRITE_WHAT_YOU'RE_DOING_HERE.md"
 M pipeline/__pycache__/__init__.cpython-314.pyc
 M pipeline/__pycache__/collectors.cpython-314.pyc
 M pipeline/__pycache__/database.cpython-314.pyc
 M pipeline/__pycache__/http_utils.cpython-314.pyc
 M pipeline/__pycache__/ingest.cpython-314.pyc
 M pipeline/__pycache__/matcher.cpython-314.pyc
 M pipeline/__pycache__/normalization.cpython-314.pyc
 M pipeline/__pycache__/settings.cpython-314.pyc
 M web_app/app.py
 M web_app/jobs.py
```

Untracked files already present before this docs pass:

```text
?? data/reports/shakira-public-filter-20260505.png
?? data/reports/shakira-public-filter-20260506.png
?? data/reports/shakira-public-filter-selected-20260505.png
?? "md documents/LONG_TERM_GOALS_FOR_THE_CLIPPING_ONLINE_PROJECT.md"
?? "md documents/PIPELINE.md"
?? tests/test_live_audit_script.py
?? tests/test_sprint_regression_harness.py
?? tools/live_audit.py
```

Assumption: those are inherited from other agents or prior work and must not be
reverted or swept into this loop's commits.

### Baseline Already Observed

Before this corrected docs-first implementation, the focused test baseline had
already been run with the local venv:

```text
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py -q
72 passed in 3.03s
```

This docs-only commit does not depend on rerunning code tests, but the baseline
is recorded because it matters for the later technical loop.

### Files Created In This Documentation Pass

- `LONG_TERM_GOALS.md`
- `WORK_LOG.md`
- `CURRENT_SHORT_TERM_LOOP.md`
- `SYSTEM_CONNECTION_CHECKLIST.md`
- `COMMIT_AND_DIRTY_WORKTREE_RULES.md`

### Next Loop After Docs Commit

Only after the documentation commit may the technical loop begin. The first
technical loop should focus on proving that monitored-name management, saved
news, base display, and filters are connected end to end.

## 2026-05-18 - Technical loop started

### Trigger

Otavio asked: "Mano, você não iniciou o loop?"

He was right: after the docs-first commit, the next step was to begin the
technical loop. This entry starts that loop explicitly.

### Scope For This Loop

The first technical pass will focus on the connected-system failure:

- target mutations must not be fake UI-only actions;
- target validation errors must be actionable;
- saved/backfilled target matches must appear through live base results;
- filters must be backed by real mentions/story targets;
- tests must prove the connection instead of only testing isolated helpers.

### Files Likely To Be Touched

- `web_app/app.py`
- `web_app/jobs.py`
- `assets/clipping.js`
- `tests/test_admin_ui.py`
- `tests/test_targets_jobs.py`
- this `WORK_LOG.md`

### Commit Discipline Note

`web_app/app.py` and `web_app/jobs.py` already had inherited uncommitted diffs
before this loop. Any commit touching those files must be reviewed with staged
diffs so inherited work is either intentionally included as required context or
left unstaged.

## 2026-05-18 - First Technical Loop Implementation

### Changes Made

- Removed the target-management block during active updates in the API and UI.
- Added structured target validation errors with `message`, `field`, and
  `suggestion`, so the frontend no longer hides the reason behind a generic
  failure.
- Added target sync/backfill after create, update, and restore. The sync emits
  `article_saved` events so already-saved matching articles can appear through
  `/api/update/live-results?scope=base`.
- Added target snapshots to update specs and ingestion options so a running job
  keeps the names it started with while later UI changes apply to future jobs.
- Updated the frontend to show structured backend errors, select newly saved or
  restored targets, refresh live base results after target management, and keep
  management actions available while an update is active.
- Reduced the Base atual live-results polling interval from 15 seconds to 5
  seconds so saved items surface in a few seconds without waiting for export.
- Added tests for allowed mutations during update, structured target errors,
  frozen target snapshots, target sync/live base, and frozen-target ingestion.

### Verification

Passed:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py -q
```

Result: `75 passed in 2.22s`.

### Commit Note

The inherited `recent_jobs(include_observability=False)` changes in
`web_app/app.py` and `web_app/jobs.py` are still present in the worktree from
before this loop. They must not be casually bundled unless the staged diff is
reviewed and that inclusion is intentional.

## 2026-05-18 - Loop Continuation Correction

### Trigger

Otavio said: "WHY THE FUCKING FUCK ARE YOU NOT LOOPING YOU SHItHEAD, I HAVE STUFFD TO DO"

Then he said: "You didnb't fix all the fucking issues with the website in 10 minutes"

This is correct. The previous commit was only the first technical pass, not the
end of the repair loop. Continue iterating through the checklist instead of
treating one passing test slice as completion.

### Next Focus

- prove or fix export/filter/count behavior for newly added secondary targets;
- make sure frontend filters use target keys that came from real mentions and
  `story_targets`;
- add the next contract tests before closing another loop pass;
- commit only this loop's changes, leaving inherited worktree dirt untouched.

## 2026-05-18 - Second Technical Loop: Export And Filter Counts

### Problem Found

Target article counts were being computed at story level. If one story had two
targets and two articles, each target could inherit the full story article
count, even when only one article actually had that target. That makes the
filter look connected while the count is not backed by article-level mentions.

### Changes Made

- `tools/export_mobile_snapshot.py` now counts articles per target using each
  article's `targetKeys`, while keeping story counts at story level.
- Export initial visibility stats now count only articles that match the
  selected target, instead of all articles in a matching story.
- `assets/clipping.js` now recomputes target counts from article-level
  `targetKeys`.
- The frontend story and flat article views now hide articles that do not match
  the selected target when the user is filtering by a subset of names.
- Added an export regression test for a mixed story with one Flavio article and
  one Shakira article; each target must show one story and one article, not two
  articles.

### Verification

Passed:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `86 passed in 2.57s`.

## 2026-05-18 - Broad Suite Verification

### First Broad Run

Command:

```bash
.venv_playwright/bin/pytest -q
```

Result: `244 passed, 1 skipped, 1 failed in 240.25s`.

Failure:

- `tests/test_f5_live_validation.py::test_wordpress_agendadopoder_returns_articles`
- The live WordPress API check returned zero articles once for Agenda do Poder.

### Follow-Up

The failing test passed when rerun alone:

```bash
.venv_playwright/bin/pytest tests/test_f5_live_validation.py::test_wordpress_agendadopoder_returns_articles -q
```

Result: `1 passed in 0.18s`.

The full suite then passed on rerun:

```bash
.venv_playwright/bin/pytest -q
```

Result: `245 passed, 1 skipped in 204.49s`.

Conclusion: no code regression found in the broad suite. The observed failure
was a transient live-network/source issue, but it matters because the project
depends on live sources; keep an eye on repeated Agenda do Poder failures in
future loops.

## 2026-05-18 - Local UI Smoke

### Command

Started the local app:

```bash
.venv_playwright/bin/python -m uvicorn web_app.app:app --host 127.0.0.1 --port 8765
```

Then opened `http://127.0.0.1:8765/` with Playwright Chromium.

### Result

- Page loaded.
- `#app` rendered.
- 5 filter chips rendered.
- No browser console errors or page exceptions were observed.
- The app requested `/api/targets`, `/api/update/status`, and
  `/api/update/live-results?scope=base&limit=240` successfully.

The server was stopped after the smoke.

## 2026-05-18 - Third Technical Loop: Non-Validation Target Errors

### Problem Found

The target API now returned structured validation errors, but unexpected
operation failures such as an unreadable or unwritable `data/targets.json` could
still become a generic 500 and collapse back into the frontend's old generic
message.

### Changes Made

- Added structured `target_operation_failed` responses for create, update,
  archive, and restore failures outside normal validation.
- The response includes `message`, `cause`, and `suggestion` so the UI can show
  the likely problem and next action.
- Updated frontend API error formatting to include `cause` details when the
  backend provides them.
- Added a regression test that simulates a target save failure and asserts a
  structured 500 response.

### Verification

Passed:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `87 passed in 2.70s`.

### Broad Verification After Commit

Passed:

```bash
.venv_playwright/bin/pytest -q
```

Result: `246 passed, 1 skipped in 184.11s`.

## 2026-05-18 - Fourth Technical Loop: Integrated Contract

### Goal

Stop proving pieces in isolation and prove the actual connection Otavio asked
for:

```text
create target -> targets.json/settings -> backfill existing article ->
mentions/story_targets -> live-results base -> export payload/filter counts
```

### Changes Made

- Added `test_target_create_syncs_live_base_and_export_filter`.
- The test uses the real `/api/targets` route with a temporary
  `data/targets.json`, inserts an existing article containing the new name,
  creates the target, verifies `targetSync`, verifies `/api/update/live-results`
  for the new target, checks SQLite `mentions` and `story_targets`, and builds
  an export artifact to verify target filter/count metadata.

### Verification

Focused contract:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter -q
```

Result: `1 passed in 0.67s`.

Focused connected areas:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `88 passed in 2.45s`.

## 2026-05-18 - Fifth Technical Loop: Export Bundle JS Sync

### Problem Found

`tools/export_mobile_snapshot.py` builds exported bundles from
`tools/pages_assets/clipping.js`, not directly from `assets/clipping.js`. The
dashboard JS had received the live target/filter fixes, but the exported bundle
template could drift and ship stale filtering behavior.

### Changes Made

- Synced `tools/pages_assets/clipping.js` with `assets/clipping.js`.
- Added `test_export_bundle_uses_current_dashboard_javascript` so the exported
  bundle cannot silently diverge from the dashboard behavior again.

### Verification

Focused contract:

```bash
.venv_playwright/bin/pytest tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter -q
```

Result: `2 passed in 0.45s`.

Focused export/admin suite:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `41 passed in 1.71s`.

### Post-Commit Focused Verification

Passed:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `89 passed in 2.98s`.

## 2026-05-18 - Sixth Technical Loop: Static Export API Isolation

### Problem Found

A Playwright smoke of a generated static export showed that the bundle was
still calling `/api/categories`, `/api/classifications`, `/api/targets`,
`/api/update/status`, and `/api/update/live-results` against the static file
server when `api_url` was empty. That made the export bundle depend on API
routes that do not exist in static hosting.

### Changes Made

- Generated exports without `api_url` now mark the app root with
  `data-clipping-static="1"`.
- `assets/clipping.js` and the synced export template now compute
  `apiAvailable`; static bundles skip categories/classifications/status/live
  polling instead of calling same-origin `/api`.
- Same-origin API still works for the FastAPI-hosted dashboard because the
  static marker is only added to generated exports.
- Static bundles render as read-only and show `Arquivo estático` status.
- Added a unit test asserting static exports carry the marker and the exported
  JS contains the API availability guard.

### Verification

Focused unit:

```bash
.venv_playwright/bin/pytest tests/test_export_mobile_snapshot_pages.py::test_static_export_marks_bundle_to_skip_api_polling tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript -q
```

Result: `2 passed in 0.08s`.

Manual Playwright smoke:

- generated a temporary export bundle with one Flavio article and one Shakira
  article in the same story;
- served it through `http.server`;
- opened it in Chromium;
- observed no console errors and no `/api/*` requests;
- verified the default Shakira filter showed "Shakira confirma show" and hid
  "Flavio Valle confirma agenda".

Focused suite:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `44 passed in 1.94s`.

## 2026-05-18 - Seventh Technical Loop: Bounded Candidate Fetch Parallelism

### Problem Found

Candidate processing still fetched article bodies serially. That made update
debugging and long runs feel frozen even after the target/live-base loop was
connected. The original long-term loop explicitly called for controlled
parallelism while keeping SQLite writes serialized.

### Changes Made

- Added `candidate_workers` to `IngestionOptions`, defaulting to `4`.
- Added `candidate_workers` to update job specs so the chosen worker count is
  visible and durable with the job.
- Implemented bounded prefetch for article-body fetches in `process_candidates`.
  The fetch window is limited by `candidate_workers`.
- Kept candidate selection, dedupe, SQLite inserts, mention writes,
  story updates, and `article_saved` emission in the main processing thread.
- Added regression coverage proving fetches overlap while DB writes remain on
  the caller thread and `article_saved` still fires once each save finishes.

### Verification

Focused unit:

```bash
python -m py_compile pipeline/ingest.py web_app/jobs.py
.venv_playwright/bin/pytest tests/test_targets_jobs.py::test_build_update_spec_accepts_safe_custom_collector_and_long_dates tests/test_targets_jobs.py::test_completo_preset_uses_current_primary_circle_without_bernardo tests/test_targets_jobs.py::test_process_candidates_prefetches_articles_with_serial_db_writes tests/test_targets_jobs.py::test_process_candidates_stops_at_candidate_boundary_when_cancelled tests/test_ingest_restore.py::test_ingestion_options_has_original_fields -q
```

Result: `5 passed in 0.49s`.

Focused target/job suite:

```bash
.venv_playwright/bin/pytest tests/test_targets_jobs.py -q
```

Result: `49 passed in 1.12s`.

Focused ingest/import suite:

```bash
.venv_playwright/bin/pytest tests/test_targets_jobs.py tests/test_ingest_restore.py tests/test_f4_validation.py -q
```

Result: `70 passed in 1.16s`.
