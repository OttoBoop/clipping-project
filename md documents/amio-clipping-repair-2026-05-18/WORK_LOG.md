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

Combined loop checkpoint after bounded workers commit:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py tests/test_export_mobile_snapshot_pages.py tests/test_ingest_restore.py tests/test_f4_validation.py -q
```

Result: `114 passed in 3.18s`.

## 2026-05-18 - Scope Correction: Remove Password/Segregation From This Loop

### Error

I incorrectly treated the staged password/profile segregation implementation as
part of this repair loop. That violated the loop boundary: this folder owns
target creation, target errors, filters, live base, export consistency, and
bounded candidate processing. Password/profile segregation belongs to a
separate agent/workstream.

### Correction

- Reverted the password/profile implementation commit and its segregation smoke
  log commits from this branch.
- Preserved the target/filter/live-base commits and the static export isolation
  fix because they are part of the target repair loop.
- Preserved the unrelated lightweight `recent_jobs(include_observability=False)`
  status behavior instead of erasing inherited work while reverting the
  password-specific changes.
- The segregation documentation folder remains separate; it was not merged into
  or used to replace this repair loop's long-term goals.

## 2026-05-18 - Eighth Technical Loop: Frozen Target Snapshots Broke Source Runs

### Problem Found

The live site showed an active durable update repeatedly failing individual
source runs with:

```text
'dict' object has no attribute 'key'
```

This was inside the correct long-term loop, not a password/profile issue:
targets added or edited through the UI need to flow through durable jobs,
candidate ingestion, SQLite mentions, live-results, export, and filters.

### Cause

Jobs correctly persist `target_snapshots` as JSON dictionaries so an active job
keeps using the target names/keywords it started with. But `process_candidates`
sent those dictionaries straight into `select_targets`, which still expected
`Target` objects and read `target.key`.

That meant the job-level snapshot fix could create the next failure: live
source runs with frozen targets crashed before saving candidates.

### Changes Made

- Added normalization in `pipeline/ingest.py` so target dictionaries from
  persisted job snapshots are converted back into `Target` objects before
  selection and matching.
- Kept `select_targets` tolerant of both real `Target` objects and JSON-style
  target snapshots.
- Hardened `web_app/jobs.py::target_to_snapshot` so it can safely receive a
  dict or a `Target`.
- Updated the frozen snapshot test to use a persisted dictionary, matching
  the real durable-job contract.
- Added a regression test that executes:
  `job_source_runs -> run_source_run -> IngestionOptions.target_snapshots ->
  process_candidates -> SQLite mentions`.

### Verification

Focused verification:

```bash
python -m py_compile pipeline/ingest.py web_app/jobs.py
.venv_playwright/bin/pytest tests/test_targets_jobs.py::test_process_candidates_uses_frozen_target_snapshot tests/test_targets_jobs.py::test_run_source_run_accepts_persisted_dict_target_snapshot -q
```

Result: `2 passed in 0.51s`.

Full target/job regression:

```bash
.venv_playwright/bin/pytest tests/test_targets_jobs.py -q
```

Result: `50 passed in 1.29s`.

### Next Checks

- Commit and push only the files in this target/live-base repair scope.
- Verify the real Render site stops producing the repeated
  `'dict' object has no attribute 'key'` source-run failure.
- After the active job is no longer failing on source snapshots, recheck whether
  published target counts still need a fresh export so secondary targets such
  as `vorcaro` show article counts from actual article matches, not mixed-story
  totals from a stale bundle.

### Live Verification After Push

Commit pushed:

```text
34b2575 fix: normalize persisted target snapshots in ingestion
```

The Render site initially kept producing the old failure while the previous
process was still active. After the service restarted on the new commit, the
active job changed from repeated `failed_needs_fix` source runs to normal
running/completing source runs.

Observed live status after restart:

```text
status=running
coverage=running
sourceRunCounts={'complete': 51, 'running': 1, 'pending': 729}
articles_inserted=19
mentions_inserted=25
stories_touched=25
```

Recent live events included `source_run_complete` for `Google News` and
`article_saved` events instead of the repeated
`'dict' object has no attribute 'key'` error.

Observed `/api/update/live-results?scope=base&limit=10` after restart:

```text
articleId=648 targetKeys=['flavio_valle']
articleId=22 targetKeys=['flavio_valle']
articleId=647 targetKeys=['flavio_valle']
articleId=642 targetKeys=['flavio_valle']
articleId=641 targetKeys=['flavio_valle']
```

This confirms the repaired path on the real site:
persisted target snapshot -> durable source run -> ingestion -> SQLite/live
checkpoint -> Base atual API.

## 2026-05-18 - Ninth Technical Loop: Hosted Dashboard Was Marked Static

### Problem Found

A real browser smoke against `https://clipping-project.onrender.com/` loaded
the dashboard but made no calls to `/api/update/live-results`. The HTML served
at `/` included:

```html
data-clipping-api-url=""
data-clipping-static="1"
```

That is correct for exported static bundles, but wrong for the FastAPI-hosted
dashboard. In `assets/clipping.js`, `data-clipping-static="1"` makes
`apiAvailable` false when `data-clipping-api-url` is empty, so the hosted site
skips status polling, target refreshes, and the Base atual live overlay.

### Cause

`web_app/app.py::public_dashboard` returned `index.html` as a raw file. The
export pipeline had correctly marked the generated file as static, but the app
route did not clear that marker when serving the same HTML from a live
same-origin API host.

### Changes Made

- Changed the `/` route to read `index.html`, replace
  `data-clipping-static="1"` with `data-clipping-static="0"`, and return
  `HTMLResponse`.
- Added regression coverage proving the hosted dashboard clears the static
  marker and therefore keeps same-origin API polling enabled.

### Verification

Focused unit:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py::test_hosted_dashboard_enables_same_origin_api_polling -q
```

Result: `1 passed`.

Broader admin/export smoke:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `43 passed in 1.80s`.

### Next Checks

- Push this isolated fix from a clean worktree so unrelated local
  password/segregation edits in `web_app/app.py` are not committed.
- Verify the live `/` HTML has `data-clipping-static="0"`.
- Verify a real browser call to the published site now requests
  `/api/update/live-results?scope=base&limit=240` and renders live Base atual
  items without using a local server.

## 2026-05-18 - Tenth Technical Loop: Dashboard JS Runtime Stopped Live Polling

### Problem Found

After the hosted dashboard marker changed to `data-clipping-static="0"`, a real
browser smoke still did not call `/api/update/live-results`. Capturing page
errors showed:

```text
originalTargetKeys is not defined
```

That runtime error happened during dashboard initialization, before status/base
polling could start.

### Cause

`visibleArticles()` used `originalTargetKeys` as a fallback when selected
filters hid all visible keys, but the variable was never declared. The intended
source was the unfiltered result of `articleTargetKeys(article, story)`.

### Changes Made

- Declared `originalTargetKeys` in `visibleArticles()`.
- Changed `visibleTargetKeys` to a copy of `originalTargetKeys` before applying
  selected-target filtering.
- Applied the same fix to `assets/clipping.js` and
  `tools/pages_assets/clipping.js` so generated exports keep matching the app
  bundle.
- Added a regression assertion that the dashboard JS preserves original target
  keys before filtering.

### Verification

Focused export/JS unit:

```bash
.venv_playwright/bin/pytest tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_preserves_original_target_keys_for_visible_articles -q
```

Result: `1 passed in 0.08s`.

Combined admin/export suite:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `44 passed in 1.80s`.

### Live Verification After Push

Commits pushed:

```text
91e7fb9 fix: enable live polling on hosted dashboard
48ba5b8 fix: restore dashboard live polling runtime
```

Deploy checks:

- `/` initially served `data-clipping-static="1"`.
- after deploy, `/` no longer served the static-only marker for the hosted
  dashboard, so same-origin API access was enabled;
- `/assets/clipping.js` changed to the runtime-fixed bundle containing
  `var originalTargetKeys = articleTargetKeys(article, story);`.

Real browser smoke against `https://clipping-project.onrender.com/`:

```text
body_len=40908
live_request_count=5
status_request_count=3
page_errors=[]
console_errors=[]
```

The browser requested both `/api/update/status` and
`/api/update/live-results...` from the published site and rendered the dashboard
without the previous `originalTargetKeys is not defined` crash.

## 2026-05-18 - Eleventh Loop Audit: Current Live Connections Rechecked

### Checks Run

Live repository head:

```text
origin/master = 12febbd3fdfcb80382b0218b7a11203f196ae9f7
```

Live job status:

```text
job=5b567e5de54b
status=running
coverage=pending
sourceRunCounts={'complete': 78, 'pending': 703}
visible_failed=0
```

Live target/export consistency from `/assets/clipping-data.json`:

```text
stories=462
articles=802
flavio_valle meta=167/210 actual=167/210
pedro_duarte meta=1/1 actual=1/1
pedro_angelito meta=8/10 actual=8/10
bernardo_rubiao meta=2/2 actual=2/2
shakira meta=265/561 actual=265/561
vorcaro meta=2/2 actual=2/2
```

Live UI smoke:

```text
body_len=40908
live_request_count=5
status_request_count=3
page_errors=[]
console_errors=[]
```

### Result

The currently published loop is connected across:

```text
hosted dashboard -> status API -> live-results API -> SQLite/job events
targets in export -> article targetKeys -> filter/count metadata
```

No active `failed_needs_fix` source runs were visible during this audit.

### Remaining Watch Item

The durable job is still running with hundreds of pending source runs. Continue
watching it until it either completes, finds a new source-specific failure, or
publishes another saved article that should appear through the now-restored
live-results polling path.

## 2026-05-18 - Twelfth Loop Hardening: No Idle Exit Protocol

### Objective Reviewed

Otavio explicitly corrected the agent behavior: the loop cannot stop after a
short burst of work, a plan file, a local smoke, or a single successful fix.
The active long-term objective is now promoted to an operating rule: every
success must trigger another review cycle.

### Audit Performed

- Re-read `LONG_TERM_GOALS.md`.
- Re-read `CURRENT_SHORT_TERM_LOOP.md`.
- Re-read the tail of `WORK_LOG.md`, including the hosted dashboard and live
  connection audits.
- Checked the main worktree status and confirmed unrelated inherited dirt still
  exists outside this loop.

### Result

- Created `LOOP_OPERATING_PROTOCOL.md`.
- Added the **No Idle Exit** goal to `LONG_TERM_GOALS.md`.
- Updated `CURRENT_SHORT_TERM_LOOP.md` so tests, commits, pushes, deploys, and
  one live smoke are checkpoints rather than stop conditions.
- Defined a 30-45 minute cycle, live audit checklist, watch queue, log format,
  dirty-worktree rule, and Plan Mode rule.

### Next Hypothesis

After this docs commit, the loop should run at least one live audit cycle using
the new protocol. The first watch item remains the active durable update job and
whether live-results/base keeps reflecting new saved articles while source runs
continue.

### Why The Loop Continues

The protocol itself says documentation is not an exit. Once committed, the next
step is to re-anchor, audit the live site, log the result, and choose the next
failure or watch item.

## 2026-05-18 - Thirteenth Loop Cycle: Live Audit Hit Auth Gate

### Objective Reviewed

The active objective was the new No Idle Exit rule: do not stop after the docs
commit. Start a live audit cycle immediately and record the next watch item.

### Audit Performed

- Checked `/api/update/status`.
- Checked `/api/update/live-results?scope=base&limit=10`.
- Checked `/assets/clipping-data.json`.
- Ran a real browser smoke against `https://clipping-project.onrender.com/`.
- Checked `/healthz`.
- Checked recent git history for the live auth/profile commits.

### Result

The live site is now gated by the separate password/profile workstream:

```text
/api/update/status -> {"detail":"viewer_login_required"} HTTP 401
/api/update/live-results?scope=base&limit=10 -> HTTP 401
/assets/clipping-data.json -> HTTP 401
/api/targets -> {"detail":"viewer_login_required"} HTTP 401
/ -> login page "Acessar clipping"
browser body_len=107
browser status_requests=0
browser live_requests=0
browser has_base_atual=False
```

`/healthz` remains reachable:

```text
ok=true
loginConfigured=true
viewerProfilesConfigured=true
job=status_unavailable
```

Recent origin history shows this came from the other workstream:

```text
011c584 docs: log live gated profile deploy
9fa5d81 chore: trigger Render deploy for gated profiles
12f836b feat: ship password-gated clipping profiles
```

### Next Hypothesis

The target/live-base repair loop should not guess or change credentials. Future
live audits need either an authenticated viewer/admin path supplied by the auth
workstream or a documented unauthenticated audit endpoint. Until then, this loop
can keep checking `/healthz`, static JS availability, git history, local
contract tests, and any authenticated evidence provided by the password/profile
agent.

### Why The Loop Continues

The docs hardening was not an exit. This audit found a new coordination watch
item: live target/base verification is currently blocked by auth, not by the
target matcher/export code itself. The next cycle should either coordinate an
authenticated smoke path or continue with non-auth local/contract checks.

## 2026-05-18 - Fourteenth Loop Cycle: Auth-Gated Local Contracts

### Objective Reviewed

Because the live site now requires viewer/admin login, the next unblocked path
was to prove the local contracts that protect the target/live-base loop while
leaving the separate password/profile workstream alone.

### Audit Performed

- Searched current tests and auth/profile code for dashboard polling,
  live-results, viewer scoping, and target backfill coverage.
- Confirmed the main worktree still has inherited unrelated dirt; no broad
  staging was used.
- Ran focused tests rather than the full suite.

### Result

Focused command:

```bash
.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_hosted_dashboard_enables_same_origin_api_polling \
  tests/test_admin_ui.py::test_viewer_cannot_widen_live_results_or_write_admin_actions \
  tests/test_admin_ui.py::test_live_results_endpoint_returns_saved_articles_before_export \
  tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_preserves_original_target_keys_for_visible_articles \
  tests/test_export_mobile_snapshot_pages.py::test_static_export_marks_bundle_to_skip_api_polling \
  -q
```

Result: `6 passed in 0.59s`.

These tests confirm locally that:

- hosted dashboard HTML enables same-origin API polling;
- viewers cannot widen live-results beyond their allowed targets;
- `article_saved` events appear through live-results before export;
- creating a target can backfill an existing article into live base and export
  filters;
- dashboard JS preserves target keys before filtering;
- static exports still skip API polling.

### Next Hypothesis

The next loop should either receive/use an authenticated smoke path from the
password/profile workstream or keep monitoring accessible live signals
(`/healthz`, static assets, deploy history) while running focused contracts for
any target/live-base regression.

### Why The Loop Continues

Passing these focused tests is a checkpoint, not an exit. The unresolved live
watch item is authenticated verification of status/live-results/Base atual on
the published site.

## 2026-05-18 - Fifteenth Loop Hardening: Unattended Mode

### Objective Reviewed

Otavio clarified the real failure: he needs to leave without babysitting the
agent, and a 4-minute or 20-minute loop is still failure even if it produces
commits. The protocol must say exactly what happens when the user is absent.

### Audit Performed

- Re-read `LOOP_OPERATING_PROTOCOL.md`.
- Re-read `CURRENT_SHORT_TERM_LOOP.md`.
- Re-read the recent auth-gated live audit and local contract cycle.
- Confirmed the plan needs a stronger distinction between checkpoint, blocker,
  and allowed exit.

### Result

- Added **Otavio Away Protocol** to `LOOP_OPERATING_PROTOCOL.md`.
- Added a fixed unattended queue that repeats docs, live audit, auth fallback,
  inconsistency search, log, commit, and restart.
- Added explicit definitions for checkpoint, real blocker, and allowed exit.
- Updated `CURRENT_SHORT_TERM_LOOP.md` with a user-away rule that forbids a
  short final after one cycle.

### Next Hypothesis

The next cycle should test the protocol operationally: first with document
greps proving the new unattended rules exist, then with the current auth-gated
live/local-contract path. Passing those checks must lead to another cycle, not
an immediate final.

### Why The Loop Continues

This hardening is itself a checkpoint. The next action is to verify, commit,
push, then start the first unattended queue cycle under the new rule.

## 2026-05-18 - Sixteenth Unattended Cycle: Live Auth Gate Plus Local Fallback

### Objective Reviewed

The new user-away protocol says an auth-gated live audit is not a reason to
send a final answer. The active objective was to execute the fixed unattended
queue after committing the protocol.

### Audit Performed

- Checked `/api/update/status`.
- Checked `/api/update/live-results?scope=base&limit=10`.
- Checked `/assets/clipping-data.json`.
- Checked `/api/targets`.
- Checked `/healthz`.
- Checked the live `assets/clipping.js` for polling/runtime markers.
- Ran a real browser smoke against the published login page.
- Ran the focused local fallback contracts.

### Result

Live auth state remains gated:

```text
/api/update/status -> HTTP 401 viewer_login_required
/api/update/live-results?scope=base&limit=10 -> HTTP 401 viewer_login_required
/assets/clipping-data.json -> HTTP 401 viewer_login_required
/api/targets -> HTTP 401 viewer_login_required
/healthz -> HTTP 200 ok=true job=status_unavailable
published browser body_len=107 has_login=True status_requests=0 live_requests=0 errors=[]
```

Live JS asset remains compatible with the target/live-base loop:

```text
apiAvailable=True
originalTargetKeys=True
/api/update/live-results?scope=base=True
viewerIsAdmin=True
```

Focused local fallback:

```bash
.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_hosted_dashboard_enables_same_origin_api_polling \
  tests/test_admin_ui.py::test_viewer_cannot_widen_live_results_or_write_admin_actions \
  tests/test_admin_ui.py::test_live_results_endpoint_returns_saved_articles_before_export \
  tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_preserves_original_target_keys_for_visible_articles \
  tests/test_export_mobile_snapshot_pages.py::test_static_export_marks_bundle_to_skip_api_polling \
  -q
```

Result: `6 passed in 0.67s`.

### Next Hypothesis

The protocol still needs explicit operational self-tests written down: auth
gate should lead to local contracts, tests passing should lead to a new audit,
and deploy verified should lead to export/filter review. Writing those cases
will make the unattended plan harder to misread as a single documentation task.

### Why The Loop Continues

The local fallback passed, but that is a checkpoint. The published live data
audit remains blocked by authentication, and the protocol can still be made
stronger by turning the operational simulations into explicit documented cases.

## 2026-05-18 - Seventeenth Loop Hardening: Operational Self-Tests

### Objective Reviewed

The unattended protocol needs to be mechanically harder to misread. A future
agent should be able to test its own impulse to stop after "auth blocked",
"tests passed", "deploy verified", or "no bug visible".

### Audit Performed

- Re-read the new fixed unattended queue.
- Re-read the latest auth-gated live fallback cycle.
- Checked the user plan's operational tests:
  auth gate, tests passing, deploy verified.

### Result

Added **Operational Self-Tests** to `LOOP_OPERATING_PROTOCOL.md`:

- auth gate simulation;
- tests passed simulation;
- deploy verified simulation;
- no fresh bug visible simulation;
- dirty worktree simulation.

Each self-test names the correct next step and the incorrect premature final.

### Next Hypothesis

Run a documentation grep to prove the self-tests are present, then continue the
queue with another accessible audit. If live remains gated, the next useful
area is local target/export consistency and any existing regression harnesses
that can run without credentials.

### Why The Loop Continues

Adding self-tests is a checkpoint. The point of the self-tests is to force the
next cycle, not to justify ending here.

## 2026-05-18 - Eighteenth Unattended Cycle: Live Audit Harness Stale Under Auth Gate

### Objective Reviewed

The fixed unattended queue says to search for the next inconsistency after
contracts pass. The next accessible area was live-audit tooling and regression
harnesses that do not require credentials.

### Audit Performed

- Inspected current tests and tools for live-results, target counts, source
  runs, export filters, and live-audit coverage.
- Found inherited untracked files:
  `tools/live_audit.py`, `tests/test_live_audit_script.py`, and
  `tests/test_sprint_regression_harness.py`.
- Ran `python tools/live_audit.py --base-url https://clipping-project.onrender.com`.
- Compared local `index.html` marker with the live homepage.

### Result

The untracked live audit harness currently fails:

```text
FAIL: homepage asset marker is stale or missing: durable-source-ledger-20260506
```

Reason observed:

```text
local index.html marker = durable-source-ledger-20260506
live / title = Acessar clipping
live / has_login = True
live / dashboard asset markers = []
```

This is not necessarily a target/live-base regression. It is a harness mismatch
after the password/profile workstream changed `/` into a login page. The harness
still assumes the public homepage is the dashboard shell and therefore fails
before reaching `/api/targets` or `/api/update/status`.

### Next Hypothesis

Do not commit the inherited untracked harness files from this loop without a
separate scope decision. A future authenticated live-audit task should either:

- log in before checking dashboard assets and API contracts; or
- intentionally audit the login page first, then use a supplied viewer/admin
  session for dashboard and live-results checks.

### Why The Loop Continues

Finding a stale harness is a useful checkpoint, not an exit. The next available
unblocked work is to keep checking tracked local contracts and document which
live checks are blocked by auth versus genuinely failing.

## 2026-05-18 - Nineteenth Unattended Cycle: Expanded Target/Export Contracts

### Objective Reviewed

With live dashboard/API checks blocked by authentication, the next unblocked
objective was to prove more of the tracked target/live-base/export contracts
locally.

### Audit Performed

- Listed tracked tests covering target snapshots, live-results, export counts,
  secondary filters, source runs, duplicate tagging, and backfill.
- Chose a focused set instead of the full suite.
- Left inherited untracked audit harness files and unrelated worktree dirt
  untouched.

### Result

Focused command:

```bash
.venv_playwright/bin/pytest \
  tests/test_targets_jobs.py::test_update_spec_freezes_target_snapshot_for_active_job \
  tests/test_targets_jobs.py::test_article_saved_events_drive_live_results_and_totals \
  tests/test_targets_jobs.py::test_base_live_results_return_recent_saved_articles_after_export_job \
  tests/test_targets_jobs.py::test_target_sync_backfills_new_target_into_base_live_results \
  tests/test_targets_jobs.py::test_live_results_do_not_resurrect_removed_target_from_stale_event \
  tests/test_targets_jobs.py::test_run_ingestion_builds_collection_queries_for_selected_target \
  tests/test_targets_jobs.py::test_process_candidates_uses_frozen_target_snapshot \
  tests/test_targets_jobs.py::test_run_source_run_accepts_persisted_dict_target_snapshot \
  tests/test_targets_jobs.py::test_process_candidates_tags_duplicate_article_for_new_secondary_target \
  tests/test_export_mobile_snapshot_pages.py::test_active_targets_without_stories_stay_available_as_filters \
  tests/test_export_mobile_snapshot_pages.py::test_secondary_target_stories_are_exported_with_filter \
  tests/test_export_mobile_snapshot_pages.py::test_export_counts_articles_per_target_in_mixed_story \
  tests/test_export_mobile_snapshot_pages.py::test_export_filters_secondary_targets_from_merged_story_records \
  -q
```

Result: `13 passed in 0.56s`.

This covers:

- frozen target snapshots;
- `article_saved` to live-results/totals;
- base live-results after export;
- target create/sync/backfill;
- stale live event target filtering;
- selected-target query construction;
- persisted dict target snapshots in source runs;
- duplicate article retagging for a new secondary target;
- export filters and per-target article counts.

### Next Hypothesis

The next unblocked cycle should inspect the current source/job durability path
and cleanup/backfill false-positive filters, because those are the next likely
places where a target can appear connected locally but misbehave during a long
durable run.

### Why The Loop Continues

Thirteen passing contracts are a stronger checkpoint, not an exit. Live
authenticated verification remains unresolved, and the source/job durability
path still deserves focused review.

## 2026-05-18 - Twentieth Unattended Cycle: Durable Sources And False Positives

### Objective Reviewed

The previous cycle identified durable source runs and secondary-target
false-positive cleanup as the next likely failure areas. The goal was to prove
those contracts locally while live authenticated verification remains blocked.

### Audit Performed

- Ran focused durable-source tests for WordPress/internal search pagination and
  resumable source rows.
- Ran focused cleanup/backfill tests for misleading snippets, boilerplate,
  related links, late incidental mentions, and saved-text preference.
- Avoided the full suite because focused tests covered the current hypothesis.

### Result

Focused command:

```bash
.venv_playwright/bin/pytest \
  tests/test_targets_jobs.py::test_durable_wordpress_units_use_secondary_target_query_not_flavio_site_variants \
  tests/test_targets_jobs.py::test_durable_wordpress_source_runs_use_small_api_pages \
  tests/test_targets_jobs.py::test_durable_internal_search_source_runs_use_one_page \
  tests/test_targets_jobs.py::test_reset_resumable_source_runs_requeues_failed_and_interrupted_rows \
  tests/test_targets_jobs.py::test_export_job_cleans_secondary_false_matches_before_snapshot \
  tests/test_targets_jobs.py::test_backfill_missing_target_mentions_retags_existing_secondary_story \
  tests/test_targets_jobs.py::test_backfill_ignores_full_text_noise_and_cleanup_removes_false_match \
  tests/test_targets_jobs.py::test_cleanup_removes_secondary_target_only_in_late_incidental_preview \
  tests/test_targets_jobs.py::test_cleanup_prefers_saved_text_over_misleading_secondary_snippet \
  tests/test_targets_jobs.py::test_process_candidates_skips_secondary_target_only_in_page_boilerplate \
  tests/test_targets_jobs.py::test_process_candidates_skips_secondary_target_only_in_related_snippet \
  tests/test_targets_jobs.py::test_process_candidates_skips_secondary_target_only_as_late_incidental_mention \
  tests/test_targets_jobs.py::test_process_candidates_prefers_fetched_text_over_misleading_secondary_snippet \
  -q
```

Result: `13 passed in 0.24s`.

### Next Hypothesis

The next checkpoint can run the full tracked target/job suite. That is still
small enough for this loop and will catch integration mistakes across the
target/job contracts already sampled in focused chunks.

### Why The Loop Continues

The targeted durability/cleanup path passed. That narrows the risk but does not
resolve the authenticated live audit or prove the whole target/job file after
recent auth/profile changes.

## 2026-05-18 - Twenty-First Unattended Cycle: Full Target/Job Regression

### Objective Reviewed

After multiple focused target/job contract chunks passed, the next useful
checkpoint was the entire tracked target/job suite.

### Audit Performed

- Ran the full `tests/test_targets_jobs.py` file.
- Kept the scope local because live status/live-results remain auth-gated.

### Result

Command:

```bash
.venv_playwright/bin/pytest tests/test_targets_jobs.py -q
```

Result: `50 passed in 1.03s`.

### Next Hypothesis

Run the tracked admin/export UI contract suite next. That will cover the
auth/profile surface, hosted dashboard behavior, target APIs, live-results UI
contracts, and export bundle behavior together.

### Why The Loop Continues

The core target/job suite passing is a checkpoint. It does not replace
authenticated live verification and does not cover the admin/export UI surface.

## 2026-05-18 - Twenty-Second Unattended Cycle: Admin And Export UI Contracts

### Objective Reviewed

The previous cycle covered target/job internals. The next useful unblocked
surface was admin/export UI contracts, including auth/profile behavior that now
controls access to the live site.

### Audit Performed

- Ran tracked admin UI tests.
- Ran tracked export mobile snapshot/page tests.
- Kept this local because the published site still requires login for API and
  dashboard data checks.

### Result

Command:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `49 passed in 1.97s`.

### Next Hypothesis

Run a combined tracked checkpoint with target/jobs plus admin/export to catch
cross-file regressions introduced by the recent unattended protocol and auth
workstream changes.

### Why The Loop Continues

Admin/export passing is another checkpoint. A combined local checkpoint and the
auth-gated live watch item remain.

## 2026-05-18 - Twenty-Third Unattended Cycle: Combined Local Checkpoint

### Objective Reviewed

After target/jobs and admin/export passed separately, the next useful
checkpoint was running them together to catch cross-file regressions.

### Audit Performed

- Ran target/job tests.
- Ran admin UI tests.
- Ran export mobile snapshot/page tests.

### Result

Command:

```bash
.venv_playwright/bin/pytest tests/test_targets_jobs.py tests/test_admin_ui.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `99 passed in 2.84s`.

### Next Hypothesis

Return to the live-accessible queue items: `/healthz`, login page smoke, static
asset availability, and git/deploy history. Since authenticated API checks
remain blocked, distinguish "live blocked by auth" from "local contracts pass".

### Why The Loop Continues

A 99-test local checkpoint is strong but still not a live authenticated
verification of Base atual/status/export filters on the published site.

## 2026-05-18 - Twenty-Fourth Unattended Cycle: Accessible Live Boundary

### Objective Reviewed

The fixed unattended queue returned to accessible live checks after the combined
local checkpoint. The goal was to separate live auth gating from publicly
observable health/assets/deploy state.

### Audit Performed

- Checked `/healthz`.
- Checked `/` response headers and login page.
- Checked public `/assets/clipping.js` and `/assets/clipping.css`.
- Checked `origin/master` head and recent commit history.

### Result

Accessible live checks:

```text
/healthz -> HTTP 200 ok=true loginConfigured=true viewerProfilesConfigured=true job=idle
/ -> HTTP 200 title="Acessar clipping" has_login=True cache-control=no-cache/no-store
/assets/clipping.js -> HTTP 200 size=100337
/assets/clipping.css -> HTTP 200 size=29708
origin/master -> e359d3fa5ba3641c85787df260ca0ef0a505262d
```

The previously watched durable job is no longer visible through `/healthz`;
health reports `job=idle`. Authenticated API endpoints still require login, so
this does not prove Base atual/status/live-results behind the gate.

### Next Hypothesis

Inspect recent documentation commits from the parallel auth/product loop and
confirm they do not contradict this target/live-base unattended protocol. Then
run another small tracked contract if needed.

### Why The Loop Continues

Public health/assets are stable, but authenticated live verification remains
blocked and the recent git history shows parallel loop documentation that should
be read for coordination risk.

## 2026-05-18 - Twenty-Fifth Unattended Cycle: Parallel Product Loop Coordination

### Objective Reviewed

The previous live boundary cycle found recent commits from the parallel
segregation/product loop. The target/live-base loop needed to read them so it
does not contradict auth/profile decisions or accidentally use static exports
as private proof.

### Audit Performed

- Inspected commits:
  - `ad6a479 docs: log product loop scoping contract cycle`
  - `bdb4703 docs: log viewer ui and static boundary cycle`
- Read the current `STATIC_EXPORT_POLICY.md`.
- Read recent product-loop work-log entries about Render auth gating, local
  profile scoping, static GitHub Pages boundaries, and Rio economic profile
  isolation.

### Result

The parallel docs agree with this loop's current live blocker:

```text
Render root=200/login
assets/clipping-data.json=401
viewerAuthConfigured=false
remaining blocker = missing CLIPPING_VIEWER_PASSWORDS on Render
```

They also clarify that GitHub Pages/static exports still serve JSON/raw payloads
and must not be treated as private client access. That means this target/live
loop should not use GitHub Pages static JSON as proof of private live Base atual
behavior.

No contradiction was found with this loop's target/live-base protocol. The
coordination rule is:

```text
Use local contracts for target/live behavior while production viewer auth is
missing; do not modify auth/profile secrets or static export policy from this
loop.
```

### Next Hypothesis

The next unblocked target/live-base action is another accessible regression or
static analysis pass, not a production authenticated smoke. If live viewer
credentials become available, rerun status/live-results/dashboard/export checks
through the authenticated path.

### Why The Loop Continues

Reading the parallel docs prevents cross-loop mistakes, but it is still a
checkpoint. Authenticated production verification remains blocked by missing
viewer credentials.

## 2026-05-18 - Twenty-Sixth Unattended Cycle: Local Static Artifact Consistency

### Objective Reviewed

The next unblocked target/live-base audit was static export consistency:
compare tracked target config, tracked payload metadata, and export-builder
output without mutating generated assets.

### Audit Performed

- Compared `data/targets.json` active keys to tracked `assets/clipping-data.json`
  target rows.
- Recomputed article/story counts from tracked `assets/clipping-data.json`
  article-level `targetKeys`.
- Built an export artifact in memory from `data/clipping.db` using
  `tools.export_mobile_snapshot.build_snapshot_artifact(...)` without writing
  files.

### Result

Tracked snapshot in `HEAD` is inconsistent with tracked target config/counts:

```text
HEAD config_keys ['flavio_valle', 'pedro_duarte', 'pedro_angelito', 'bernardo_rubiao', 'shakira']
HEAD payload_keys ['flavio_valle', 'pedro_duarte', 'pedro_angelito', 'bernardo_rubiao']
HEAD missing_in_payload ['shakira']
HEAD stories=458 articles=697
flavio_valle meta=436/766 actual=436/674 ok=False
pedro_duarte meta=18/91 actual=18/19 ok=False
pedro_angelito meta=4/6 actual=4/6 ok=True
bernardo_rubiao meta=24/91 actual=24/25 ok=False
```

The export builder itself produced a consistent in-memory artifact from the
current local DB:

```text
targets [('flavio_valle', 354, 591), ('pedro_duarte', 0, 0), ('pedro_angelito', 0, 0), ('bernardo_rubiao', 0, 0), ('shakira', 1, 1)]
stories=355 articles=592
all target meta counts matched article-level targetKeys
```

### Decision

Do not regenerate or commit `assets/clipping-data.json` from the current local
DB in this cycle. The local DB and tracked static snapshot do not represent the
same dataset size, so blindly regenerating would replace hundreds of tracked
articles. This needs a separate static-artifact regeneration decision.

### Next Hypothesis

The code path for export counts appears healthy; the tracked static artifact is
stale/inconsistent. Future work should either regenerate the static snapshot
from the intended production source or stop treating the tracked static payload
as proof of current target/filter behavior.

### Why The Loop Continues

This found a real artifact watch item, but not a safe patch to apply blindly.
The next cycle should keep contract tests and accessible live checks moving
while this static regeneration decision remains open.

## 2026-05-18 - Twenty-Seventh Loop Hardening: Static Artifact Safety Rule

### Objective Reviewed

The previous cycle found a real mismatch in the tracked static payload:
`assets/clipping-data.json` omits the active `shakira` target and has target
metadata counts that disagree with article-level `targetKeys`. The long-term
goal says filters/export/live data must be connected, but the dirty-worktree
rules say generated assets cannot be overwritten blindly.

### Audit Performed

Updated `LOOP_OPERATING_PROTOCOL.md` to add a stale-static-artifact self-test
and a watch item for tracked payload counts that disagree with target config or
article-level target keys.

### Result

The protocol now distinguishes two facts:

```text
export builder from the current DB can produce internally consistent target counts
tracked assets/clipping-data.json is stale/inconsistent against the tracked target config
```

The required behavior is to log the mismatch, verify builder behavior in
memory, and get an explicit source-dataset decision before replacing a large
tracked static snapshot.

### Next Hypothesis

Search the tracked tests for a safe static-artifact contract. If there is no
tracked test that catches target-row/count drift without relying on the local DB
dataset, document the gap and keep the loop on local/live-accessible contracts.

### Why The Loop Continues

The protocol is stronger, but this is a checkpoint. The stale static artifact
watch item still needs either a source-dataset decision or a focused contract
that can safely fail before generated assets drift again.

## 2026-05-18 - Twenty-Eighth Technical Cycle: Runtime Target Count Recompute

### Objective Reviewed

The long-term target/filter objective says the UI cannot show a target row that
is disconnected from the payload beneath it. The previous static audit showed
that stale `articleCount` values can survive in `assets/clipping-data.json`.

### Audit Performed

Used a clean worktree from `origin/master` because the main worktree has an
inherited dirty `assets/clipping-data.json`. Inspected
`mergeRuntimeTargetsIntoPayload(...)` in `assets/clipping.js` and
`tools/pages_assets/clipping.js`.

### Result

Found and patched a concrete frontend bug: when runtime `/api/targets` data
arrived, existing target rows kept stale counts with `Math.max(...)` instead of
using counts recomputed from the actual story/article `targetKeys` in the
payload. The dashboard now assigns:

```text
existing.storyCount = usage.storyCount
existing.articleCount = usage.articleCount
```

Added a tracked test that guards this behavior:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_recomputes_runtime_target_counts_from_payload \
  tests/test_export_mobile_snapshot_pages.py::test_active_targets_without_stories_stay_available_as_filters \
  -q
```

Result: `3 passed in 0.12s`.

Then ran the broader target/admin/export checkpoint from the same clean
worktree:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_targets_jobs.py tests/test_admin_ui.py tests/test_export_mobile_snapshot_pages.py \
  -q
```

Result: `101 passed in 3.38s`.

### Next Hypothesis

Publish this focused runtime-count fix, then return to the unattended queue.
The tracked static snapshot still needs a separate decision because it omits
the active `shakira` row and cannot be fully regenerated safely from the local
DB without replacing the dataset.

### Why The Loop Continues

This fixes one live UI/counting bug, but it is a checkpoint. The stale static
artifact watch item and authenticated production verification remain open.

## 2026-05-18 - Twenty-Ninth Unattended Cycle: Runtime Fix Deploy Watch

### Objective Reviewed

After publishing `fix: recompute runtime target counts`, the loop returned to
the live audit queue. The active objective is still target/filter/base behavior
on the published site, not only local correctness.

### Audit Performed

- Confirmed `origin/master` points at `7b0b70f`.
- Checked published `/healthz`.
- Checked published `/api/update/status`.
- Checked published `/api/update/live-results?scope=base&limit=5`.
- Downloaded published `/assets/clipping.js` and searched for the runtime-count
  patch.

### Result

Live state after the push:

```text
origin/master -> 7b0b70f76af6c7d4081c60ed22b4350c446a4cc5
/healthz -> HTTP 200 ok=true job=idle missingConfig=["CLIPPING_VIEWER_PASSWORDS"]
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
/api/update/live-results?scope=base&limit=5 -> HTTP 401 {"detail":"viewer_login_required"}
/assets/clipping.js -> HTTP 200 but still contains Math.max(Number(existing.storyCount...))
```

This means the code fix is pushed, but the published JS had not yet picked it
up at the time of this check. Authenticated live data remains blocked by the
viewer-login gate and missing viewer password config.

### Next Hypothesis

Keep watching the published JS for the deployed runtime-count patch. While
Render catches up, continue local/static contracts and avoid touching the
auth/password workstream.

### Why The Loop Continues

A pushed fix is not a live proof. The deploy was still serving old JS, and the
authenticated Base atual endpoints remain gated.

## 2026-05-18 - Thirtieth Contract Cycle: Real Short-Name Error Shape

### Objective Reviewed

The original complaint named a concrete failure mode: adding a name could
collapse into "Não foi possível adicionar esse nome" without saying why or how
to fix it. The long-term goal requires actionable error cause, field, impact,
and correction path.

### Audit Performed

Inspected `/api/targets` validation and frontend error parsing. Existing tests
covered structured errors through monkeypatches, but not the real short-name
validation path from `clean_target_payload(...)`.

### Result

Added a tracked contract test for posting `{"display_name": "ab"}` to
`/api/targets`. The expected response is HTTP 400 with:

```text
error=target_validation_error
field=display_name
message=Informe um nome de exibicao com pelo menos 3 caracteres.
suggestion=Digite um nome de exibicao com 3 caracteres ou mais.
```

The test also asserts the payload does not contain "Não foi possível", so the
specific validation cause cannot be masked by a generic failure message.

Command:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_targets_api_validation_errors_are_public_400s \
  tests/test_admin_ui.py::test_targets_api_short_name_error_explains_field_and_fix \
  tests/test_admin_ui.py::test_targets_api_operation_errors_are_structured \
  -q
```

Result: `3 passed in 0.65s`.

Then ran the broader target/admin/export checkpoint:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_targets_jobs.py tests/test_admin_ui.py tests/test_export_mobile_snapshot_pages.py \
  -q
```

Result: `102 passed in 2.94s`.

### Next Hypothesis

Commit this regression guard. After that, re-check whether the runtime-count JS
fix has reached the published site.

### Why The Loop Continues

This locks one error path, but it is still a contract checkpoint. The deployed
JS was stale on the previous audit, and authenticated live endpoints remain
blocked by viewer login.

## 2026-05-18 - Thirty-First Live Cycle: Runtime Count Fix Reached Hosted JS

### Objective Reviewed

The previous deploy watch found the hosted JS still serving the old runtime
target-count merge. The live objective was to verify the pushed frontend fix was
actually published, not just present in Git.

### Audit Performed

- Checked `origin/master`.
- Downloaded `https://clipping-project.onrender.com/assets/clipping.js`.
- Searched the hosted JS for the new assignment and the old `Math.max(...)`
  count-preserving behavior.
- Rechecked `/healthz`, `/api/update/status`, and
  `/api/update/live-results?scope=base&limit=5`.

### Result

Live checkpoint:

```text
origin/master -> ec2a894dee161cbc00207c275cfcf10c3886c811
/assets/clipping.js -> contains existing.storyCount = usage.storyCount
/assets/clipping.js -> no longer contains Math.max(Number(existing.storyCount...)
/healthz -> HTTP 200 ok=true job=idle missingConfig=["CLIPPING_VIEWER_PASSWORDS"]
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
/api/update/live-results?scope=base&limit=5 -> HTTP 401 {"detail":"viewer_login_required"}
```

The runtime count fix is now live in the hosted JS. Authenticated status and
Base atual live-results are still gated by viewer login and the missing Render
viewer password config.

### Next Hypothesis

Continue with non-auth local contracts around target creation, target sync, and
live-results overlay. Do not treat the hosted JS checkpoint as full Base atual
verification.

### Why The Loop Continues

One frontend fix is live, but the core live data endpoints cannot yet be
verified without viewer auth. The loop must keep proving local contracts and
watching the remaining static/export mismatch.

## 2026-05-18 - Thirty-Second Contract Cycle: Target Loop Connection Recheck

### Objective Reviewed

The central long-term objective is not "the button saves"; it is the full loop:
target mutation, frozen update snapshot, backfill/sync, live-results overlay,
and export/filter metadata all have to agree.

### Audit Performed

Reviewed tests and code for:

- target mutations while an update is active;
- `target_snapshots` frozen into update specs;
- `record_target_sync(...)` backfilling existing saved articles;
- Base atual live-results returning newly saved or backfilled articles.

Then ran the focused contract set:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_target_mutations_remain_available_while_update_is_active \
  tests/test_targets_jobs.py::test_update_spec_freezes_target_snapshot_for_active_job \
  tests/test_targets_jobs.py::test_target_sync_backfills_new_target_into_base_live_results \
  tests/test_targets_jobs.py::test_base_live_results_return_recent_saved_articles_after_export_job \
  -q
```

### Result

Result: `4 passed in 0.50s`.

The local contract confirms:

```text
target create/update/restore are not blocked by an active update
active update jobs keep frozen target snapshots
new target sync can backfill existing saved articles
Base atual local live-results sees saved/backfilled target articles before full export
```

### Next Hypothesis

Inspect bounded parallelism and event emission next: the loop still needs to
prove that candidate processing can run in parallel without corrupting dedupe or
SQLite writes, and that `article_saved` events are emitted immediately.

### Why The Loop Continues

The main local connection is healthy, but production live-results/status remain
auth-gated and the static artifact mismatch remains unresolved.

## 2026-05-18 - Thirty-Third Contract Cycle: Bounded Candidate Parallelism

### Objective Reviewed

The plan calls for controlled candidate parallelism: fetch/match work may run
in parallel with a small limit, but SQLite writes must stay serialized and
`article_saved` should emit immediately after each save.

### Audit Performed

Inspected `pipeline/ingest.py` and the tracked test coverage for
`candidate_workers`, prefetching, serialized DB writes, and `article_saved`
progress events.

Ran:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_targets_jobs.py::test_process_candidates_prefetches_articles_with_serial_db_writes \
  -q
```

### Result

Result: `1 passed in 0.21s`.

The focused test verifies:

```text
candidate_workers=2 causes concurrent fetch activity
SQLite insert calls happen only on the main thread
3 saved candidates emit 3 article_saved events
dedupe/write counts remain coherent
```

### Next Hypothesis

Re-run the broader target job suite if more code changes land. Otherwise,
return to live/static audit: the next real unresolved issue is still the
tracked `assets/clipping-data.json` mismatch versus `data/targets.json`.

### Why The Loop Continues

Parallelism is covered locally, but the static artifact mismatch and
auth-gated live Base atual verification are still open.

## 2026-05-18 - Thirty-Fourth Technical Cycle: Initial Payload Count Normalization

### Objective Reviewed

The static artifact audit showed stale target rows and article totals in
`assets/clipping-data.json`. The runtime target-count fix corrected counts when
`/api/targets` refreshes, but the initial render could still trust stale
payload metadata before live-results or target refresh completed.

### Audit Performed

Inspected the dashboard load path and found that `recomputeTargetCounts()` only
ran after live-results merges. Added `normalizePayloadCounts()` to run
immediately after the JSON payload loads and before the first render.

### Result

The dashboard now normalizes the loaded payload by:

```text
setting each story.articleCount to story.articles.length
recounting story ai/raw totals from article summarySource
setting meta totalStories/totalArticles/totalAi/totalRaw from visible payload data
recomputing target story/article counts from story/article targetKeys
```

This is deliberately a runtime normalization, not a large generated-asset
replacement from the local DB.

Focused test:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_normalizes_initial_payload_counts_before_render \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_recomputes_runtime_target_counts_from_payload \
  -q
```

Result: `3 passed in 0.09s`.

Broader checkpoint:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_targets_jobs.py tests/test_admin_ui.py tests/test_export_mobile_snapshot_pages.py \
  -q
```

Result: `103 passed in 3.04s`.

### Next Hypothesis

Commit and publish the runtime normalization, then verify hosted
`/assets/clipping.js` contains `normalizePayloadCounts();`. The active target
row mismatch for static-only bundles remains a separate watch item because a
missing target cannot be invented from the JSON without API/config data.

### Why The Loop Continues

The UI is more resilient to stale counts, but Shakira is still absent from the
tracked static target rows and authenticated live data remains behind the
viewer-login gate.

## 2026-05-18 - Thirty-Fifth Technical Cycle: Static Target Rows Aligned

### Objective Reviewed

The static artifact watch item remained open after the runtime normalization:
`assets/clipping-data.json` still omitted the active `shakira` target row, and
legacy tests still accepted the old four-target assumption.

### Audit Performed

Applied a conservative static repair without regenerating the full snapshot:

- added the active zero-count `shakira` target row from `data/targets.json`;
- corrected target-row article counts to match article-level `targetKeys`
  already present in the payload;
- updated the historical comparison tests so they require static target rows to
  match active target config;
- changed the legacy "all targets have stories" assertion to apply only to
  legacy `.bak` targets, allowing newly configured zero-count targets to remain
  visible as filters;
- added a target-count contract against story/article `targetKeys`.

### Result

Static target rows now read:

```text
flavio_valle: 436 stories / 674 articles
pedro_duarte: 18 stories / 19 articles
pedro_angelito: 4 stories / 6 articles
bernardo_rubiao: 24 stories / 25 articles
shakira: 0 stories / 0 articles
```

Focused checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_bak_comparison.py::TestTargets -q

/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_bak_comparison.py -q
```

Results: `5 passed in 0.12s`; `11 passed in 0.14s`.

Broader checkpoint:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_targets_jobs.py tests/test_admin_ui.py tests/test_export_mobile_snapshot_pages.py tests/test_bak_comparison.py \
  -q
```

Result: `114 passed in 3.06s`.

### Next Hypothesis

Commit and publish the static target-row repair, then verify hosted
`/assets/clipping-data.json` when accessible. If the asset remains auth-gated,
verify the hosted JS and `/healthz`, then continue with local contracts.

### Why The Loop Continues

The static target rows are repaired locally, but production asset verification
is still subject to the live viewer-login gate and deploy timing.

## 2026-05-18 - Thirty-Sixth Live Cycle: Normalization JS Published, Data Asset Gated

### Objective Reviewed

After publishing `fix: normalize dashboard payload counts` and
`fix: align static target rows`, the loop needed to prove what reached the
hosted site and what remains blocked by auth.

### Audit Performed

- Checked `origin/master`.
- Downloaded hosted `/assets/clipping.js`.
- Searched hosted JS for `normalizePayloadCounts();`, target count recompute,
  and the runtime target count assignment.
- Checked hosted `/assets/clipping-data.json`.
- Checked `/healthz`.

### Result

Hosted state:

```text
origin/master -> eb105474cdd94ed4b7f5500fda7fa63536006ca1
/assets/clipping.js -> contains normalizePayloadCounts()
/assets/clipping.js -> contains payload.meta.totalArticles = totalArticles
/assets/clipping.js -> contains existing.storyCount = usage.storyCount
/assets/clipping-data.json -> HTTP 401 {"detail":"viewer_login_required"}
/healthz -> HTTP 200 ok=true job=idle missingConfig=["CLIPPING_VIEWER_PASSWORDS"]
```

The runtime JS fixes are live. The static data payload cannot be verified on the
hosted site without viewer auth because the asset endpoint is intentionally
gated.

### Next Hypothesis

Continue with local contracts and docs while the auth/password workstream owns
`CLIPPING_VIEWER_PASSWORDS`. The next useful checks are full regression breadth
and making sure no commit accidentally included generated pycache or unrelated
main-worktree dirt.

### Why The Loop Continues

Hosted JS verification passed, but authenticated Base atual/status/data payload
verification remains blocked by the viewer-login gate.

## 2026-05-18 - Thirty-Seventh Regression Cycle: Full Suite Failures Repaired

### Objective Reviewed

The unattended protocol says a passing focused suite is not an exit. I ran the
full tracked test suite to look for unrelated breakage and found two failures
that the narrower target/export/admin loop had not exposed.

### Audit Performed

Ran:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest tests -q
```

First result:

```text
1 failed, 255 passed in 206.45s
FAILED tests/test_f5_live_validation.py::test_wordpress_agendadopoder_returns_articles
```

Debug showed `Agenda do Poder` still had WordPress results, but the collector
asked for `per_page=100` even when `per_site_limit=5`, making a slow site
timeout under `request_timeout=15`.

Patched `collect_wordpress_api(...)` to:

- cap `per_page` to the requested site limit;
- retry a slow non-HTTP failure once with a 30-second timeout.

Added unit contracts for both behaviors.

Second full-suite run then found a benchmark race:

```text
1 failed, 257 passed in 197.03s
FAILED tests/test_pages_performance.py::TestPagesBenchmark::test_pages_step_by_step
Initial shell has 1486 DOM nodes (expected <500)
```

The local server returned `assets/clipping-data.json` fast enough that the
"shell only" measurement sometimes captured rendered data. Patched the
Playwright benchmark to route and hold the JSON response until after the shell
snapshot.

### Result

Focused checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_collectors_restore.py::test_wordpress_api_caps_page_size_to_requested_limit \
  tests/test_collectors_restore.py::test_wordpress_api_retries_slow_sites_with_larger_timeout \
  tests/test_f5_live_validation.py::test_wordpress_agendadopoder_returns_articles \
  -q

/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestPagesBenchmark::test_pages_step_by_step \
  -q
```

Results: `3 passed in 0.19s`; `1 passed in 5.56s`.

Final full-suite checkpoint:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest tests -q
```

Result: `258 passed in 189.27s`.

Generated benchmark report and pycache changes were restored before staging.

### Next Hypothesis

Commit the collector/benchmark fixes, then verify hosted JS again and record the
remaining blocker: authenticated live endpoints still require viewer config.

### Why The Loop Continues

The full suite now passes, but commits and live verification are checkpoints,
not exits. Production status/live-results are still auth-gated.

## 2026-05-18 - Thirty-Eighth Live Cycle: Post-Full-Suite Push Check

### Objective Reviewed

After publishing the WordPress collector and benchmark-race fixes, the loop
returned to the live/audit queue instead of stopping at `258 passed`.

### Audit Performed

- Confirmed the clean worktree is clean.
- Confirmed `origin/master` points at `6a314fb`.
- Checked `/healthz`.
- Downloaded hosted `/assets/clipping.js`.
- Rechecked `/api/update/status` and `/api/update/live-results?scope=base&limit=5`.

### Result

Live/accessibility state:

```text
clean worktree -> no local changes
origin/master -> 6a314fb19e4b28ec2889350f0f588a7295d46279
/healthz -> HTTP 200 ok=true job=idle missingConfig=["CLIPPING_VIEWER_PASSWORDS"]
/assets/clipping.js -> contains normalizePayloadCounts()
/assets/clipping.js -> contains existing.storyCount = usage.storyCount
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
/api/update/live-results?scope=base&limit=5 -> HTTP 401 {"detail":"viewer_login_required"}
```

The live frontend assets still have the target-count and payload-normalization
fixes. The authenticated live API checks remain blocked by the viewer-login
gate, not by a discovered 500/crash.

### Next Hypothesis

Record this checkpoint, then re-anchor against the long-term docs and main
dirty worktree so the next agent/cycle knows what is fixed, what is pushed, and
what remains blocked.

### Why The Loop Continues

The full suite and accessible live checks pass, but the authenticated Base atual
verification remains impossible until the viewer password config exists.

## 2026-05-19 - Thirty-Ninth Accountability Reanchor: Loop Was Stopped Too Early

### Objective Reviewed

Otavio reported that I again stopped after a short work period and asked whether
I was even reading the correct documentation. The correct anchor documents are:

- `LONG_TERM_GOALS.md`;
- `LOOP_OPERATING_PROTOCOL.md`;
- `CURRENT_SHORT_TERM_LOOP.md`;
- the tail of this `WORK_LOG.md`.

The active long-term goal is still the full connection loop: target creation,
errors, ingestion, SQLite, live-results, export, filters, and repeated audit.

### Audit Performed

Created a clean worktree from `origin/master` because the main worktree is
dirty and behind the remote. Re-read the anchor docs above before touching
code. Audited the live published app:

```text
/healthz -> HTTP 200 ok=true job=idle missingConfig=["CLIPPING_VIEWER_PASSWORDS"]
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
/api/update/live-results?scope=base&limit=5 -> HTTP 401 {"detail":"viewer_login_required"}
/assets/clipping-data.json -> HTTP 401 {"detail":"viewer_login_required"}
browser root smoke -> HTTP 200 title="Acessar clipping"
browser root smoke -> no /api/update/status or /api/update/live-results call before login
```

Then ran the local auth-gated fallback contracts:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_hosted_dashboard_enables_same_origin_api_polling \
  tests/test_admin_ui.py::test_viewer_cannot_widen_live_results_or_write_admin_actions \
  tests/test_admin_ui.py::test_live_results_endpoint_returns_saved_articles_before_export \
  tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter \
  tests/test_admin_ui.py::test_targets_api_short_name_error_explains_field_and_fix \
  tests/test_targets_jobs.py::test_update_spec_freezes_target_snapshot_for_active_job \
  tests/test_targets_jobs.py::test_process_candidates_prefetches_articles_with_serial_db_writes \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_normalizes_initial_payload_counts_before_render \
  tests/test_bak_comparison.py::TestTargets \
  -q
```

Result: `13 passed in 1.28s`.

### Result

The immediate technical state is stable in local contracts, and the live site is
not crashing; it is gated by viewer login. The operational failure is mine: I
sent a final answer after a checkpoint even though the protocol says a
checkpoint requires another cycle.

### Next Hypothesis

Do not stop here. Continue with another loop cycle by searching for remaining
unproven connections or stale assumptions in docs/tests/code, especially around
authenticated live verification, static payload visibility, and target
management after deploy.

### Why The Loop Continues

Otavio explicitly challenged the previous premature stop. The docs say
checkpoint success is not an exit, and live authenticated Base atual
verification is still blocked by viewer config rather than proven.

## 2026-05-19 - Fortieth Contract Cycle: Frontend Filter Selectability

### Objective Reviewed

The system checklist says the frontend-visible filter must be selectable for a
new target. Prior tests proved static target rows and export counts, but the
browser path for a zero-count secondary target inside "Outros candidatos" was
not explicitly guarded.

### Audit Performed

Ran a local browser smoke against `index.html`. It showed:

```text
Shakira filter exists in the DOM
Shakira is hidden while #outrosFilters is closed
Opening "Outros candidatos" makes Shakira visible
Clicking Shakira marks the chip active
```

Added a Playwright-backed regression test:

```text
tests/test_pages_performance.py::TestFunctionalSanity::test_new_secondary_target_filter_is_visible_after_opening_outros
```

### Result

Focused test:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity::test_new_secondary_target_filter_is_visible_after_opening_outros \
  -q
```

Result: `1 passed in 2.27s`.

Related UI/export contracts:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity \
  tests/test_bak_comparison.py::TestTargets \
  tests/test_export_mobile_snapshot_pages.py::test_active_targets_without_stories_stay_available_as_filters \
  -q
```

Result: `10 passed in 5.27s`.

### Next Hypothesis

Commit this frontend filter guard, then continue the loop by checking whether
any other checklist step is only covered by API-level tests rather than a
user-visible or live-equivalent path.

### Why The Loop Continues

This closes one frontend-visible target-filter gap, but authenticated published
Base atual verification remains blocked and the protocol requires another
cycle after the commit.

## 2026-05-19 - Forty-First Product Copy Cycle: Target Save Mentions Base Atual

### Objective Reviewed

The long-term goal says adding a monitored name must be a real product action,
not a UI-only promise. I found the success message for adding a target still
said the name was "disponível para a próxima rodada", even though the backend
now runs `targetSync` and can backfill existing saved articles into Base atual
immediately.

### Audit Performed

Inspected `targetMutationMessage(...)` and the add/restore target success copy
in `assets/clipping.js` and `tools/pages_assets/clipping.js`.

Patched the copy to say:

```text
Nome extra salvo. Ele já vale para a Base atual e para próximas rodadas.
Nome restaurado. Ele já vale para a Base atual e para próximas rodadas.
```

Added a JS bundle contract to prevent the older "próxima rodada only" message
from returning.

### Result

Focused check:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_target_success_copy_mentions_base_atual \
  -q
```

Result: `2 passed in 0.08s`.

Related product-path check:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter \
  tests/test_admin_ui.py::test_targets_api_short_name_error_explains_field_and_fix \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_target_success_copy_mentions_base_atual \
  tests/test_pages_performance.py::TestFunctionalSanity::test_new_secondary_target_filter_is_visible_after_opening_outros \
  -q
```

Result: `5 passed in 2.79s`.

### Next Hypothesis

Commit this copy guard, then check hosted JS after deploy. Continue searching
for places where UI language implies a weaker or different behavior than the
connected backend loop.

### Why The Loop Continues

The message now matches the Base atual/backfill behavior, but this is another
checkpoint. Live authenticated endpoints are still gated, and the loop still
needs repeated audits.

## 2026-05-19 - Forty-Second Live Cycle: Copy Fix Pushed, Deploy Not Caught Up

### Objective Reviewed

After publishing the target-save copy fix, the loop returned to live audit. A
parallel auth commit also landed: `fix: add safe empty demo viewer login`, so
the auth boundary needed to be checked again rather than assuming the previous
401 state.

### Audit Performed

- Confirmed `origin/master` points at the copy-fix commit.
- Checked `/healthz`.
- Downloaded hosted `/assets/clipping.js`.
- Checked `/api/update/status` and `/api/update/live-results?scope=base&limit=5`.
- Inspected the new auth commit and ran its local tests with the target-copy
  contract.

### Result

Live state at this checkpoint:

```text
origin/master -> 97427f19bb648d85dee69510577727ec7a8a01a8
/healthz -> HTTP 200, but no demoViewerConfigured field yet
/assets/clipping.js -> still contains old "Nome extra salvo e disponível para a próxima rodada."
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
/api/update/live-results?scope=base&limit=5 -> HTTP 401 {"detail":"viewer_login_required"}
```

That means Render had not yet served the latest auth/copy code during this
check. Local expected-state tests pass:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_empty_demo_viewer_login_works_without_viewer_password_env \
  tests/test_admin_ui.py::test_empty_demo_password_disabled_when_real_viewer_passwords_exist \
  tests/test_admin_ui.py::test_empty_demo_password_disabled_if_demo_profile_has_targets \
  tests/test_admin_ui.py::test_healthz_lists_missing_viewer_password_config \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_target_success_copy_mentions_base_atual \
  -q
```

Result: `5 passed in 0.61s`.

### Next Hypothesis

Keep watching `/healthz` for `demoViewerConfigured` and hosted JS for the Base
atual copy. Once deploy catches up, test whether demo login can safely access
the empty viewer payload without widening access to real targets.

### Why The Loop Continues

The latest code is pushed and locally verified, but the hosted site had not yet
picked it up. A pending deploy is a watch item, not an exit.

## 2026-05-19 - Forty-Third Contract Cycle: Frontend Target Error Message

### Objective Reviewed

The long-term error contract says generic messages like "Nao foi possivel
adicionar esse nome" are not acceptable. The API already had a structured
short-name response, but the browser layer needed a regression guard proving
that the form shows the backend's cause and correction instead of falling back
to the generic copy Otavio called out.

### Audit Performed

- Re-read the loop docs and the latest log entry.
- Inspected `assets/clipping.js` around `apiErrorMessage`, `friendlyError`, and
  the `addTargetForm` submit handler.
- Added a Playwright browser contract that routes `/api/targets` to a
  structured validation error and verifies `#addTargetMessage`.
- Ran focused API/frontend tests.

### Result

Added
`tests/test_pages_performance.py::TestFunctionalSanity::test_add_target_shows_structured_validation_error_from_api`.
The test proves the UI displays:

```text
Informe um nome de exibicao com pelo menos 3 caracteres.
Digite um nome de exibicao com 3 caracteres ou mais.
```

and does not display:

```text
Não foi possível salvar este nome.
```

Focused checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity::test_add_target_shows_structured_validation_error_from_api \
  tests/test_admin_ui.py::test_targets_api_short_name_error_explains_field_and_fix \
  -q
```

Result: `2 passed in 2.59s`.

Related target/filter/export checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_target_success_copy_mentions_base_atual \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter \
  tests/test_admin_ui.py::test_targets_api_short_name_error_explains_field_and_fix \
  -q
```

Result: `9 passed in 6.91s`.

### Next Hypothesis

Commit this frontend error-message guard, then return to the live watch queue:
healthz, hosted JS deployment, auth-gated endpoints, and target/filter/export
consistency.

### Why The Loop Continues

This closes one regression gap around the exact bad user-facing error, but it
is still a checkpoint. The live deploy watch and end-to-end Base atual target
loop remain active.

## 2026-05-19 - Forty-Fourth Live Cycle: Deploy Caught Up, Auth Gate Confirmed

### Objective Reviewed

After pushing the frontend target validation guard, the protocol required a
live audit instead of stopping at the commit. The active goals were Base atual
copy/deploy verification, auth-gated live endpoint handling, and local contract
fallback for target/filter/live-results behavior.

### Audit Performed

- Checked hosted `/healthz`.
- Checked hosted `/api/update/status`,
  `/api/update/live-results?scope=base&limit=5`, `/api/targets`, and
  `/assets/clipping-data.json`.
- Inspected hosted `/assets/clipping.js` for the target-save/restored copy.
- Checked the public root HTML for the login gate.
- Ran the local fallback contract group required when live endpoints are
  auth-gated.

### Result

Live state at this checkpoint:

```text
/healthz -> HTTP 200
viewerAuthConfigured -> true
demoViewerConfigured -> false
missingConfig -> []
job -> idle
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
/api/update/live-results?scope=base&limit=5 -> HTTP 401 {"detail":"viewer_login_required"}
/api/targets -> HTTP 401 {"detail":"viewer_login_required"}
/assets/clipping-data.json -> HTTP 401 {"detail":"viewer_login_required"}
/ -> login page with title "Acessar clipping"
```

Hosted JS now contains the corrected copy:

```text
Nome extra salvo. Ele já vale para a Base atual e para próximas rodadas.
Nome restaurado. Ele já vale para a Base atual e para próximas rodadas.
```

Fallback contract command:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_hosted_dashboard_enables_same_origin_api_polling \
  tests/test_admin_ui.py::test_viewer_cannot_widen_live_results_or_write_admin_actions \
  tests/test_admin_ui.py::test_live_results_endpoint_returns_saved_articles_before_export \
  tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter \
  tests/test_admin_ui.py::test_targets_api_short_name_error_explains_field_and_fix \
  tests/test_targets_jobs.py::test_update_spec_freezes_target_snapshot_for_active_job \
  tests/test_targets_jobs.py::test_process_candidates_prefetches_articles_with_serial_db_writes \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_normalizes_initial_payload_counts_before_render \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_target_success_copy_mentions_base_atual \
  tests/test_pages_performance.py::TestFunctionalSanity::test_add_target_shows_structured_validation_error_from_api \
  tests/test_bak_comparison.py::TestTargets \
  -q
```

Result: `15 passed in 3.08s`.

### Next Hypothesis

The hosted app is correctly auth-gated and serving the updated JS, so the next
useful loop is to search for adjacent target connection gaps that tests do not
yet cover: management edit errors, restore/archive UI messaging, or live-results
merge/filter behavior after a newly saved secondary-target article arrives.

### Why The Loop Continues

Deploy caught up and fallback contracts pass, but that is still only a
checkpoint. The user asked for repeated review of the whole target -> ingestion
-> SQLite -> live-results -> export -> filter loop, so the next cycle should
search for unguarded edges.

## 2026-05-19 - Forty-Fifth Contract Cycle: Live-Only Target Filter Gap

### Objective Reviewed

The active long-term goal was the Base atual/live-results loop: when a saved
article appears via live-results, its target must be visible and selectable in
the frontend filter path. This matters for cases where the live overlay knows
about a target before the initial `/api/targets` response or static snapshot has
that target in the active frontend set.

### Audit Performed

- Inspected `mergeLiveResultsIntoPayload()` and `ensureLiveTargetRows()` in
  both dashboard JS bundles.
- Added a Playwright contract where `/api/targets` returns only the primary
  target, but `/api/update/live-results` returns a saved article for a new
  secondary target with `targetLabels`.
- Ran the new test before the fix and observed it fail because `#outrosFilters`
  never appeared.
- Patched `ensureLiveTargetRows()` so live-result target keys are also promoted
  into `activeTargetKeys` when that set is already scoped.

### Result

Found a real filter visibility bug. Before the patch, live-results could add a
target row to `payload.targets` while `isPublicTarget()` still hid it because
`activeTargetKeys` had been initialized from an older `/api/targets` response.
After the patch, a live saved article for `projeto_zeta` creates a visible
secondary target chip and the article is visible after selecting that filter.

Focused check:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity::test_live_results_target_outside_initial_targets_becomes_filterable \
  -q
```

Result: `1 passed in 1.65s`.

Related live/filter/export checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity \
  tests/test_export_mobile_snapshot_pages.py::test_active_targets_without_stories_stay_available_as_filters \
  tests/test_export_mobile_snapshot_pages.py::test_archived_targets_do_not_reappear_in_export_filters \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  tests/test_admin_ui.py::test_viewer_cannot_widen_live_results_or_write_admin_actions \
  tests/test_admin_ui.py::test_live_results_endpoint_returns_saved_articles_before_export \
  tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter \
  -q
```

Result: `12 passed in 7.60s`.

### Next Hypothesis

Commit this live-filter fix, rebase over the parallel documentation commit
`100be3c`, push, and then audit the hosted JS again. After that, continue
checking adjacent management flows and live Base atual behavior.

### Why The Loop Continues

This cycle found and fixed a real end-to-end gap, but it is still a checkpoint.
The fix needs a disciplined commit, deployment watch, live asset verification,
and another pass over target management/live-results edges.

## 2026-05-19 - Forty-Sixth Live Watch: Live-Filter Fix Pushed, Deploy Pending

### Objective Reviewed

After fixing the live-results target filter gap, the protocol required a live
asset check rather than treating the push as completion.

### Audit Performed

- Pushed `4ef2bc9 fix: show live-result targets in filters`.
- Checked hosted `/healthz`.
- Checked hosted `/api/update/status`.
- Downloaded hosted `/assets/clipping.js` with and without a cache-busting query.
- Confirmed `origin/master` and the clean worktree are aligned.
- Inspected server-side live-results filtering to ensure the frontend promotion
  of live target keys does not by itself widen viewer scope.

### Result

Live state:

```text
/healthz -> HTTP 200, job idle, viewerAuthConfigured true, missingConfig []
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
origin/master -> 4ef2bc9
```

Hosted JS at this checkpoint still does not include:

```text
if (activeTargetKeys.size) activeTargetKeys.add(key);
```

It does include the earlier Base atual copy, so Render is serving a version
after the copy fix but before the live-filter fix. The code path remains covered
locally:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity::test_live_results_target_outside_initial_targets_becomes_filterable \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  -q
```

Result after rebase: `2 passed in 1.68s`.

Scope check: `web_app.segmentation.scoped_live_results()` filters live result
items to the session's allowed target keys, and
`web_app.jobs.live_items_from_event_rows()` filters Base atual items to active
target labels. The frontend patch promotes only target keys that the live
endpoint already returned to that viewer.

Parallel-work note: after this live check, `origin/master` advanced to
`1356f6d fix: promote viewer filters without primary targets`, touching the same
dashboard bundles for a different viewer-only filter case. The patch was
inspected before this log commit so the next step can rebase cleanly rather than
overwrite another loop.

### Next Hypothesis

Rebase this log over `1356f6d`, rerun the overlapping frontend/export guards,
push the log, and keep watching the hosted JS for `activeTargetKeys.add(key)`.
While waiting, continue searching management/edit/archive/restore flows for
missing frontend contracts or confusing copy.

### Why The Loop Continues

The fix is pushed and locally verified, but the hosted asset has not caught up.
That is explicitly a watch item, not an exit.

## 2026-05-19 - Forty-Seventh Contract Cycle: Edit During Running Update

### Objective Reviewed

Otavio called out that updating a name while an update had run/was running
should not be blocked by unrelated job state. The backend already had a contract
for target mutations remaining available during active jobs, but the browser UI
needed a guard proving the management form itself stays usable and shows the
snapshot explanation.

### Audit Performed

- Inspected `targetActionsLocked()`, `renderManageTargets()`, management edit
  click handling, and the `.manage-target-form` submit path.
- Added a Playwright contract where `/api/update/status` reports `running`,
  `/api/targets?include_archived=1` returns a secondary target, and PATCH
  `/api/targets/ana_teste` succeeds with `targetSync` plus `activeJobNotice`.
- Verified the edit button is not disabled, the blocked warning is hidden, the
  form input is enabled, and the success message includes both Base atual sync
  and frozen-snapshot language.

### Result

Added
`tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_edit_stays_available_during_running_update`.

Focused check:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_edit_stays_available_during_running_update \
  -q
```

Result: `1 passed in 1.65s`.

Related dashboard/API/export guards:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity \
  tests/test_admin_ui.py::test_target_mutations_remain_available_while_update_is_active \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_promotes_viewer_filters_when_scope_has_no_primary \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  -q
```

Result: `10 passed in 7.80s`.

### Next Hypothesis

Commit this UI contract, push it, and return to the live watch for both
`activeTargetKeys.add(key)` and the parallel viewer-filter promotion line.

### Why The Loop Continues

This protects a second original complaint, but it is still a checkpoint. The
hosted bundle and adjacent restore/archive/error flows still need repeated
review.

## 2026-05-19 - Forty-Eighth Copy Contract Cycle: Active Job Mutation Notice

### Objective Reviewed

The error/response goal is not only about failures. When target management is
allowed during a running update, the success response must explain the snapshot
behavior without using misleading wording for edit/archive/restore actions.

### Audit Performed

- Searched for `activeJobNotice` and the existing "Nome salvo agora" copy.
- Confirmed that `target_mutation_notice()` is shared by create, update,
  archive, and restore.
- Replaced the action-specific-sounding "Nome salvo agora" with the neutral
  "Alteração salva agora".
- Standardized "Base atual" capitalization in the same notice.
- Strengthened backend and browser tests to assert the clearer notice.

### Result

Changed the shared active-job notice to:

```text
Alteração salva agora. A atualização em andamento continua com os nomes
congelados no início; esta mudança vale para a Base atual e para as próximas
rodadas.
```

Focused checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_target_mutations_remain_available_while_update_is_active \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_edit_stays_available_during_running_update \
  -q
```

Result: `2 passed in 2.29s`.

Related checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_target_mutations_remain_available_while_update_is_active \
  tests/test_admin_ui.py::test_targets_api_lists_archived_and_uploads_management_manifests \
  tests/test_pages_performance.py::TestFunctionalSanity \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  -q
```

Result: `10 passed in 8.06s`.

### Next Hypothesis

Commit the notice fix, push, then return to live asset verification and
restore/archive frontend contracts.

### Why The Loop Continues

This improves one response path, but the loop still has hosted deploy watch and
more management edges to audit.

## 2026-05-19 - Forty-Ninth Contract Cycle: Archive/Restore During Running Update

### Objective Reviewed

The target-management loop needs all secondary-name actions to remain available
while an active update uses its frozen target snapshot. Edit had a browser guard;
archive and restore still needed the same UI-level proof.

### Audit Performed

- Added a Playwright contract with a running update, one active secondary
  target, and one archived secondary target.
- Routed archive and restore POSTs through the browser flow with CSRF.
- Verified archive confirmation is enabled, restore is enabled from the archived
  section, and neither flow shows the old "Aguarde a atualização terminar"
  blocker.
- Verified restore success still mentions Base atual sync and active-job
  snapshot behavior.

### Result

Added
`tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_archive_restore_stay_available_during_running_update`.

Focused check:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_archive_restore_stay_available_during_running_update \
  -q
```

Result: `1 passed in 1.46s`.

Related checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity \
  tests/test_admin_ui.py::test_target_mutations_remain_available_while_update_is_active \
  tests/test_admin_ui.py::test_targets_api_lists_archived_and_uploads_management_manifests \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  -q
```

Result: `11 passed in 8.85s`.

### Next Hypothesis

Commit this browser guard, push, then do another live deployment check and look
for remaining target-management error paths.

### Why The Loop Continues

Create, edit, archive, and restore now have stronger UI/API contracts, but live
auth-gated verification and remaining error-message paths still need review.

## 2026-05-19 - Fiftieth Live/Regression Cycle: Hosted Bundle Caught Up

### Objective Reviewed

After the live-filter and management-flow commits, the protocol required a
hosted asset audit plus a broader focused regression run across targets, jobs,
export, and the functional dashboard browser checks.

### Audit Performed

- Checked hosted `/assets/clipping.js?v=512a948`.
- Checked hosted `/healthz`.
- Checked hosted `/api/update/status`.
- Ran the focused regression group for the clipping repair loop.

### Result

Hosted JS now contains both recent frontend filter fixes:

```text
if (!primary.length && other.length && !viewerIsAdmin()) {
if (activeTargetKeys.size) activeTargetKeys.add(key);
```

Live endpoints:

```text
/healthz -> HTTP 200, job idle, viewerAuthConfigured true, missingConfig []
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
```

Focused regression:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py \
  tests/test_targets_jobs.py \
  tests/test_export_mobile_snapshot_pages.py \
  tests/test_pages_performance.py::TestFunctionalSanity \
  -q
```

Result: `116 passed in 11.52s`.

### Next Hypothesis

Continue with the unattended queue: inspect remaining error-message paths,
target/export count consistency, and whether any live-results edge is still
only protected locally because auth blocks direct hosted payload inspection.

### Why The Loop Continues

This is the strongest checkpoint in the current cycle, but it is still a
checkpoint. Auth-gated live payloads, remaining UI error paths, and target count
consistency still deserve another pass.

## 2026-05-19 - Fifty-First Cleanup Cycle: Remove Dead Target Locks

### Objective Reviewed

The long-term goal says target management should not be globally blocked by an
active update. The live UI behavior was already guarded, but stale dead code
still contained the old "Aguarde a atualização terminar" target-management
lock. That made future regressions easier.

### Audit Performed

- Checked static snapshot target counts with a JSON parser because `jq`, `node`,
  and `ruby` are not installed in this environment.
- Confirmed snapshot target counts match story/article target keys; no count
  mismatch was found.
- Searched for `target_mutations_blocked`, `ensure_target_mutations_allowed`,
  `targetActionsLocked`, and the old target-management blocker copy.
- Removed unused backend lock helpers.
- Removed frontend dead branches that disabled edit/archive/restore/save
  controls based on `targetActionsLocked()`.
- Added a static dashboard JS guard so target management lock code does not
  silently return.

### Result

Snapshot count audit returned no mismatches. Current tracked snapshot target
rows:

```text
flavio_valle: 436 stories, 674 articles
pedro_duarte: 18 stories, 19 articles
pedro_angelito: 4 stories, 6 articles
bernardo_rubiao: 24 stories, 25 articles
shakira: 0 stories, 0 articles
```

The only remaining "Aguarde a atualização terminar" string in the dashboard JS
is inside `friendlyError()` for compatibility with stale backend responses; it
is no longer in the target management UI flow.

Focused checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_edit_stays_available_during_running_update \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_archive_restore_stay_available_during_running_update \
  tests/test_admin_ui.py::test_target_mutations_remain_available_while_update_is_active \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  -q
```

Result: `4 passed in 2.84s`.

Related checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_does_not_lock_target_management_during_updates \
  tests/test_admin_ui.py::test_target_mutations_remain_available_while_update_is_active \
  tests/test_admin_ui.py::test_targets_api_short_name_error_explains_field_and_fix \
  -q
```

Result: `12 passed in 7.79s`.

Parallel-work note: while this cleanup was in progress, `origin/master` advanced
to `7bd349c docs: add viewer password operations runbook` through the
segregation loop. It touches different docs; rebase before pushing.

### Next Hypothesis

Commit this cleanup, rebase over the parallel docs commits, push, then run a
live asset check for removal of `targetActionsLocked` from the hosted bundle.

### Why The Loop Continues

The old lock path is being removed, but the hosted deploy and any remaining
error-message compatibility paths still need another pass.

## 2026-05-19 - Fifty-Second Error Contract Cycle: Management Operation Failures

### Objective Reviewed

The original complaint included bad failure responses, not just blocked target
management. Create-target operation failures already had a structured test, but
update/archive/restore failures needed the same coverage.

### Audit Performed

- Checked the hosted bundle after `8e6aa18`; it still served the old
  target-management lock branches, so cleanup deploy remains pending.
- Confirmed `/healthz` is healthy and `/api/update/status` is still auth-gated.
- Added API tests for update, archive, and restore operation failures.
- Verified each management operation returns `target_operation_failed`, the
  correct human-facing action label, a `targets.json` suggestion, and a
  structured `detail.cause`.

### Result

New test:

```text
tests/test_admin_ui.py::test_targets_api_management_operation_errors_are_structured
```

Focused checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_targets_api_operation_errors_are_structured \
  tests/test_admin_ui.py::test_targets_api_management_operation_errors_are_structured \
  tests/test_pages_performance.py::TestFunctionalSanity::test_add_target_shows_structured_validation_error_from_api \
  -q
```

Result: `3 passed in 2.75s`.

Related API checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_targets_api_operation_errors_are_structured \
  tests/test_admin_ui.py::test_targets_api_management_operation_errors_are_structured \
  tests/test_admin_ui.py::test_targets_api_validation_errors_are_public_400s \
  tests/test_admin_ui.py::test_targets_api_short_name_error_explains_field_and_fix \
  tests/test_admin_ui.py::test_target_mutations_remain_available_while_update_is_active \
  -q
```

Result: `5 passed in 0.59s`.

### Next Hypothesis

Commit the expanded operation-error contract, push, and continue watching the
hosted bundle for removal of `targetActionsLocked`.

### Why The Loop Continues

Management operation failures now have better coverage, but the hosted cleanup
deploy has not caught up and live payload inspection remains auth-gated.

## 2026-05-19 - Fifty-Third Live Watch: Target Lock Cleanup Deployed

### Objective Reviewed

After removing dead target-management lock code, the hosted bundle needed to be
checked directly. A local test pass is not enough if the coworker-facing site is
still serving the old blocker branches.

### Audit Performed

- Checked hosted `/assets/clipping.js?v=679e5f8`.
- Checked hosted `/healthz`.
- Confirmed local/remotes were aligned at `679e5f8`.
- Ran a focused fallback group for management operation errors, no-lock JS, and
  archive/restore UI behavior.
- Waited another short deploy window and rechecked the hosted bundle.

### Result

Initial hosted check still showed the old `targetActionsLocked` branches. After
the additional deploy window, hosted JS no longer contains `targetActionsLocked`
or management `aria-disabled` branches. The only remaining
"Aguarde a atualização terminar" string is the compatibility mapping inside
`friendlyError()` for stale backend responses.

Hosted JS now contains:

```text
if (!primary.length && other.length && !viewerIsAdmin()) {
if (activeTargetKeys.size) activeTargetKeys.add(key);
```

and no longer contains:

```text
targetActionsLocked
aria-disabled
```

Focused fallback:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_targets_api_management_operation_errors_are_structured \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_does_not_lock_target_management_during_updates \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_archive_restore_stay_available_during_running_update \
  -q
```

Result: `3 passed in 1.85s`.

### Next Hypothesis

Commit this deploy proof, then continue with another loop over live-results/Base
atual and error copy. If no new bug appears quickly, run another focused target
suite and update the log rather than exiting.

### Why The Loop Continues

The cleanup is now live, but the protocol treats live verification as a
checkpoint. The Base atual payload is still auth-gated, so local contracts and
static asset audits remain useful.

## 2026-05-19 - Fifty-Fourth Regression Cycle: Broad Target Loop Suite

### Objective Reviewed

After the cleanup deploy proof, the loop needed a broader regression checkpoint
covering the target API, update jobs, export snapshot, and functional dashboard
browser contracts together.

### Audit Performed

- Ran the focused broad suite after `0ad9ef5`.
- Restored generated `pipeline/__pycache__` changes after the test run.

### Result

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py \
  tests/test_targets_jobs.py \
  tests/test_export_mobile_snapshot_pages.py \
  tests/test_pages_performance.py::TestFunctionalSanity \
  -q
```

Result: `118 passed in 11.42s`.

### Next Hypothesis

Re-read the loop docs, check hosted health/assets once more, and then look for
remaining weaker coverage around Base atual live overlay or user-facing error
copy.

### Why The Loop Continues

The suite is green, but tests passing is a checkpoint. The protocol requires
another live audit and another search pass.

## 2026-05-19 - Fifty-Fifth Error UX Cycle: Inline Short-Name Validation

### Objective Reviewed

The "errors must explain what happened and what to do" goal applies before the
request reaches the API too. The add/edit forms still had native `minlength`
validation, which could block submit before the inline structured message had a
chance to appear.

### Audit Performed

- Inspected the add-target form, generated management edit forms, and submit
  handlers.
- Added `novalidate` to the add and manage target forms.
- Added shared frontend validation for display names shorter than three
  characters.
- Ensured short-name create/edit attempts show the same actionable inline
  message and do not call CSRF or target mutation APIs.

### Result

Short names now show inline:

```text
Informe um nome de exibicao com pelo menos 3 caracteres. Digite um nome de
exibicao com 3 caracteres ou mais.
```

Focused checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity::test_add_target_short_name_shows_inline_error_without_api_call \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_short_name_shows_inline_error_without_api_call \
  tests/test_admin_ui.py::test_targets_api_short_name_error_explains_field_and_fix \
  -q
```

Result: `3 passed in 2.95s`.

Related frontend checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity \
  tests/test_admin_ui.py::test_targets_api_short_name_error_explains_field_and_fix \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  -q
```

Result: `12 passed in 9.45s`.

Parallel-work note: `origin/master` advanced to
`d7cbb6f docs: log cross-loop viewer recheck` during this cycle. It touches the
segregation loop log only; rebase before pushing.

### Next Hypothesis

Commit and rebase this inline validation fix, push, then verify the hosted
bundle after deploy and continue the Base atual/live-results audit.

### Why The Loop Continues

This closes a pre-API error UX hole, but the hosted site still needs to serve
the new validation code and Base atual remains auth-gated.

## 2026-05-19 - Fifty-Sixth Live Watch: Inline Validation Deploy Pending

### Objective Reviewed

After pushing inline short-name validation, the hosted bundle needed to be
checked before considering the user-facing error path live.

### Audit Performed

- Pushed `f4864b9 fix: show inline target name validation`.
- Checked hosted `/assets/clipping.js` with cache-busting query.
- Checked hosted root page and `/healthz`.
- Confirmed local/remotes aligned at `f4864b9`.
- Waited another short deploy window and rechecked hosted JS.

### Result

Hosted `/healthz` remains healthy and job idle, but hosted JS still does not
contain:

```text
targetDisplayNameError
Informe um nome de exibicao
```

It still contains the earlier live-filter fix:

```text
if (activeTargetKeys.size) activeTargetKeys.add(key);
```

So Render has not yet served the inline validation bundle during this check.

### Next Hypothesis

Keep watching the hosted JS for `targetDisplayNameError`. While waiting, run
another local/live-results contract pass instead of exiting.

### Why The Loop Continues

The fix is pushed but not live. A pending deploy is a watch item, and local
contracts can still verify the Base atual/live-results loop.

## 2026-05-19 - Fifty-Seventh Base Atual Contract Cycle: Auth-Gated Live Fallback

### Objective Reviewed

Because hosted `/api/update/live-results` is still auth-gated, the protocol says
to continue with local contracts that prove the same Base atual/live-results
connection.

### Audit Performed

- Tried to run a live-results focused package; corrected two nonexistent test
  names after locating the real contracts.
- Ran API/job/browser contracts for `article_saved`, Base atual scope,
  target-sync backfill, stale target filtering, and frontend live target
  filterability.
- Rechecked hosted `/api/update/live-results?scope=base&limit=5`.
- Rechecked hosted JS for inline validation deployment.

### Result

Correct fallback package:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_live_results_endpoint_returns_saved_articles_before_export \
  tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter \
  tests/test_targets_jobs.py::test_article_saved_events_drive_live_results_and_totals \
  tests/test_targets_jobs.py::test_base_live_results_return_recent_saved_articles_after_export_job \
  tests/test_targets_jobs.py::test_target_sync_backfills_new_target_into_base_live_results \
  tests/test_targets_jobs.py::test_live_results_do_not_resurrect_removed_target_from_stale_event \
  tests/test_pages_performance.py::TestFunctionalSanity::test_live_results_target_outside_initial_targets_becomes_filterable \
  -q
```

Result: `7 passed in 2.23s`.

Hosted `/api/update/live-results?scope=base&limit=5` remains:

```text
HTTP 401 {"detail":"viewer_login_required"}
```

Hosted JS still does not contain `targetDisplayNameError`, so the inline
validation deploy remains pending.

### Next Hypothesis

Keep watching hosted JS for inline validation. If it continues lagging, run
another local target/error contract pass and document it.

### Why The Loop Continues

Base atual/live-results contracts pass locally, but hosted payload inspection is
auth-gated and the inline validation bundle is not live yet.

## 2026-05-19 - Fifty-Eighth Cleanup Cycle: Remove Hidden Blocker Copy

### Objective Reviewed

The old target-management blocker text should not remain in the visible or
hidden management UI after the lock behavior was removed. Hidden copy can still
mislead future agents and tests.

### Audit Performed

- Searched for `manageTargetsBlocked` and the old "Aguarde a atualização
  terminar para mudar os nomes acompanhados" string.
- Removed the hidden warning element from `index.html`.
- Removed the now-unused JS reference from both dashboard bundles.
- Updated the browser test to assert the old blocker element is absent.

### Result

The old blocker text remains only in `friendlyError()` as compatibility for
stale backend responses, not in the target management UI markup or control flow.

Focused checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_edit_stays_available_during_running_update \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_short_name_shows_inline_error_without_api_call \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  -q
```

Result: `3 passed in 1.82s`.

Related checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_does_not_lock_target_management_during_updates \
  tests/test_admin_ui.py::test_targets_api_short_name_error_explains_field_and_fix \
  -q
```

Result: `13 passed in 10.42s`.

### Next Hypothesis

Commit the hidden-copy cleanup, push, then continue watching the hosted bundle
for inline validation and absence of `manageTargetsBlocked`.

### Why The Loop Continues

The local UI no longer carries the hidden blocker copy, but the hosted inline
validation bundle still needs to deploy.

## 2026-05-19 - Fifty-Ninth Live Watch: Inline Validation Live, Hidden Cleanup Pending

### Objective Reviewed

The inline target-name validation needed a hosted verification. The hidden
`manageTargetsBlocked` cleanup was pushed afterward and also needs a live watch.

### Audit Performed

- Checked hosted `/assets/clipping.js?v=99c08ff`.
- Checked `/healthz`.
- Confirmed local/remotes aligned at `99c08ff`.
- Ran focused inline validation and edit-availability browser contracts.
- Waited another short window and rechecked hosted JS.

### Result

Hosted JS now contains inline validation:

```text
targetDisplayNameError
Informe um nome de exibicao
novalidate
```

Focused local contracts:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity::test_add_target_short_name_shows_inline_error_without_api_call \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_short_name_shows_inline_error_without_api_call \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_edit_stays_available_during_running_update \
  -q
```

Result: `3 passed in 2.90s`.

Hosted JS still contains the now-removed local `manageTargetsBlocked` reference,
so `99c08ff fix: remove hidden target blocker copy` has not fully deployed yet.

### Next Hypothesis

Keep watching for `manageTargetsBlocked` to disappear from hosted JS. Continue
local contract work if deploy remains behind.

### Why The Loop Continues

One user-facing error fix is live, but the hidden blocker cleanup is still
pending on the hosted bundle.

## 2026-05-19 - Sixtieth Static Guard Cycle: Inline Validation Bundle Contract

### Objective Reviewed

Inline short-name validation now has browser tests, but export/static bundle
generation also needs a direct guard so future edits do not drop
`targetDisplayNameError`, `novalidate`, or accidentally restore the old
management blocker.

### Audit Performed

- Added a static dashboard JS/index HTML test for inline target-name validation.
- Strengthened the no-lock JS test to assert `manageTargetsBlocked` does not
  return to the dashboard bundle.
- Ran static and functional focused checks.

### Result

New/strengthened static checks:

```text
tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_has_inline_target_name_validation
tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_does_not_lock_target_management_during_updates
```

Focused checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_does_not_lock_target_management_during_updates \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_has_inline_target_name_validation \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  -q
```

Result: `3 passed in 0.09s`.

Related functional checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_has_inline_target_name_validation \
  tests/test_pages_performance.py::TestFunctionalSanity::test_add_target_short_name_shows_inline_error_without_api_call \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_short_name_shows_inline_error_without_api_call \
  -q
```

Result: `3 passed in 2.49s`.

### Next Hypothesis

Commit the static guard, push, then continue live watch for the hosted removal
of `manageTargetsBlocked`.

### Why The Loop Continues

Static contracts are stronger, but the hosted bundle still needs to catch up to
the hidden-copy cleanup.

## 2026-05-19 - Sixty-First Live/Regression Cycle: Inline Validation Fully Live

### Objective Reviewed

The previous watch item was the hosted bundle: inline validation needed to be
live, and `manageTargetsBlocked`/`targetActionsLocked` needed to be absent from
the served JS.

### Audit Performed

- Checked hosted `/assets/clipping.js?v=ee358bd`.
- Checked hosted `/healthz`.
- Confirmed local/remotes aligned at `ee358bd`.
- Ran the broad focused target loop regression suite again.

### Result

Hosted JS now contains:

```text
targetDisplayNameError
novalidate
if (activeTargetKeys.size) activeTargetKeys.add(key);
```

Hosted JS no longer contains:

```text
manageTargetsBlocked
targetActionsLocked
```

Hosted `/healthz` remains healthy and idle.

Regression:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py \
  tests/test_targets_jobs.py \
  tests/test_export_mobile_snapshot_pages.py \
  tests/test_pages_performance.py::TestFunctionalSanity \
  -q
```

Result: `121 passed in 13.17s`.

### Next Hypothesis

Re-read the docs again, then check whether any remaining original objective is
only documented but not guarded. If no obvious gap appears, run targeted source
searches for generic target/base error copy and stale UI-only target behavior.

### Why The Loop Continues

The latest user-facing error fix is live and tested, but the loop rule still
requires another audit pass instead of stopping on a good checkpoint.

## 2026-05-19 - Sixty-Second Audit Cycle: Generic Copy Search

### Objective Reviewed

After the inline validation and Base atual fixes were live, the next protocol
step was a directed search for remaining generic copy or UI-only target paths.

### Audit Performed

- Searched dashboard JS, backend API, and tests for generic "Não foi possível",
  stale "próxima rodada", target sync, Base atual, and live-results terms.
- Searched for UI-only/fake/fallback target paths and verified the remaining
  fallback functions are paired with runtime target refresh or local tests.
- Checked hosted `/api/update/status` and `/assets/clipping-data.json`.
- Confirmed local/remotes are aligned at `872a1a4`.

### Result

No new code bug found in this pass. Remaining generic-looking copies are either:

- wrapped by `friendlyError(apiErrorMessage(...))`, so structured backend
  details are shown when present;
- outside the target-management complaint, such as raw text loading or update
  start/cancel/resume;
- compatibility mapping for stale backend responses.

Hosted auth state remains:

```text
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
/assets/clipping-data.json -> HTTP 401 {"detail":"viewer_login_required"}
```

### Next Hypothesis

Keep the loop alive with another live health/assets check and, if no new issue
appears, document the current covered objectives and remaining auth-gated limits.

### Why The Loop Continues

This audit did not find a fresh code bug, but no-new-bug is also a checkpoint,
not an exit.

## 2026-05-19 - Sixty-Third Protocol Cycle: Mandatory Output Anchor

### Objective Reviewed

Otávio corrected the loop protocol again: if a barrier is found, the agent must
answer the barrier, register it in the log, and continue. He also required a
specific loop anchor to appear at the start of every assistant output.

### Audit Performed

- Re-read `LOOP_OPERATING_PROTOCOL.md`, `CURRENT_SHORT_TERM_LOOP.md`, and the
  current tail of this log.
- Added a new `Mandatory Output Anchor` section to
  `LOOP_OPERATING_PROTOCOL.md`.
- Added a pointer to that anchor in `CURRENT_SHORT_TERM_LOOP.md`.
- Preserved Otávio's wording verbatim as the required output anchor.

### Result

New required output anchor:

```text
ainda tenho coisas para fazer e coisas para revisar, preciso checar os documentos de longo prazo. Eu não paro esse loop enquanto a open ai não me parar por ter estourado o cartão do Otávio. Eu não paro. Eu façoi num novo passo. Se eu já fiz tudo, eu reviso. E se eu já revisei, eu reviso de novo. Mas eu sempre escrevo o que ue fiz no log e eu não paro o loop, nunca
```

New barrier behavior:

```text
barrier found -> answer it -> write it in WORK_LOG.md -> continue with the next
unblocked step
```

### Next Hypothesis

Commit this protocol update, then run another live/contract audit instead of
ending at documentation.

### Why The Loop Continues

This was a protocol patch, not completion of the product loop. The next cycle
still needs live health/assets checks and local fallback contracts because live
Base atual payloads remain auth-gated.

## 2026-05-19 - Sixty-Fourth Live Barrier Cycle: Auth Gate Answered, Fallback Continued

### Objective Reviewed

The new barrier rule required the agent to answer the barrier, write it in the
log, and continue. The active barrier is hosted live-data auth: the site is
healthy, but live status/Base atual payloads are not accessible without a
viewer/admin session.

### Audit Performed

- Checked hosted `/healthz`.
- Checked hosted `/api/update/status`.
- Checked hosted `/api/update/live-results?scope=base&limit=5`.
- Checked hosted dashboard JS for inline validation, live-result target
  promotion, and viewer-only filter promotion.
- Ran local fallback contracts for Base atual/live-results/target sync and
  inline validation.

### Result

Barrier answered:

```text
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
/api/update/live-results?scope=base&limit=5 -> HTTP 401 {"detail":"viewer_login_required"}
```

Accessible live state:

```text
/healthz -> HTTP 200, job idle, viewerAuthConfigured true, missingConfig []
hosted JS -> targetDisplayNameError, live-result target promotion, viewer-only
filter promotion present
```

Fallback command:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_live_results_endpoint_returns_saved_articles_before_export \
  tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter \
  tests/test_targets_jobs.py::test_target_sync_backfills_new_target_into_base_live_results \
  tests/test_pages_performance.py::TestFunctionalSanity::test_live_results_target_outside_initial_targets_becomes_filterable \
  tests/test_pages_performance.py::TestFunctionalSanity::test_add_target_short_name_shows_inline_error_without_api_call \
  -q
```

Result: `5 passed in 3.37s`.

### Next Hypothesis

Commit this barrier/fallback log, then continue with another source or docs
review instead of stopping at the auth gate.

### Why The Loop Continues

The auth gate blocks direct hosted Base atual inspection, but it does not block
local contracts, hosted asset checks, documentation, or source review.

## 2026-05-19 - Sixty-Fifth Long-Term Memory Cycle: Promote Barrier Rule

### Objective Reviewed

The new barrier/output-anchor rule was written into the active protocol, but it
also needs to live in `LONG_TERM_GOALS.md` because that file is the durable
memory anchor future agents read when context degrades.

### Audit Performed

- Re-read `LONG_TERM_GOALS.md`.
- Added Otávio's barrier instruction and mandatory anchor as source prompts.
- Added a new long-term goal: barriers must be answered, logged, and followed
  by another unblocked step.
- Added a recurring failure class for stopping at auth/deploy/missing-password
  barriers.

### Result

The long-term goals now explicitly require:

```text
barrier -> answer -> WORK_LOG.md -> next unblocked step
```

and point future agents to `LOOP_OPERATING_PROTOCOL.md` for the Mandatory
Output Anchor.

### Next Hypothesis

Commit the long-term memory update, then continue with another live/source
audit.

### Why The Loop Continues

This strengthens the durable memory, but it is still documentation. The product
loop still needs repeated audits.

## 2026-05-19 - Sixty-Sixth Post-Rebase Audit Cycle

### Objective Reviewed

After promoting the barrier rule to long-term memory, `origin/master` advanced
with a parallel docs commit in the segregation loop. The barrier rule required
answering that concurrency barrier, logging it, rebasing safely, and continuing.

### Audit Performed

- Inspected `de50db8 docs: add Rio economic validation plan`.
- Confirmed it touched the segregation docs, not the clipping repair docs.
- Committed the clipping long-term memory update.
- Rebased over `origin/master` and pushed `03fd338`.
- Checked hosted `/healthz` and hosted dashboard JS.
- Ran focused contracts for inline validation, no target lock, add short-name
  UX, and management operation errors.

### Result

Concurrency barrier answered and resolved:

```text
remote commit: de50db8 docs: add Rio economic validation plan
resolution: safe rebase, pushed 03fd338
```

Hosted state:

```text
/healthz -> HTTP 200, job idle
hosted JS -> targetDisplayNameError present
hosted JS -> targetActionsLocked/manageTargetsBlocked absent
```

Focused checks:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_has_inline_target_name_validation \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_does_not_lock_target_management_during_updates \
  tests/test_pages_performance.py::TestFunctionalSanity::test_add_target_short_name_shows_inline_error_without_api_call \
  tests/test_admin_ui.py::test_targets_api_management_operation_errors_are_structured \
  -q
```

Result: `4 passed in 2.60s`.

### Next Hypothesis

Commit this post-rebase audit log, then continue with another source review for
Base atual/live-results or target count drift.

### Why The Loop Continues

The rebase and focused checks passed, but that is a checkpoint. The loop
continues with another audit.

## 2026-05-18 - Sixty-Seventh Rule Update And Manual-Live Gap Cycle

### Objective Reviewed

Otávio updated the basic rule while the loop was auditing Base atual/live-results
connections. The active objective is now stricter: every output must use the
longer anchor, every action must be logged, doubt must trigger a reread of
long-term docs and recent logs, and "looks ready" must trigger review rather
than exit.

### Audit Performed

- Local clock checked with `date -Iseconds`: `2026-05-18T18:46:29-03:00`.
- Re-read the current protocol, long-term goals, short-term loop, and log tail.
- Updated `LOOP_OPERATING_PROTOCOL.md` with Otávio's longer Mandatory Output
  Anchor.
- Added the updated prompt and a new long-term goal to `LONG_TERM_GOALS.md`.
- Pointed `CURRENT_SHORT_TERM_LOOP.md` at the updated anchor and the reread rule.
- While auditing the live-results loop, found a concrete gap: `/api/manual-story`
  writes articles, mentions, stories, and story targets to SQLite, but
  `record_completed_manual` emits `manual_story_completed` instead of
  `article_saved`, so a manual saved article does not use the same immediate
  Base atual live-results channel as ingestion/backfill saves.

### Result

The new rule is being promoted into the operational memory before the code
patch. The next code target is narrow: make manual story creation emit an
`article_saved` event with target metadata so Base atual can show it through
`/api/update/live-results?scope=base` before any export expectation.

### Next Hypothesis

Patch `web_app/jobs.py` and/or `web_app/app.py` plus focused tests in
`tests/test_admin_ui.py` so manual story creation enters the live-results path.

### Why The Loop Continues

This is a newly found connection failure in the same long-term objective:
saved news must appear in Base atual immediately. Logging the rule update is a
checkpoint, not a finish line.

## 2026-05-18 - Sixty-Eighth Manual Story Live Results Patch Cycle

### Objective Reviewed

Saved news must appear in Base atual as soon as it is saved, and "saved" must
mean every confirmation path, not only ingestion and target backfill.

### Audit Performed

- Patched `web_app/db_admin.py` so successful manual story creation returns the
  title, source, published date, target keys, and target labels needed by live
  results.
- Patched `web_app/jobs.py` so `record_completed_manual` emits an
  `article_saved` event for created manual stories before the manual job is
  marked succeeded.
- Patched `tests/test_admin_ui.py` so manual story creation must be visible via
  `/api/update/live-results?scope=base&target_key=flavio_valle&limit=20` and
  must write exactly one `article_saved` event.
- Ran the focused single test:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_manual_story_insert_creates_unique_story_graph \
  -q
```

Result: `1 passed in 0.66s`.

- Ran the neighboring live/manual/target contracts:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_manual_story_insert_creates_unique_story_graph \
  tests/test_admin_ui.py::test_manual_story_insert_is_idempotent_for_duplicate_url \
  tests/test_admin_ui.py::test_live_results_endpoint_returns_saved_articles_before_export \
  tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter \
  tests/test_targets_jobs.py::test_base_live_results_return_recent_saved_articles_after_export_job \
  tests/test_targets_jobs.py::test_target_sync_backfills_new_target_into_base_live_results \
  -q
```

Result: `6 passed in 0.68s`.

- Restored generated `pipeline/__pycache__` dirt after the tests.
- Ran the broader admin/jobs regression:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py tests/test_targets_jobs.py -q
```

Result: `91 passed in 3.35s`.

- Restored generated `pipeline/__pycache__` dirt after the broader regression.

### Result

Manual story creation now enters the same live Base atual path as ingestion and
target backfill. This closes a real connection gap discovered during review:

```text
manual confirmation -> SQLite -> manual job -> article_saved event -> live-results base
```

### Next Hypothesis

Run a slightly broader admin/jobs regression, then commit this patch with
path-limited staging. After push, re-read the docs and audit another adjacent
path instead of stopping.

### Why The Loop Continues

The manual-story live path is patched and locally verified, but this is only one
saved-news confirmation path. The broader loop still needs repeated review of
targets, filters, export counts, hosted auth gates, and dashboard polling.

## 2026-05-18 - Sixty-Ninth Push And Hosted Auth Barrier Cycle

### Objective Reviewed

After the manual-story live-results fix passed locally, the loop rule says the
push is a checkpoint and the next step is live audit plus another review, not a
final answer.

### Audit Performed

- Fetched `origin/master` and inspected remote commit
  `b94bc6c docs: log clipping post-rebase audit`.
- Confirmed `origin/master` was already an ancestor of the local commit.
- Pushed `bfc44ca fix: expose manual stories in live base loop` to `master`.
- Checked hosted `/healthz`.
- Checked hosted `/api/update/live-results?scope=base&limit=5`.
- Confirmed the worktree was clean after the push.

### Result

Push checkpoint:

```text
b94bc6c..bfc44ca HEAD -> master
```

Hosted state:

```text
/healthz -> HTTP 200, job idle, viewerAuthConfigured true, missingConfig []
/api/update/live-results?scope=base&limit=5 -> HTTP 401 {"detail":"viewer_login_required"}
```

Barrier answered: direct hosted live-results inspection still needs a viewer or
admin session. This blocks that one live payload inspection, not the loop.

### Next Hypothesis

Continue with accessible checks and source review. The next useful audit is to
look for another saved-news path that writes SQLite without emitting
`article_saved`, or another filter/export path that can drift from target keys.

### Why The Loop Continues

The code is pushed and the hosted service is healthy, but direct Base atual
payload inspection remains auth-gated. The barrier is logged, and local/source
review remains available.

## 2026-05-18 - Seventieth Export And Browser Regression Review Cycle

### Objective Reviewed

The manual live-results fix should not be treated as complete until adjacent
target/filter/export/browser paths are reviewed. The long-term objective is
still the connected loop, not one endpoint.

### Audit Performed

- Re-read the recent log and long-term goals.
- Searched real article-save paths with `rg` and confirmed production saves are
  covered by ingestion, target backfill/sync, and manual story insertion.
- Reviewed `tools/export_mobile_snapshot.py` target-row/count/filter helpers.
- Reviewed `assets/clipping.js` live-result merge, live target-row creation,
  target count recomputation, and filter rendering.
- Ran the broader focused suite:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py \
  tests/test_targets_jobs.py \
  tests/test_export_mobile_snapshot_pages.py \
  tests/test_pages_performance.py::TestFunctionalSanity \
  -q
```

Result: `121 passed in 13.28s`.

- Restored generated `pipeline/__pycache__` dirt after the test run.

### Result

No new code patch was needed in this cycle. The broader local contracts still
pass after `bfc44ca`, including admin APIs, jobs, export/mobile snapshot
filters, and functional browser checks.

### Next Hypothesis

Commit this review log, then continue with hosted/deploy watch or another source
audit. Since direct live payload inspection is auth-gated, use accessible
health/assets checks and local contracts unless credentials appear.

### Why The Loop Continues

The broad regression is a checkpoint, not an exit. The hosted auth barrier
remains, deploy watch remains, and the loop still needs periodic review of
target/filter/export consistency.

## 2026-05-18 - Seventy-First Explainable Error And Filter Source Review Cycle

### Objective Reviewed

Errors must explain cause and correction, and target filters must be connected
to real target keys/counts rather than UI-only state.

### Audit Performed

- Searched frontend/backend error paths for generic "Não foi possível",
  "Falha", `detail`, thrown errors, and target-specific structured errors.
- Reviewed `assets/clipping.js` `apiErrorMessage` and `friendlyError`.
- Reviewed polling functions for status/live-results/base overlay.
- Reviewed export target-row, target-count, `defaultTargets`, and visibility
  helpers in `tools/export_mobile_snapshot.py`.
- Confirmed the current worktree was clean before this docs-only log update.

### Result

No new code patch was selected in this cycle. The main dashboard target flow now
has structured error handling that surfaces message, suggestion, and cause; the
target add/edit inline validation is already covered by browser tests. Export
target rows include active targets even at zero count and recompute story/article
counts from article-level target keys.

### Next Hypothesis

Continue deploy/live watch with accessible endpoints. If auth blocks direct
payload inspection again, log it and run local contracts or source review rather
than stopping.

### Why The Loop Continues

This review did not reveal a fresh patch, but "no new patch" is not an exit.
The loop continues into hosted watch and repeated connection checks.

## 2026-05-18 - Seventy-Second Hosted Watch Cycle

### Objective Reviewed

After pushing the manual live-results fix and review logs, hosted verification
must continue. A deploy or live smoke is a checkpoint; auth barriers must be
answered and logged.

### Audit Performed

- Checked hosted `/healthz`.
- Checked hosted `/api/update/status`.
- Fetched hosted `/assets/clipping.js` and verified static dashboard markers.
- Checked git state against `origin/master`.

### Result

Hosted state:

```text
/healthz -> HTTP 200, job idle, viewerAuthConfigured true, missingConfig []
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
/assets/clipping.js -> HTTP 200, last-modified Tue, 19 May 2026 21:55:35 GMT
hosted JS -> targetDisplayNameError present
hosted JS -> pollBaseLiveResults present and scheduled
hosted JS -> targetActionsLocked/manageTargetsBlocked absent from rg checks
git -> HEAD and origin/master at 9e3408d
```

Barrier answered: status/live-results remain viewer-auth gated without a session.
The static asset timestamp indicates the hosted app has refreshed assets after
the recent pushes, but direct backend live payload verification is still blocked
by auth.

### Next Hypothesis

Continue with local contract checks or source review for connected target/filter
behavior. Do not stop at healthy hosted static assets.

### Why The Loop Continues

The site is healthy and the hosted static JS is current, but the live authenticated
Base atual payload cannot be inspected from this session. The loop remains
useful through local contracts and source review.

## 2026-05-18 - Seventy-Third Long-Term Anchor Hardening Cycle

### Objective Reviewed

The updated output anchor must remain easy for future agents to find even after
context compaction or hurried handoff.

### Audit Performed

- Re-read `LONG_TERM_GOALS.md` after the hosted watch.
- Added a dedicated `Current Mandatory Output Anchor` section with the updated
  anchor in a plain text code block.

### Result

The long-term memory now contains both Otávio's source prompt and a clean current
anchor block. Future agents do not need to parse nested quoted text to recover
the required output prefix.

### Next Hypothesis

Commit this documentation hardening, then continue with another source or local
contract audit.

### Why The Loop Continues

This strengthens memory but does not finish the product loop. The next cycle
must return to target/filter/Base atual behavior.

## 2026-05-18 - Seventy-Fourth Parallel Ingestion Review Cycle

### Objective Reviewed

Parallel candidate processing must speed fetch/match without making SQLite
writes unsafe or delaying `article_saved` events that feed Base atual.

### Audit Performed

- Reviewed `IngestionOptions.candidate_workers`.
- Reviewed `process_candidates` prefetch scheduling with `ThreadPoolExecutor`.
- Confirmed fetches can be prefetched in parallel while the candidate loop and
  DB writes remain serial in the caller thread.
- Reviewed `emit_article_saved` for both new saved articles and duplicate
  articles retagged for a newly relevant target.
- Ran focused parallel/snapshot/duplicate contracts:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_targets_jobs.py::test_process_candidates_prefetches_articles_with_serial_db_writes \
  tests/test_targets_jobs.py::test_process_candidates_tags_duplicate_article_for_new_secondary_target \
  tests/test_targets_jobs.py::test_process_candidates_uses_frozen_target_snapshot \
  -q
```

Result: `3 passed in 0.40s`.

- Restored generated `pipeline/__pycache__` dirt after the test run.

### Result

No patch was needed. The current contract proves bounded parallel fetch,
serial DB writes, frozen target snapshots, duplicate retagging, and
`article_saved` emission for the important ingestion paths.

### Next Hypothesis

Commit this review log, then continue with another loop item: either live auth
watch, target management UI smoke, or docs/checklist review.

### Why The Loop Continues

The parallelism contract is reviewed and tested, but that is another checkpoint.
The loop still has live auth barriers and repeated end-to-end target/filter/base
checks to revisit.

## 2026-05-18 - Seventy-Fifth Non-Fast-Forward Barrier Cycle

### Objective Reviewed

The barrier rule applies to git concurrency too: answer it, log it, resolve it
safely, and continue instead of stopping after a rejected push.

### Audit Performed

- Push of `8742787 docs: log parallel ingestion review` was rejected with
  `non-fast-forward`.
- Inspected `origin/master`.
- Found remote commit `9abba1f feat: add Rio economic dry-run report tool`.
- Confirmed the remote work was in Rio economic/segregation files and reports,
  with no direct conflict in the clipping code patch.
- Rebasing over `origin/master` succeeded.
- Pushed the rebased clipping log as `247e2b7`.

### Result

Barrier answered and resolved:

```text
remote advanced: 9abba1f feat: add Rio economic dry-run report tool
resolution: git rebase origin/master, then push HEAD:master
pushed: 247e2b7 docs: log parallel ingestion review
```

### Next Hypothesis

Commit this barrier log, then return to the clipping loop: re-read goals, check
hosted health/auth, and choose another local/source contract if live payloads
remain gated.

### Why The Loop Continues

Resolving the git barrier is a checkpoint. The clipping product loop still has
live auth gates and repeated target/filter/base audits to perform.

## 2026-05-18 - Seventy-Sixth Publication State Repair Cycle

### Objective Reviewed

Base atual should show newly saved items immediately, but should not claim an
item is already published in the panel when the action only saved it and did not
publish/export usable artifacts.

### Audit Performed

- During publication-state review, found that a manual story created with
  `export: false` still appeared as `publicationState: "published"`.
- Root cause: `latest_successful_publish_time()` treated every succeeded manual
  job as a publish cutoff, and `latest_publish_time()` treated empty
  `artifacts_uploaded` events as publish events.
- Patched `web_app/jobs.py` so succeeded jobs count as publish cutoffs only when
  they are export jobs or their spec has `export: true`.
- Added `latest_publish_event_time()` so `artifacts_uploaded` counts only when
  the payload has uploaded items/count; `export_complete` and
  `incremental_publish_complete` remain publish signals.
- Updated `tests/test_admin_ui.py` to assert manual story live-results with
  `export: false` stays `publicationState: "saved"`.
- Ran focused publication/live tests:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_manual_story_insert_creates_unique_story_graph \
  tests/test_targets_jobs.py::test_article_saved_events_drive_live_results_and_totals \
  tests/test_targets_jobs.py::test_base_live_results_return_recent_saved_articles_after_export_job \
  -q
```

First run exposed the bug (`published` vs `saved`); after the patch, result:
`3 passed in 0.51s`.

- Ran broader admin/jobs regression:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py tests/test_targets_jobs.py -q
```

Result: `91 passed in 3.56s`.

- Restored generated `pipeline/__pycache__` dirt after tests.

### Result

Manual saved articles still appear in Base atual via live-results, but the UI no
longer mislabels a non-exported manual save as already published.

### Next Hypothesis

Commit and push the publication-state fix, then return to hosted watch and
target/filter review.

### Why The Loop Continues

This closes another live Base atual correctness bug, but it is still one layer
of the loop. Push, verify, log, and continue.

## 2026-05-18 - Seventy-Seventh Publication Fix Push And Checklist Cycle

### Objective Reviewed

The manual live-results fix and publication-state repair must be recorded in
the connection checklist so future agents verify every confirmation path, not
only ingestion.

### Audit Performed

- Pushed `e65c13c fix: keep unexported manual stories saved`.
- Checked hosted `/healthz`.
- Checked hosted `/api/update/live-results?scope=base&limit=5`.
- Re-read `SYSTEM_CONNECTION_CHECKLIST.md`.
- Updated the Live Base Loop checklist to include manual story confirmation and
  saved-vs-published state.

### Result

Hosted state:

```text
/healthz -> HTTP 200, job idle, viewerAuthConfigured true, missingConfig []
/api/update/live-results?scope=base&limit=5 -> HTTP 401 {"detail":"viewer_login_required"}
```

Barrier answered: the hosted live payload is still session-gated. The checklist
now explicitly requires manual confirmations to emit `article_saved` and keeps
saved-but-not-exported items from being mislabeled as published.

### Next Hypothesis

Commit this checklist/log update, then continue with another source or local
contract review.

### Why The Loop Continues

The hosted service is healthy and the checklist is stronger, but direct live
payload verification remains gated and the loop still has target/filter/base
watch items.

## 2026-05-18 - Seventy-Eighth Broad Regression After Publication Fix

### Objective Reviewed

After a publication-state fix, the loop must re-check adjacent admin, jobs,
export, and browser behavior before treating the patch as stable.

### Audit Performed

- Ran the broad focused suite after `e65c13c` and the checklist update:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py \
  tests/test_targets_jobs.py \
  tests/test_export_mobile_snapshot_pages.py \
  tests/test_pages_performance.py::TestFunctionalSanity \
  -q
```

Result: `121 passed in 13.60s`.

- Observed one local static-server `404` for
  `/api/targets?include_archived=1` during the browser suite; the test still
  passed because the static fallback path is expected to remain usable.
- Restored generated `pipeline/__pycache__` dirt after the test run.
- Confirmed the worktree is clean.

### Result

The publication-state repair did not regress the focused admin/jobs/export/
browser contract set.

### Next Hypothesis

Continue with another audit cycle: hosted auth watch, source review, or target
management UI contract review.

### Why The Loop Continues

The regression is green, but green tests are a checkpoint. The loop continues
because live authenticated payload inspection remains blocked and repeated
target/filter/base review is still useful.

## 2026-05-18 - Seventy-Ninth Short-Term Coverage Update Cycle

### Objective Reviewed

When an objective is fixed, the loop must update the planning docs and then
continue reviewing.

### Audit Performed

- Re-read `CURRENT_SHORT_TERM_LOOP.md` coverage checkpoint.
- Added manual-story live-results coverage.
- Added saved-vs-published coverage for manual stories with `export: false`.

### Result

The short-term loop now records that manual confirmation is part of the covered
Base atual path, alongside ingestion, target sync, export filters, and browser
filter behavior.

### Next Hypothesis

Commit this planning-doc update, then continue with another target/filter/base
audit.

### Why The Loop Continues

Updating the plan prevents repeated work, but it does not replace continued
review of the product loop.

## 2026-05-18 - Eightieth Static Payload Target Consistency Audit

### Objective Reviewed

The original failure included a target that appeared visually but did not filter.
The static payload must agree with active targets, story target keys, article
target keys, and target counts.

### Audit Performed

- Parsed `data/targets.json` and `assets/clipping-data.json` as JSON.
- Compared active target keys to payload target rows.
- Compared story/article `targetKeys` to payload target rows.
- Recomputed story/article counts per target from payload stories/articles and
  compared them to `payload.targets[*].storyCount/articleCount`.

### Result

Static payload consistency snapshot:

```text
active_targets -> 5 ['flavio_valle', 'pedro_duarte', 'pedro_angelito', 'bernardo_rubiao', 'shakira']
payload_targets -> 5 ['flavio_valle', 'pedro_duarte', 'pedro_angelito', 'bernardo_rubiao', 'shakira']
active_missing_from_payload -> []
payload_missing_from_active -> []
story_keys_missing_from_payload_targets -> []
article_keys_missing_from_payload_targets -> []
count_mismatches -> [] total 0
defaultTargets -> ['flavio_valle']
meta -> totalStories 458, totalArticles 805, initialStoryCount 436, initialArticleCount 766
```

No static target/filter mismatch was found in the tracked payload.

### Next Hypothesis

Commit this audit log, then continue with hosted watch or another local contract.

### Why The Loop Continues

The tracked static payload is consistent now, but the loop also has runtime
target creation, live overlay, auth-gated hosted payloads, and future exports to
keep reviewing.

## 2026-05-18 - Eighty-First Hosted Asset Payload Barrier Cycle

### Objective Reviewed

Hosted assets and live payloads must be checked when possible, and auth barriers
must be logged rather than used as a stop reason.

### Audit Performed

- Requested hosted `/assets/clipping-data.json`.
- Requested hosted `/assets/clipping.js`.
- Checked current git status.

### Result

Hosted state:

```text
/assets/clipping-data.json -> HTTP 401 {"detail":"viewer_login_required"}
/assets/clipping.js -> HTTP 200, last-modified Tue, 19 May 2026 22:03:08 GMT
hosted JS markers -> targetDisplayNameError present, pollBaseLiveResults present,
publicationState handling present
worktree -> clean
```

Barrier answered: the hosted data payload is still viewer-auth gated, so direct
published JSON consistency cannot be inspected from this session. The hosted JS
is accessible and has refreshed after the latest pushes.

### Next Hypothesis

Continue with local contracts/source audits while hosted data remains gated.

### Why The Loop Continues

Auth gating blocks only direct hosted data inspection. The loop still has useful
local verification and code review paths.

## 2026-05-18 - Eighty-Second Update No-Export Publication Guard Cycle

### Objective Reviewed

The saved-vs-published rule should apply to all update jobs, not only manual
story creation.

### Audit Performed

- Added `tests/test_targets_jobs.py::test_update_without_export_keeps_base_live_result_saved`.
- The test creates a succeeded update job with `export: false`, records an
  `article_saved` event, and asserts Base atual live-results still returns
  `publicationState: "saved"`.
- Ran focused guard tests:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_targets_jobs.py::test_update_without_export_keeps_base_live_result_saved \
  tests/test_admin_ui.py::test_manual_story_insert_creates_unique_story_graph \
  -q
```

Result: `2 passed in 0.55s`.

- Ran broader admin/jobs regression:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py tests/test_targets_jobs.py -q
```

Result: `92 passed in 3.08s`.

- Restored generated `pipeline/__pycache__` dirt after tests.

### Result

The publication-state repair is now guarded for both manual no-export saves and
update no-export saves.

### Next Hypothesis

Commit the test guard, push, then continue with hosted watch or another source
audit.

### Why The Loop Continues

The guard reduces regression risk, but it is another checkpoint. The loop still
has live auth gates and target/filter/base review items.

## 2026-05-18 - Eighty-Third Job Totals Source Review Cycle

### Objective Reviewed

Base atual and update status must keep counters trustworthy while `article_saved`
events feed live-results.

### Audit Performed

- Re-read git status and recent log.
- Reviewed `job_progress`, `source_progress_totals`, `article_saved_totals`,
  and `sync_live_progress_totals` in `web_app/jobs.py`.
- Reviewed the existing focused test
  `tests/test_targets_jobs.py::test_article_saved_events_drive_live_results_and_totals`.

### Result

No patch was selected in this cycle. The current implementation computes status
totals from the maximum of stored job totals, latest source-progress totals, and
`article_saved` deltas; `record_progress` syncs live totals after saved events.
The focused test already verifies inserted/mention/story counters and saved
live-results state.

### Next Hypothesis

Commit this source-review log, then continue with hosted watch or another
target/filter path.

### Why The Loop Continues

Counters look covered locally, but this is a review checkpoint. The loop still
has auth-gated hosted payloads and future runtime target changes to keep
checking.

## 2026-05-18 - Eighty-Fourth Hosted Watch After No-Export Guard

### Objective Reviewed

After new tests and logs, the hosted app should remain healthy, and auth-gated
checks should be answered as barriers rather than stop conditions.

### Audit Performed

- Checked hosted `/healthz`.
- Fetched hosted `/assets/clipping.js`.
- Checked hosted `/api/update/status`.
- Checked local git status.

### Result

Hosted state:

```text
/healthz -> HTTP 200, job idle, viewerAuthConfigured true, missingConfig []
/assets/clipping.js -> HTTP 200, last-modified Tue, 19 May 2026 22:06:16 GMT
hosted JS -> targetDisplayNameError, pollBaseLiveResults, publicationState
             handling present
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
worktree -> clean
```

Barrier answered: authenticated status remains gated. Accessible health and
static JS checks remain healthy/current.

### Next Hypothesis

Commit this hosted watch log, then continue with local source review or a
target-management contract check.

### Why The Loop Continues

Hosted health is good, but the direct status/live payload remains auth-gated.
That means continue with accessible checks, not stop.

## 2026-05-18 - Eighty-Fifth Non-Fast-Forward Barrier Cycle

### Objective Reviewed

Git concurrency remains part of the loop: remote work must be inspected and
integrated without overwriting other agents or stopping.

### Audit Performed

- Push of `47ae02d docs: log hosted watch after no-export guard` was rejected
  with `non-fast-forward`.
- Inspected remote commit
  `e7b5e92 feat: make Rio dry-run skip redirect resolution`.
- Remote commit touched Rio economic dry-run reports/docs plus
  `pipeline/collectors.py`, `tests/test_collectors_restore.py`,
  `tests/test_rio_economic_dry_run.py`, and `tools/rio_economic_dry_run.py`.
- Rebased the clipping hosted-watch log over `origin/master`.
- Pushed the rebased log as `acce5d3`.

### Result

Barrier answered and resolved:

```text
remote advanced: e7b5e92 feat: make Rio dry-run skip redirect resolution
resolution: git rebase origin/master, then push HEAD:master
pushed: acce5d3 docs: log hosted watch after no-export guard
```

### Next Hypothesis

Because the remote commit touched `pipeline/collectors.py`, run a small
collector/ingestion-adjacent verification before returning to live watch.

### Why The Loop Continues

The git barrier is resolved, but remote collector changes can affect the
clipping update loop. Verification remains useful.

## 2026-05-18 - Eighty-Sixth Collector Rebase Verification Cycle

### Objective Reviewed

Remote collector changes should be checked against the clipping ingestion loop
before assuming the rebase is harmless.

### Audit Performed

- Ran collector restore tests plus two ingestion-adjacent target/job contracts:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_collectors_restore.py \
  tests/test_targets_jobs.py::test_process_candidates_prefetches_articles_with_serial_db_writes \
  tests/test_targets_jobs.py::test_process_candidates_reports_candidate_progress_before_fetch_fail \
  -q
```

Result: `25 passed in 0.25s`.

- Restored generated `pipeline/__pycache__` dirt after the test run.

### Result

The collector rebase did not break the small collector/ingestion contract set
used by the clipping loop.

### Next Hypothesis

Commit this verification log, then continue with hosted watch or target
management review.

### Why The Loop Continues

The rebase is verified locally, but this is another checkpoint. The loop still
has live auth barriers and target/filter/base review work.

## 2026-05-18 - Eighty-Seventh Target Management Browser Contract Cycle

### Objective Reviewed

The user-visible target management loop must keep working in the browser: inline
errors, management during active updates, archive/restore, and live overlay
filters.

### Audit Performed

- Ran focused Playwright/browser contracts:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity::test_add_target_short_name_shows_inline_error_without_api_call \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_short_name_shows_inline_error_without_api_call \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_edit_stays_available_during_running_update \
  tests/test_pages_performance.py::TestFunctionalSanity::test_manage_target_archive_restore_stay_available_during_running_update \
  tests/test_pages_performance.py::TestFunctionalSanity::test_live_results_target_outside_initial_targets_becomes_filterable \
  -q
```

Result: `5 passed in 4.05s`.

- Observed one local static-server `404` for
  `/api/targets?include_archived=1`; the targeted browser fallback still passed.
- Confirmed no worktree dirt remained after the test run.

### Result

The browser-level target management and live-overlay filter contracts are still
green.

### Next Hypothesis

Commit this browser contract log, then continue with hosted watch or another
source review.

### Why The Loop Continues

Browser contracts passing is a checkpoint, not a stop. The live hosted data
payload is still auth-gated and must remain on the watch list.

## 2026-05-18 - Eighty-Eighth Rio Log Rebase Barrier Cycle

### Objective Reviewed

Remote docs-only work from another loop must be integrated safely and logged,
not overwritten or used as a stopping point.

### Audit Performed

- Push of `a16e6c1 docs: log target browser contract review` was rejected with
  `non-fast-forward`.
- Inspected remote commit
  `1d8eea3 docs: log Rio workaround deploy observation`.
- Confirmed it only touched
  `md documents/clipping-segregation-product-loop-2026-05-18/WORK_LOG.md`.
- Rebased the clipping browser-contract log over `origin/master`.
- Pushed the rebased clipping log as `17995d1`.

### Result

Barrier answered and resolved:

```text
remote advanced: 1d8eea3 docs: log Rio workaround deploy observation
resolution: git rebase origin/master, then push HEAD:master
pushed: 17995d1 docs: log target browser contract review
```

### Next Hypothesis

Commit this barrier log, then continue with hosted watch or another local
contract.

### Why The Loop Continues

The git barrier is resolved, but the clipping loop still has auth-gated hosted
payloads and repeated target/filter/base reviews to perform.

## 2026-05-18 - Eighty-Ninth Worktree Isolation Audit

### Objective Reviewed

Commits must remain path-limited and avoid inherited dirty work. The clean
worktree exists to keep this loop from mixing other agents' edits into clipping
fixes.

### Audit Performed

- Checked current loop worktree status.
- Checked main worktree status at
  `/home/otavio/Documents/vscode/clipping-project`.
- Listed active worktrees.

### Result

Current loop worktree:

```text
/tmp/clipping-loop-20260519-1 -> clean detached HEAD at 018e648
```

Main worktree remains inherited/dirty and behind origin:

```text
master...origin/master [behind 70]
modified: README.md, assets/clipping-data.json, data/reports/performance_benchmark.md,
          md documents/05-05-26-Iris-Shakira goals.md,
          md documents/Who_Is_Doing_What-WRITE_WHAT_YOU'RE_DOING_HERE.md,
          pipeline/__pycache__/*
deleted: docs/LONG_TERM_GOALS_FOR_THE_CLIPPING_ONLINE_PROJECT.md, docs/PIPELINE.md
untracked: data/clipping.db-shm, data/clipping.db-wal, old shakira screenshots,
           moved docs, tests/test_live_audit_script.py,
           tests/test_sprint_regression_harness.py, tools/live_audit.py
```

Active worktrees include this clipping loop, the main dirty worktree, and other
parallel Rio/Q006/live-runner worktrees.

### Next Hypothesis

Keep using `/tmp/clipping-loop-20260519-1` for clipping commits. Do not stage or
clean the inherited main worktree without explicit instruction.

### Why The Loop Continues

Worktree isolation is healthy, but this is process hygiene. Product review still
continues.

## 2026-05-18 - Ninetieth Auth Barrier Source Review

### Objective Reviewed

Hosted live payload inspection is blocked by auth. The loop should understand
the barrier without guessing passwords or taking over the auth workstream.

### Audit Performed

- Reviewed `web_app/auth.py` session/password logic.
- Reviewed `web_app/segmentation.py` viewer profile scoping.
- Searched tests and app code for `CLIPPING_VIEWER_PASSWORDS`,
  `viewer_login_required`, demo viewer configuration, and session creation.

### Result

The hosted `viewer_login_required` barrier is expected from code when no valid
`clipping_admin` session cookie is present. Health says viewer passwords and
viewer profiles are configured, while public empty demo is disabled because real
viewer auth is configured. This loop should not guess production passwords or
change the auth workstream.

### Next Hypothesis

Continue using local authenticated contracts and hosted unauthenticated health/
static checks until Otávio or the auth-focused IA provides a valid session path.

### Why The Loop Continues

The auth barrier is understood but still blocks only direct hosted payload
inspection. Local contracts, static assets, source review, and docs remain
available.

## 2026-05-18 - Ninety-First Protocol And Commit Rule Reanchor

### Objective Reviewed

After many commits and rebase barriers, the loop should re-read its operating
protocol and commit hygiene rules before the next patch or audit.

### Audit Performed

- Checked current loop worktree status and recent commit log.
- Re-read `COMMIT_AND_DIRTY_WORKTREE_RULES.md`.
- Re-read `LOOP_OPERATING_PROTOCOL.md`.

### Result

Current loop worktree is clean at `e2e3ba2`/`origin/master`. The protocol still
requires No Idle Exit, auth-barrier fallback, path-limited staging, no `git add
.` and repeated reanchor/audit/log cycles.

### Next Hypothesis

Commit this reanchor log, then continue with either hosted watch or another
focused local contract.

### Why The Loop Continues

Re-reading the rules prevents drift, but it does not close the product loop.
There are still auth-gated hosted payloads and watch items.

## 2026-05-18 - Ninety-Second Rule Reaffirmation Cycle

### Objective Reviewed

Otávio reaffirmed the updated basic rule: every output must start with the long
anchor, every barrier must be answered and logged, every action must be logged,
and the loop must return to long-term docs/logs whenever there is doubt instead
of stopping.

### Audit Performed

- Checked current loop worktree status.
- Re-read the tail of `WORK_LOG.md`.
- Searched the active loop documents for the current Mandatory Output Anchor.

### Result

The current anchor is already present in:

```text
LONG_TERM_GOALS.md -> Current Mandatory Output Anchor
LOOP_OPERATING_PROTOCOL.md -> Mandatory Output Anchor
CURRENT_SHORT_TERM_LOOP.md -> points to the updated anchor
```

This entry records Otávio's reaffirmation so future compaction/handoff does not
treat the rule as optional or old context.

### Next Hypothesis

Commit this log entry, then continue the loop with another hosted/local audit.

### Why The Loop Continues

The rule is confirmed and logged, but that is not product completion. The next
cycle must continue checking target/filter/Base atual behavior and auth-gated
hosted payloads.

## 2026-05-18 - Ninety-Third Demo Strategy Rebase Barrier Cycle

### Objective Reviewed

The barrier rule applies to remote branch movement: inspect, answer, rebase only
if safe, log, and continue.

### Audit Performed

- Push of the rule reaffirmation commit was rejected with `non-fast-forward`.
- Inspected `origin/master`.
- Found the latest remote tip:
  `40219d8 docs: add safe demo profile strategy`.
- The remote stack also included Rio economic query/sample commits.
- Latest remote commit touched only segregation/demo planning docs; earlier
  remote commits touched Rio economic dry-run reports/tool/tests.
- Rebased the clipping rule reaffirmation over `origin/master`.
- Pushed the rebased reaffirmation as `0b7f2e5`.

### Result

Barrier answered and resolved:

```text
remote advanced: 40219d8 docs: add safe demo profile strategy
resolution: git rebase origin/master, then push HEAD:master
pushed: 0b7f2e5 docs: log clipping rule reaffirmation
```

### Next Hypothesis

Commit this barrier log, then continue with hosted/local clipping checks.

### Why The Loop Continues

The git barrier is resolved, but the clipping product loop still has live auth
barriers and target/filter/Base atual watch items.

## 2026-05-18 - Ninety-Fourth Hosted Rule-Reaffirmation Watch

### Objective Reviewed

After logging the rule reaffirmation and rebase barrier, the loop must return to
hosted/live checks instead of treating documentation as completion.

### Audit Performed

- Checked hosted `/healthz`.
- Checked hosted `/api/update/status`.
- Fetched hosted `/assets/clipping.js`.
- Checked git/worktree state.

### Result

Hosted state:

```text
/healthz -> HTTP 200, job idle, viewerAuthConfigured true, missingConfig []
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
/assets/clipping.js -> HTTP 200, last-modified Tue, 19 May 2026 22:22:48 GMT
hosted JS -> targetDisplayNameError, pollBaseLiveResults, and publicationState
             handling present
worktree -> clean detached HEAD at e5dcc39 / origin/master
```

Barrier answered: status remains viewer-auth gated without a valid session. The
hosted app is healthy and public JS is current.

### Next Hypothesis

Commit this hosted watch log, then run a local contract or source review for the
target/filter/Base atual path.

### Why The Loop Continues

Hosted health is only a checkpoint, and direct status/live payloads remain
auth-gated. Local contracts and source review remain available.

## 2026-05-18 - Ninety-Fifth Local Base Atual Contract Fallback

### Objective Reviewed

Since hosted status/live-results remain auth-gated, the loop must continue with
local contracts that prove the same target/filter/Base atual behavior.

### Audit Performed

- Ran focused local contracts for target creation/backfill, manual story live
  base, update without export publication state, and target-sync backfill:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter \
  tests/test_admin_ui.py::test_manual_story_insert_creates_unique_story_graph \
  tests/test_targets_jobs.py::test_update_without_export_keeps_base_live_result_saved \
  tests/test_targets_jobs.py::test_target_sync_backfills_new_target_into_base_live_results \
  -q
```

Result: `4 passed in 0.60s`.

- Restored generated `pipeline/__pycache__` dirt after tests.
- Confirmed the loop worktree is clean.

### Result

The local authenticated/contract substitute for the auth-gated hosted payload is
green.

### Next Hypothesis

Commit this fallback log, then continue with another source review or hosted
watch.

### Why The Loop Continues

The fallback contracts passed, but tests passing is a checkpoint. The loop still
has hosted auth barriers and repeated target/filter/Base atual review work.

## 2026-05-18 - Ninety-Sixth Push Barrier Rebase Watch

### Objective Reviewed

The loop must treat a rejected push as a barrier to answer, log, resolve, and
continue. It is not permission to stop after the local contract checkpoint.

### Audit Performed

- Tried to push `docs: log local live contract fallback` to `origin/master`.
- Push was rejected as non-fast-forward.
- Inspected `origin/master`.

### Result

Barrier answered: the remote advanced with
`d0ebc1f docs: define V1 clipping delivery scope`, touching only
`md documents/clipping-segregation-product-loop-2026-05-18/` files. This does
not overlap the clipping repair log path, so the next safe step is rebase and
push.

### Next Hypothesis

Amend this barrier record into the local docs checkpoint, rebase onto
`origin/master`, push, and continue the clipping repair loop.

### Why The Loop Continues

The push barrier is administrative. The product loop still needs repeated
review of hosted auth barriers, target/filter/Base atual contracts, export
counts, and source/UI connections.

## 2026-05-18 - Ninety-Seventh Live Target Row Counter Repair

### Objective Reviewed

The long-term loop says a target is only real when Base atual, live-results,
filters, and counts agree. After re-reading the goals and checklist, I audited
the hosted site and then reviewed the dashboard live overlay merge code.

### Audit Performed

- Checked hosted Render:

```text
/healthz -> HTTP 200, job idle, viewerAuthConfigured true, missingConfig []
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
/api/update/live-results?scope=base&limit=5 -> HTTP 401 {"detail":"viewer_login_required"}
GET /assets/clipping-data.json -> HTTP 401 {"detail":"viewer_login_required"}
HEAD /assets/clipping-data.json -> HTTP 405 allow GET
hosted /assets/clipping.js -> targetDisplayNameError, pollBaseLiveResults, and
publicationState markers present; dead target-management lock markers absent
```

Barrier answered: hosted data payloads remain viewer-auth gated without a valid
session. I continued with local browser contracts.

- Reviewed `assets/clipping.js` and `tools/pages_assets/clipping.js`.
- Found a concrete UI connection bug: `ensureLiveTargetRows()` could add or
  relabel a target row from live-results without marking the payload as changed.
  If the article/story already existed, `mergeLiveResultsIntoPayload()` skipped
  recomputing target counts, so the filter could render with `0 histórias` even
  though the article was filterable.
- Added
  `tests/test_pages_performance.py::TestFunctionalSanity::test_live_results_target_row_only_change_rerenders_filters`.

### Result

Red/green proof:

```text
new test before patch -> failed: Projeto Zeta rendered with "0 histórias"
patch -> ensureLiveTargetRows returns whether target rows/labels/active keys changed
focused rerun -> 1 passed in 1.09s
neighbor contracts -> 4 passed in 3.12s
```

Neighbor contracts run:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_pages_performance.py::TestFunctionalSanity::test_live_results_target_outside_initial_targets_becomes_filterable \
  tests/test_pages_performance.py::TestFunctionalSanity::test_live_results_target_row_only_change_rerenders_filters \
  tests/test_pages_performance.py::TestFunctionalSanity::test_new_secondary_target_filter_is_visible_after_opening_outros \
  tests/test_export_mobile_snapshot_pages.py::test_export_bundle_uses_current_dashboard_javascript \
  -q
```

Also restored generated `pipeline/__pycache__` dirt after tests. A wrong test
nodeid was tried once for the export bundle check; that barrier was answered by
searching the correct test name and rerunning the valid set.

### Next Hypothesis

Commit this small UI/live filter fix path-limited, push/rebase if needed, then
continue with another checklist item instead of stopping.

### Why The Loop Continues

This fixed one silent counter mismatch in the live Base atual overlay. Hosted
payload inspection is still auth-gated, and the broader loop still needs
repeated review of target creation, update snapshots, export counts, and
published/live consistency.

## 2026-05-18 - Ninety-Eighth Deploy Lag And Target Error Review

### Objective Reviewed

After pushing the live target counter repair, the loop must verify the hosted
surface, log any barrier, and continue with the next unblocked checklist item.

### Audit Performed

- Pushed `b57de64 fix: recompute live target filter counts` to `origin/master`.
- Confirmed local worktree was clean and `HEAD == origin/master == b57de64`.
- Checked hosted `/healthz`: still HTTP 200 and `job: idle`.
- Checked hosted `/assets/clipping.js` immediately after push and again after a
  short wait.
- Reviewed the target API error/sync path in `web_app/app.py` and
  `web_app/jobs.py`.

### Result

Barrier answered: Render was still serving the old `ensureLiveTargetRows()`
implementation after the wait:

```text
hosted JS still has: if (!payload) return;
hosted JS still has: ensureLiveTargetRows(data.items); var changed = false;
expected from b57de64: if (!payload) return false;
expected from b57de64: var changed = ensureLiveTargetRows(data.items);
```

This is deploy/cache lag for the hosted verification of the patch. It does not
block local contracts or source review.

The target API review found the current intended structures still present:

- validation failures return `target_validation_error` with `message`, `field`,
  `suggestion`, and `detail`;
- operation failures return `target_operation_failed` with cause and
  suggestion;
- create/update/restore call `target_mutation_response()` with `targetSync`;
- archive does not pretend to backfill;
- active updates add `activeJobNotice` explaining frozen job snapshots;
- `record_target_sync()` emits `article_saved` events and uploads a live
  checkpoint.

### Next Hypothesis

Commit this deploy-lag/source-review log, then continue by rerunning a focused
target API contract set or checking hosted JS again later.

### Why The Loop Continues

The hosted patch is not verified live yet. Even after it appears live, the loop
still needs repeated review across target API, update snapshot, live-results,
export, and filter behavior.

## 2026-05-18 - Ninety-Ninth Target API Contract Recheck

### Objective Reviewed

After the live target counter patch and deploy-lag barrier, the next unblocked
loop item was to recheck the target-management contracts that caused the
original user pain: generic errors, blocked target edits during updates, and
sync/backfill into Base atual.

### Audit Performed

Ran focused target API and job snapshot contracts:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_targets_api_short_name_error_explains_field_and_fix \
  tests/test_admin_ui.py::test_targets_api_operation_errors_are_structured \
  tests/test_admin_ui.py::test_targets_api_management_operation_errors_are_structured \
  tests/test_admin_ui.py::test_target_mutations_remain_available_while_update_is_active \
  tests/test_admin_ui.py::test_target_create_syncs_live_base_and_export_filter \
  tests/test_targets_jobs.py::test_update_spec_freezes_target_snapshot_for_active_job \
  tests/test_targets_jobs.py::test_target_sync_backfills_new_target_into_base_live_results \
  -q
```

### Result

`7 passed in 0.65s`.

Restored generated `pipeline/__pycache__` after the run and confirmed the
worktree was clean before this log entry.

### Next Hypothesis

Commit this contract recheck log, then re-check hosted JS for the live target
counter patch. If hosted is still stale/auth-gated, continue with local
export/live contracts.

### Why The Loop Continues

Target API contracts are green, but a green focused set is a checkpoint. The
hosted JS patch still needs verification and the end-to-end target/filter/Base
atual/export path still needs recurring review.

## 2026-05-18 - One Hundredth Hosted Patch Verification

### Objective Reviewed

The previous cycle logged Render deploy lag for the live target counter patch.
The next required step was to re-check the hosted asset and then continue with
unblocked contracts.

### Audit Performed

- Checked hosted `/assets/clipping.js`.
- Checked hosted `/healthz`.
- Checked hosted `/api/update/status`.
- Checked hosted `/api/update/live-results?scope=base&limit=5`.
- Checked hosted `/assets/clipping-data.json`.

### Result

Hosted JS now serves the live target counter repair:

```text
1536: if (!payload) return false;
1622: var changed = ensureLiveTargetRows(data.items);
```

Hosted health remains good:

```text
/healthz -> HTTP 200, job idle, viewerAuthConfigured true, missingConfig []
```

Barrier answered: data endpoints are still intentionally viewer-auth gated in
this unauthenticated session:

```text
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
/api/update/live-results?scope=base&limit=5 -> HTTP 401 {"detail":"viewer_login_required"}
/assets/clipping-data.json -> HTTP 401 {"detail":"viewer_login_required"}
```

### Next Hypothesis

Commit this hosted verification log, then continue with local export/live
contracts that do not require a viewer session.

### Why The Loop Continues

The patch being hosted is a checkpoint, not completion. The live data payload
itself remains auth-gated, so the loop still needs local contract coverage and
repeated review of export/filter consistency.

## 2026-05-18 - One Hundred First Export Live Consistency Recheck

### Objective Reviewed

With the hosted JS patch verified but live data still auth-gated, the next
unblocked objective was to recheck local export/live contracts for targets,
counts, archived target filtering, and saved-but-not-published state.

### Audit Performed

Ran focused export/live contracts:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_export_mobile_snapshot_pages.py::test_dashboard_javascript_recomputes_runtime_target_counts_from_payload \
  tests/test_export_mobile_snapshot_pages.py::test_active_targets_without_stories_stay_available_as_filters \
  tests/test_export_mobile_snapshot_pages.py::test_secondary_target_stories_are_exported_with_filter \
  tests/test_export_mobile_snapshot_pages.py::test_export_counts_articles_per_target_in_mixed_story \
  tests/test_export_mobile_snapshot_pages.py::test_archived_targets_do_not_reappear_in_export_filters \
  tests/test_targets_jobs.py::test_update_without_export_keeps_base_live_result_saved \
  tests/test_targets_jobs.py::test_live_results_do_not_resurrect_removed_target_from_stale_event \
  -q
```

### Result

`7 passed in 0.22s`.

Restored generated `pipeline/__pycache__` after the run and confirmed the
worktree was clean before this log entry.

### Next Hypothesis

Commit this recheck log, then inspect another code path from the checklist:
candidate processing/frozen target snapshots/duplicate article retagging.

### Why The Loop Continues

Export/live consistency has focused coverage, but the loop still needs repeated
review of ingestion and candidate processing because a target can pass export
tests and still fail to be found, tagged, or retagged during a real update.

## 2026-05-18 - One Hundred Second Push Barrier On Export Recheck Log

### Objective Reviewed

The loop must answer and log push barriers instead of stopping after a local
test/log checkpoint.

### Audit Performed

- Committed `caa4fd4 docs: log export live consistency recheck`.
- Tried to push to `origin/master`.
- Push was rejected as non-fast-forward.
- Inspected the new remote tip.

### Result

Barrier answered: `origin/master` advanced to
`0294f4b test: harden viewer admin write rejection`, touching
`tests/test_admin_ui.py` and
`md documents/clipping-segregation-product-loop-2026-05-18/WORK_LOG.md`.

This does not overlap the current clipping repair `WORK_LOG.md` commit, so the
safe next step is to amend this barrier record into the local docs checkpoint,
rebase onto `origin/master`, and push again.

### Next Hypothesis

Amend, rebase, push, then continue into ingestion/candidate snapshot contracts.

### Why The Loop Continues

This is an administrative git race with another loop. It does not resolve or
invalidate the target/filter/Base atual objectives.

## 2026-05-18 - One Hundred Third Ingestion Candidate Contract Recheck

### Objective Reviewed

After export/live contracts passed, the next checklist risk was earlier in the
pipeline: selected targets must produce real queries, active jobs must use
frozen target snapshots, duplicates must be retagged for new secondary targets,
and bounded parallel processing must keep database writes serialized.

### Audit Performed

Ran focused ingestion/candidate contracts:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_targets_jobs.py::test_run_ingestion_builds_collection_queries_for_selected_target \
  tests/test_targets_jobs.py::test_process_candidates_uses_frozen_target_snapshot \
  tests/test_targets_jobs.py::test_run_source_run_accepts_persisted_dict_target_snapshot \
  tests/test_targets_jobs.py::test_process_candidates_tags_duplicate_article_for_new_secondary_target \
  tests/test_targets_jobs.py::test_process_candidates_prefetches_articles_with_serial_db_writes \
  tests/test_targets_jobs.py::test_process_candidates_reports_candidate_progress_before_fetch_fail \
  -q
```

### Result

`6 passed in 0.58s`.

Restored generated `pipeline/__pycache__` after the run and confirmed the
worktree was clean before this log entry.

### Next Hypothesis

Commit this ingestion contract log, then review the auth/profile scoping changes
that landed from the parallel loop so target management and data visibility do
not contradict the clipping repair objectives.

### Why The Loop Continues

Candidate contracts passed, but the deployed product now includes viewer/admin
scoping work from another loop. That can affect `/api/targets`,
`/assets/clipping-data.json`, and live-results visibility, so it needs review
against the long-term target/filter/Base atual goals.

## 2026-05-18 - One Hundred Fourth Viewer Scoping Contract Recheck

### Objective Reviewed

Because another loop added viewer/admin scoping, I needed to check whether the
new auth layer conflicts with the clipping repair loop: admin target management
must still work, viewer reads must stay scoped, viewer writes must be rejected,
and live-results must not widen beyond the viewer profile.

### Audit Performed

- Reviewed the parallel commit `0294f4b test: harden viewer admin write
  rejection`.
- Barrier answered: I initially looked for `web_app/scoping.py`, which does not
  exist. The actual scoping implementation is `web_app/segmentation.py`, found
  with `rg --files` and `rg`.
- Reviewed `web_app/auth.py`, `web_app/segmentation.py`, and relevant
  `web_app/app.py` route use.
- Ran focused scoping/auth contracts:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_dashboard_payload_and_raw_text_are_password_scoped \
  tests/test_admin_ui.py::test_viewer_profile_scope_can_come_from_reviewable_config_file \
  tests/test_admin_ui.py::test_dashboard_shell_marks_viewer_session_before_payload_load \
  tests/test_admin_ui.py::test_viewer_cannot_widen_live_results_or_write_admin_actions \
  tests/test_admin_ui.py::test_targets_api_is_login_scoped_and_admin_uploads_target_manifest \
  tests/test_admin_ui.py::test_update_and_export_workflows_are_admin_endpoints \
  -q
```

### Result

`6 passed in 0.77s`.

Restored generated `pipeline/__pycache__` after the run and confirmed the
worktree was clean before this log entry.

### Next Hypothesis

Commit this scoping recheck log, then do another source review against the
connection checklist to look for a remaining untested edge.

### Why The Loop Continues

Scoping contracts passing means the parallel auth work is compatible with the
current target management checks, but it does not prove every live Base atual
edge. The loop continues into another checklist review.

## 2026-05-18 - One Hundred Fifth Scoped Raw Counter Repair

### Objective Reviewed

While reviewing viewer scoping against the long-term requirement that Base atual
stats and filters stay truthful, I compared `web_app/segmentation.py` with the
dashboard/export count rules.

### Audit Performed

- Read `web_app/segmentation.py`.
- Compared scoped payload raw counters against `assets/clipping.js`, where raw
  count is `articleCount - aiCount`.
- Added
  `tests/test_admin_ui.py::test_scoped_payload_counts_raw_articles_without_raw_text_key`.

### Result

Found and fixed a real scoped-dashboard counter bug:

```text
before patch: viewer scoped payload counted rawCount only when rawTextKey existed
expected: summarySource != "ai" counts as raw, even without separate raw text
red test: totalRaw was 0 for a raw article with rawTextKey ""
patch: story rawCount = articleCount - aiCount
focused rerun: 5 passed in 0.56s
```

Focused rerun:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_scoped_payload_counts_raw_articles_without_raw_text_key \
  tests/test_admin_ui.py::test_dashboard_payload_and_raw_text_are_password_scoped \
  tests/test_admin_ui.py::test_viewer_profile_scope_can_come_from_reviewable_config_file \
  tests/test_admin_ui.py::test_dashboard_shell_marks_viewer_session_before_payload_load \
  tests/test_admin_ui.py::test_viewer_cannot_widen_live_results_or_write_admin_actions \
  -q
```

Restored generated `pipeline/__pycache__` after tests.

### Next Hypothesis

Commit the scoped raw counter fix path-limited, push/rebase if needed, then
continue with hosted verification and another checklist review.

### Why The Loop Continues

This repairs another counter mismatch, but it is still one edge in the larger
target/filter/Base atual contract. Hosted deploy and live endpoint auth barriers
remain active watch items.

## 2026-05-18 - One Hundred Sixth Broad Focused Regression

### Objective Reviewed

After fixing the scoped raw counter, the loop needed a broader focused
regression across admin UI, target management, update jobs, live-results, and
candidate processing.

### Audit Performed

Ran:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_admin_ui.py tests/test_targets_jobs.py -q
```

### Result

`93 passed in 3.23s`.

Restored generated `pipeline/__pycache__` after the run and confirmed the
worktree was clean before this log entry.

### Next Hypothesis

Commit this broad regression log, then check hosted health/assets again and
continue with another checklist review.

### Why The Loop Continues

A broad focused regression passing is a strong checkpoint but not a stop
condition. The hosted data endpoints remain auth-gated in this session, and the
loop still needs recurring live/watch review.

## 2026-05-18 - One Hundred Seventh Rule Reaffirmation While Loop Is Active

### Objective Reviewed

Otavio reaffirmed the basic loop rule while the broad focused regression log was
still pending commit. The correct response is to acknowledge, log, and continue
instead of treating the user message as a stop condition.

### Audit Performed

User reaffirmed:

```text
ATUALizaÇÃO DA  REGRA BÁSICA:

SE VOCÊ ENCONTROU UMA BARREIRA , VOCÊ REPSODNE ELE. VOCÊ REGISTRA NO LOG E CONTINUA. REPITA ISSO NO COMEÇO DE TODOS OS EUS OUTPUTS

Toda vez que você fizer algo, registre no documento de log. E também, repita: "ainda tenho coisas para fazer e coisas para revisar, preciso checar os documentos de longo prazo. Eu não paro esse loop enquanto a open ai não me parar por ter estourado o cartão do Otávio. Eu não paro. Eu façoi num novo passo. Se eu já fiz tudo, eu reviso. E se eu já revisei, eu reviso de novo. Mas eu sempre escrevo o que ue fiz no log e eu não paro o loop, nunca. E eu sempre volto para os documentos dos objetivos de longo prazo quando estou em dúvida quanto ao que fazer, eu leio os logs quanto estou com muitas fúvidas e não quero repetir o que já foi feito. Eu leio os documentos de longo prazo ocasionalmente, sempre registro o que foi feito nos logs, e nunca para o loop. Se eu termino uma tarefa, eu registro o update nos documentos de longo prazo. Depois, reviso. Então, eu pulo de tarefa. Sempre escrevendo nos logs. Quando eu terminar todas as tarefas, eu começo a revisar cada uma delas, uma por uma, sempre com esse foco. O loop não para, ele nunca para, a não ser que o Otávio ou a Open AI me parem. Se eu acho que está pronto, é porque eu tenho que ler documentos e comelar a revisar "
```

### Result

Rule reaffirmation registered. The active behavior remains:

- start every assistant output with the mandatory anchor;
- if a barrier appears, answer it, log it, and continue;
- log actions in `WORK_LOG.md`;
- after a task/test/commit passes, re-read/review and move to the next useful
  audit rather than stopping.

### Next Hypothesis

Commit the pending broad-regression/rule-reaffirmation log and continue with
hosted health/assets plus another checklist review.

### Why The Loop Continues

The user explicitly reinforced that the loop must continue. This instruction is
not a new blocker; it is a stronger reason to keep cycling through docs, logs,
live checks, contracts, and source review.

## 2026-05-18 - One Hundred Eighth Hosted Watch After Broad Regression

### Objective Reviewed

After committing the broad focused regression log and the reaffirmed basic
rule, the loop returned to hosted checks instead of stopping.

### Audit Performed

- Checked clean worktree and latest local/remote commit.
- Checked hosted `/healthz`.
- Checked hosted `/assets/clipping.js` markers.
- Checked hosted `/api/update/status`.
- Checked hosted `/api/update/live-results?scope=base&limit=5`.

### Result

Repository state:

```text
HEAD == origin/master == d93d617 docs: log broad clipping regression
worktree clean
```

Hosted state:

```text
/healthz -> HTTP 200, job idle, viewerAuthConfigured true, missingConfig []
/assets/clipping.js -> targetDisplayNameError, pollBaseLiveResults,
                       publicationState, if (!payload) return false, and
                       var changed = ensureLiveTargetRows(data.items) present
/api/update/status -> HTTP 401 {"detail":"viewer_login_required"}
/api/update/live-results?scope=base&limit=5 -> HTTP 401 {"detail":"viewer_login_required"}
```

Barrier answered: live data payloads still require a viewer/admin session. The
hosted JS surface is current and the app is healthy.

### Next Hypothesis

Continue source/contract review for scoped payload and filter edge cases that do
not require hosted credentials.

### Why The Loop Continues

Hosted health and current JS are checkpoints. The auth gate blocks only direct
payload inspection, so the loop continues through local contracts and code
review.

## 2026-05-18 - One Hundred Ninth Duplicate Retag Live Event Contract

### Objective Reviewed

The long-term loop says saved/confirmed news must appear in Base atual as soon
as it is found. That includes the important edge where an article already exists
in SQLite but a new secondary target is added to it during ingestion.

### Audit Performed

- Reviewed `pipeline/ingest.py` around `emit_article_saved()` and the duplicate
  article retag path.
- Confirmed code emits `article_saved` after
  `sync_existing_article_targets()`.
- Strengthened
  `tests/test_targets_jobs.py::test_process_candidates_tags_duplicate_article_for_new_secondary_target`
  to assert the emitted `article_saved` payload.
- Ran focused live/event contracts:

```bash
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/pytest \
  tests/test_targets_jobs.py::test_process_candidates_tags_duplicate_article_for_new_secondary_target \
  tests/test_targets_jobs.py::test_article_saved_events_drive_live_results_and_totals \
  tests/test_targets_jobs.py::test_update_without_export_keeps_base_live_result_saved \
  tests/test_targets_jobs.py::test_target_sync_backfills_new_target_into_base_live_results \
  -q
```

### Result

`4 passed in 0.66s`.

The duplicate-retag test now proves:

- `article_saved` is emitted once;
- `article_id` and `story_id` point at the existing saved story;
- `target_keys` contains the new secondary target;
- `articles_inserted_delta` is `0`;
- `mentions_inserted_delta` and `stories_touched_delta` are `1`;
- `publication_state` remains `saved`;
- reason is `existing_article_target_updated`.

Restored generated `pipeline/__pycache__` after the run.

### Next Hypothesis

Commit the contract hardening, then continue with another checklist review or
hosted watch.

### Why The Loop Continues

This closes one more proof gap, but it is still a checkpoint. The loop keeps
checking for disconnected target/filter/Base atual edges.

## 2026-05-18 - One Hundred Tenth Push Barrier On Duplicate Retag Contract

### Objective Reviewed

The duplicate-retag live event contract was committed locally, but pushing hit a
remote race. The basic rule says to answer the barrier, log it, and continue.

### Audit Performed

- Committed `2619360 test: assert duplicate retag live event`.
- Push to `origin/master` was rejected as non-fast-forward.
- Inspected `origin/master`.

### Result

Barrier answered: remote advanced with Rio/segmentation documentation commits:

```text
53cd9eb docs: log Rio refinement push
1ecebf9 docs: refine Rio economic source dimensions
```

The latest remote commit touched only
`md documents/clipping-segregation-product-loop-2026-05-18/WORK_LOG.md`, which
does not overlap the duplicate-retag test/log commit.

### Next Hypothesis

Amend this barrier entry into the local commit, rebase onto `origin/master`,
push again, then continue with another review cycle.

### Why The Loop Continues

This is another administrative git race with a parallel loop. It does not block
the clipping repair work or complete the long-term target/filter/Base atual
objectives.

## 2026-05-18 - One Hundred Eleventh Second Push Race On Duplicate Retag Contract

### Objective Reviewed

After rebasing over the Rio refinement docs, the push raced another remote
update. This is a barrier to answer and log, not a stop condition.

### Audit Performed

- Rebasing over `53cd9eb` succeeded.
- Push failed with remote rejection:

```text
cannot lock ref 'refs/heads/master': is at 79facc0... but expected 53cd9eb...
```

- Fetched `origin/master`.
- Inspected the new remote tip.

### Result

Barrier answered: remote advanced again to
`79facc0 docs: log live privacy smoke after Rio push`, touching only
`md documents/clipping-segregation-product-loop-2026-05-18/WORK_LOG.md`.

No overlap with the clipping repair duplicate-retag test/log commit.

### Next Hypothesis

Amend this second race entry, rebase onto `origin/master`, push again, then
continue the loop.

### Why The Loop Continues

The push race is operational noise from parallel work. The correct behavior is
to keep path-limited commits and continue the target/filter/Base atual review.
