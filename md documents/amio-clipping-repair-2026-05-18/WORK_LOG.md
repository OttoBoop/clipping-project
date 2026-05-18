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
