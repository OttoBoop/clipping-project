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
