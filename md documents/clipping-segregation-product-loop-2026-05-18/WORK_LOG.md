# Work Log - Clipping Segregation And Product Loop

_Created 2026-05-18 by Atlas/Codex. Append-only unless correcting a factual
typo in the current entry._

This log records what happened, what was verified, what was inherited, and what
the next loop must remember.

## 2026-05-18 - Documentation loop started

### User Prompt Anchors

Otavio's instructions that define this loop:

> "A principal tarefa agora e conseguir segregar o site."

> "A gente pode usar esse site como base e colocar um sistema de senhas, que permite que cada cliente veja apenas as noticias que lhe interessam."

> "No fundo, tudo tem o mesmo backend."

> "O primeiro ponto e mais importante e que eu preciso que voce reformule as perguntas."

> "Para o plano de longo prazo, o foco deve ser simplesmente colocar esses objetivos."

> "Voce pode se fazer perguntas, escrever pequenos documentos e responder elas voce mesmo, desde que voce faca os logs."

> "Tambem e importante notar que o repo esta bem sujo, entao a primeira tarefa mesmo e ver como tudo de fato esta funcionando."

### Correction

I initially asked architecture-choice questions too early. That was wrong for
this moment. The correct first deliverable is a loop memory and a product
contract: login, profile segregation, sellability, no fake UI, and systemic
checks before technical choices.

### Inherited Worktree State

Fresh status before creating this loop showed `master...origin/master [ahead 7]`
with inherited dirty files:

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
?? data/reports/shakira-public-filter-20260505.png
?? data/reports/shakira-public-filter-20260506.png
?? data/reports/shakira-public-filter-selected-20260505.png
?? "md documents/LONG_TERM_GOALS_FOR_THE_CLIPPING_ONLINE_PROJECT.md"
?? "md documents/PIPELINE.md"
?? tests/test_live_audit_script.py
?? tests/test_sprint_regression_harness.py
?? tools/live_audit.py
```

Assumption: these are inherited from other agents or previous loops and must
not be reverted or swept into this loop's commits.

### Coordination Claim Decision

The shared coordination file
`md documents/Who_Is_Doing_What-WRITE_WHAT_YOU'RE_DOING_HERE.md` already had
an inherited uncommitted hunk about `/api/update/status` performance. Appending
there and committing the full file would risk bundling another agent's work.

Decision: do not edit that shared file in the docs-only commit. Instead, create
`README_FOR_ACTIVE_AI.md` in this loop folder as the coordination surface most
likely to be read by another agent entering this new loop. If a later agent can
stage hunks safely, it may append a short claim to the shared file.

### Files Created In This Documentation Pass

- `LONG_TERM_GOALS.md`
- `DEPENDENCY_MAP.md`
- `CURRENT_SHORT_TERM_LOOP.md`
- `SYSTEM_REVIEW_CHECKLIST.md`
- `WORK_LOG.md`
- `COMMIT_AND_DIRTY_WORKTREE_RULES.md`
- `README_FOR_ACTIVE_AI.md`

### Next Loop After Docs Commit

After the docs-only checkpoint, the technical loop should implement functional
password-gated segregation on the existing FastAPI app.

## 2026-05-18 - Loop Resumed After Scope Failure

### Why This Entry Exists

Otavio pointed out that the previous pass did not behave like a durable loop:
it treated one implementation checkpoint as a finish line instead of returning
to `LONG_TERM_GOALS.md`, asking the next operational questions, logging the
answers, and continuing from the next objective.

This entry restarts the loop with that discipline.

### Current Repository State Checked

Current `git status --short --branch`:

```text
## master...origin/master
 M pipeline/__pycache__/collectors.cpython-314.pyc
 M pipeline/__pycache__/database.cpython-314.pyc
 M pipeline/__pycache__/ingest.cpython-314.pyc
 M pipeline/__pycache__/matcher.cpython-314.pyc
 M pipeline/__pycache__/settings.cpython-314.pyc
?? data/reports/shakira-public-filter-20260505.png
?? data/reports/shakira-public-filter-20260506.png
?? data/reports/shakira-public-filter-selected-20260505.png
?? "md documents/LONG_TERM_GOALS_FOR_THE_CLIPPING_ONLINE_PROJECT.md"
?? "md documents/PIPELINE.md"
?? tests/test_live_audit_script.py
?? tests/test_sprint_regression_harness.py
?? tools/live_audit.py
```

No staged changes were present when this loop was resumed.

### Problem Found

The password/profile implementation that previously existed in commit
`9e05c08` is not present in the current working tree. It was explicitly removed
by commit `6fd0bac` (`revert: remove password segregation from target repair
loop`).

The revert was directionally correct for the target-repair loop: password and
product segregation should not be smuggled into that other loop. But the result
for this product loop is that Axis 1 from `DEPENDENCY_MAP.md` is still open:
the current app does not yet provide functional password-gated segregation.

### Questions Asked And Answered By This Loop

**Q: Which long-term goal is currently blocking everything else?**

A: Axis 1, segregation and login. Product packaging, Rio economic methodology,
market research, and new deploy/repo decisions still depend on scoped access
working in the current app.

**Q: Did the previous password work fail because the code idea was impossible?**

A: No. It failed operationally because it contaminated the target-repair loop
and was treated as a finished checkpoint instead of a continuing product loop.
The next attempt must be owned only by this folder and logged here.

**Q: Should this loop touch the Shakira/debug or target-repair long-term plans?**

A: No. This loop can read them for collision awareness, but it must not rewrite
their goals or redirect their agents. The coordination note must be narrowed so
other agents do not treat password segregation as their active task.

**Q: What is the next technical action?**

A: Reintroduce password/profile segregation as a product-loop implementation,
not as a target-repair patch. Before code, narrow `README_FOR_ACTIVE_AI.md`.
After code, verify with the checklist: logged-out blocked, viewer scoped JSON,
viewer raw text scoped, direct API widening blocked, admin still works.

**Q: What must not be done in this iteration?**

A: Do not create a new repo/site. Do not sweep inherited pycache, Shakira
screenshots, moved legacy docs, or audit scripts into commits. Do not ask
Otavio architecture questions that can be answered by reading the repo.

### Next Action

1. Narrow the active-AI coordination note so it does not pull Shakira/debug or
   target-repair agents into password work.
2. Recheck the current FastAPI/static route shape.
3. Reimplement the smallest server-side scoped login layer in this loop's file
   set.
4. Run focused tests before any broader suite.

## 2026-05-18 - Product Loop Reimplementation Attempt

### Changes Made In This Loop

After logging the scope failure, this loop reintroduced password/profile
segregation as product-loop work rather than target-repair work.

Touched product-loop paths:

- `web_app/auth.py`
- `web_app/app.py`
- `web_app/segmentation.py`
- `tests/test_admin_ui.py`
- `md documents/clipping-segregation-product-loop-2026-05-18/README_FOR_ACTIVE_AI.md`
- `md documents/clipping-segregation-product-loop-2026-05-18/WORK_LOG.md`

The implementation:

- supports admin and viewer sessions;
- supports viewer passwords via `CLIPPING_VIEWER_PASSWORDS`;
- maps viewers to profiles such as `flavio`, `shakira`, `rio_economico`, and
  `demo_cliente`;
- serves `assets/clipping-data.json` and `assets/clipping-raw-texts.json`
  through authenticated scoped handlers;
- scopes targets, stories, articles, raw texts, classifications, live results,
  and status responses server-side;
- requires admin for update/export/target mutation/category mutation and
  classification writes;
- lets viewer sessions fetch CSRF only so they can log out cleanly.

### Questions Asked And Answered By This Loop

**Q: Did this patch accidentally depend on frontend-only filtering?**

A: No. The server now filters the JSON and raw-text payloads before returning
them to the browser. Frontend hiding remains useful for visual cleanliness, but
it is not the security boundary.

**Q: Can a Shakira viewer widen scope with query params?**

A: Focused tests cover `/api/update/live-results?target_key=flavio_valle` under
a Shakira viewer and expect an empty result instead of Flavio data.

**Q: Did the change break target/update operator workflows?**

A: Focused tests cover admin login before update/export/target operations. They
still pass after moving those routes behind admin sessions.

**Q: Are full-suite failures caused by this segregation work?**

A: The full suite has two live-source failures unrelated to login/scoping:
Agenda do Poder WordPress returned 0 articles and CONIB internal search
returned 0 articles. The non-live suite passed.

### Verification

Passed:

```bash
python -m py_compile web_app/auth.py web_app/segmentation.py web_app/app.py
```

Passed:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py -q
```

Result: `31 passed in 1.87s`.

Passed:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `93 passed in 2.80s`.

Failed only on live-source validation:

```bash
.venv_playwright/bin/pytest -q
```

Result: `2 failed, 250 passed, 1 skipped in 474.03s`.

Failures:

- `tests/test_f5_live_validation.py::test_wordpress_agendadopoder_returns_articles`
- `tests/test_f5_live_validation.py::test_conib_internal_search_returns_articles`

Passed non-live:

```bash
.venv_playwright/bin/pytest -m 'not live' -q
```

Result: `240 passed, 13 deselected in 13.08s`.

### Next Question For The Loop

Should the next product-loop step be live app smoke with real viewer passwords,
or a review of profile definitions and allowed target keys? The loop answer is:
do live local smoke first, because the short-term promise is functional
password-gated segregation on the current app. Profile taxonomy can improve
after the access boundary is visibly proven.

## 2026-05-18 - Local HTTP Smoke For Scoped Login

### Server

Started local FastAPI server:

```bash
CLIPPING_ADMIN_PASSWORD='test-password' \
CLIPPING_SESSION_SECRET='local-segmentation-secret' \
CLIPPING_VIEWER_PASSWORDS='{"flavio":"viewer-flavio","shakira":"viewer-shakira","rio_economico":"viewer-rio","demo_cliente":"viewer-demo"}' \
.venv_playwright/bin/python -m uvicorn web_app.app:app --host 127.0.0.1 --port 8765
```

### Smoke Results

- Logged-out `GET /assets/clipping-data.json`: `401`.
- Logged-out `GET /`: `200` with login page and without the dashboard runner.
- Shakira login: `200`, role `viewer`, profile `shakira`.
- Shakira `GET /assets/clipping-data.json`: `200`, role `viewer`, profile
  `shakira`, targets `[]`, stories `0`, articles `0`.
- Shakira `GET /assets/clipping-raw-texts.json`: `200`, raw keys `0`.
- Shakira direct widening attempt:
  `GET /api/update/live-results?target_key=flavio_valle&limit=10`: `200`,
  count `0`, items `0`.
- Flavio login: `200`, role `viewer`, profile `flavio`.
- Flavio `GET /assets/clipping-data.json`: targets
  `['flavio_valle', 'pedro_duarte', 'pedro_angelito', 'bernardo_rubiao']`,
  stories `458`, articles `697`.
- Flavio direct widening attempt:
  `GET /api/update/live-results?target_key=shakira&limit=10`: `200`,
  count `0`, items `0`.
- Admin login: `200`, role `admin`, profile `admin`.
- Admin `GET /assets/clipping-data.json`: targets `4`, stories `458`,
  articles `805`.

### Interpretation

The local asset snapshot still does not contain Shakira target rows, so the
Shakira profile is a clean empty view locally. That is acceptable for this
loop's boundary check: empty scoped profiles must not fall back to showing
Flavio/Rio/client data.

Next product-loop question: should this profile map stay hard-coded by default,
or should it move to a repo/config JSON with explicit owner review? Loop answer:
keep the default for the first sprint, but the next sprint should create a
reviewable profile configuration file before selling this to real clients.

## 2026-05-18 - Next Loop Question: Reviewable Client Profile Map

### Question

Can Otavio or a future agent review which target keys belong to each client
without editing Python code or touching passwords?

### Answer

Not yet. The current implementation can override profiles through
`CLIPPING_VIEWER_PROFILES`, but that hides an important product decision inside
environment JSON. For a sellable clipping product, profile scope is not just a
deployment setting; it is the contract that prevents client contamination.

### Decision

Create a password-free, reviewable profile file in the repo. Passwords remain
in environment variables. Profile scope becomes:

1. safe built-in defaults;
2. `data/viewer_profiles.json` for explicit repo-reviewed scope;
3. optional env override for Render/emergency operations.

This keeps secrets out of Git while making client visibility auditable.

## 2026-05-18 - Reviewable Viewer Profile Config Implemented

### Changes Made

- Added `data/viewer_profiles.json` as a password-free profile scope file.
- Updated `web_app/segmentation.py` so profile scope is loaded in this order:
  built-in safe defaults, `data/viewer_profiles.json`, then
  `CLIPPING_VIEWER_PROFILES`.
- Added optional `CLIPPING_VIEWER_PROFILES_PATH` for tests and emergency
  operator use.
- Added safe health metadata: `viewerProfilesConfigured`.
- Added a regression test proving a viewer profile can be remapped by a
  reviewable config file without changing Python or storing passwords in Git.

### Verification

Passed:

```bash
python -m py_compile web_app/auth.py web_app/segmentation.py web_app/app.py
.venv_playwright/bin/pytest tests/test_admin_ui.py -q
```

Result: `32 passed in 1.82s`.

Passed:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `94 passed in 2.58s`.

Passed:

```bash
.venv_playwright/bin/pytest -m 'not live' -q
```

Result: `241 passed, 13 deselected in 13.70s`.

Local server smoke after restart:

- `GET /healthz`: `200`, with `authConfigured`, `loginConfigured`,
  `viewerAuthConfigured`, and `viewerProfilesConfigured` all true.
- Flavio viewer login: `200`, role `viewer`, profile `flavio`.
- Flavio scoped data: label `Flavio Valle`, targets
  `['flavio_valle', 'pedro_duarte', 'pedro_angelito', 'bernardo_rubiao']`,
  stories `458`.

### Next Review Question

The next failure class to check is public-file leakage after export. The FastAPI
route now protects same-origin `/assets/clipping-data.json`, but static export
files still intentionally contain full snapshots for Wix/offline contexts. The
loop must decide whether client product access can rely on static exports at
all, or whether private clients must use the FastAPI app only.

## 2026-05-18 - Static Export Boundary Reviewed

### Question

Can static exports be treated as the password-gated product surface for paid
clients?

### Answer

No. Static export bundles intentionally write JSON snapshots beside static HTML
so the bundle can run offline or in Wix/GitHub Pages contexts. That can be
useful for review and public/non-private publishing, but it is not a session
boundary.

### Changes Made

- Added `STATIC_EXPORT_POLICY.md` to this loop folder.
- Added a regression test proving the FastAPI app does not serve
  `data/reports/...` report exports as part of the private app surface.

### Verification

Passed:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `46 passed in 2.03s`.

### Decision For Future Agents

Do not propose GitHub Pages, Wix, or static report bundles as the private paid
client surface. The private product surface is the FastAPI login plus
server-side scoped payloads/APIs. A future scoped static export may be built,
but it must be treated as a separate deliverable with its own leakage tests.

## 2026-05-18 - Viewer Shell Fake-UI Review

### Question

Does a logged-in viewer briefly receive operator controls before the scoped
payload arrives?

### Answer

Before this pass, yes in principle: the HTML shell was static and contained the
runner/target-management controls. The JS hid controls after reading the scoped
payload, but the product promise is cleaner if the server marks the session role
before payload fetch.

### Changes Made

- FastAPI `/` now injects `data-clipping-session-role` and
  `data-clipping-session-profile` into the dashboard shell.
- Viewer sessions receive `<body class="viewer-readonly">`.
- Dashboard JS reads the initial session role and applies viewer controls before
  loading the JSON payload.
- Dashboard CSS hides runner/target-management surfaces immediately when
  `viewer-readonly` is present.
- Added a regression test for viewer shell role/profile marking.
- Kept `assets/clipping.js` and `tools/pages_assets/clipping.js` synchronized.
- Kept `assets/clipping.css` and `tools/pages_assets/clipping.css`
  synchronized.

### Verification

Passed:

```bash
python -m py_compile web_app/app.py web_app/segmentation.py web_app/auth.py
diff -q assets/clipping.js tools/pages_assets/clipping.js
diff -q assets/clipping.css tools/pages_assets/clipping.css
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `47 passed in 2.03s`.

Passed:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `96 passed in 2.72s`.

Local HTTP smoke:

- Shakira viewer login: `200`.
- Shakira viewer `/`: `200`, contains `class="viewer-readonly"`,
  `data-clipping-session-role="viewer"`, and
  `data-clipping-session-profile="shakira"`.
- Admin login: `200`.
- Admin `/`: `200`, contains `data-clipping-session-role="admin"` and does not
  contain `class="viewer-readonly"`.

### Next Review Question

The next product-loop review should inspect whether admin-only write endpoints
consistently require CSRF. Login scoping prevents viewers from writing, but
admin mutation routes should also preserve CSRF discipline where feasible.

## 2026-05-18 - Admin Mutation CSRF Review

### Question

After adding viewer/admin sessions, do admin-only mutation endpoints also
require CSRF, or can another site trigger writes through the admin cookie?

### Problem Found

Several routes required admin login but did not require CSRF:

- `/api/update/start`
- `/api/update/resume`
- `/api/update/cancel`
- `/api/export`
- `/api/targets`
- `/api/targets/{target_key}`
- `/api/targets/{target_key}/archive`
- `/api/targets/{target_key}/restore`
- `/api/categories`
- `/api/classifications`

The dashboard JS had `csrfToken` support but did not fetch `/api/csrf`, so
simply enforcing CSRF server-side would have broken the operator UI.

### Changes Made

- Added `require_csrf(request)` to admin mutation routes.
- Added dashboard JS `ensureCsrfToken()` and made `apiPost`/`apiPatch` fetch
  `/api/csrf` before sending writes.
- Kept `assets/clipping.js` and `tools/pages_assets/clipping.js` synchronized.
- Updated tests so intended admin writes send CSRF.
- Expanded the missing/bad-CSRF regression test beyond manual story/logout.
- Updated the sprint regression cancel test to use CSRF.

### Verification

Passed:

```bash
python -m py_compile web_app/app.py web_app/auth.py web_app/segmentation.py
diff -q assets/clipping.js tools/pages_assets/clipping.js
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_sprint_regression_harness.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `54 passed in 2.22s`.

Passed:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py tests/test_export_mobile_snapshot_pages.py tests/test_sprint_regression_harness.py -q
```

Result: `104 passed in 3.04s`.

Passed:

```bash
.venv_playwright/bin/pytest -m 'not live' -q
```

Result: `244 passed, 13 deselected in 13.82s`.

Local HTTP smoke:

- Admin login: `200`.
- `POST /api/update/start` without CSRF: `403`, detail
  `csrf_check_failed`.
- `GET /api/csrf`: `200`.
- `POST /api/update/start` with CSRF: passed the CSRF boundary and reached the
  expected local environment error, `503 persistent_storage_not_configured`.

### Next Review Question

The next product-loop review should inspect classification/category read
surface. Categories are currently shared taxonomy; classifications are scoped by
target. If future clients get private custom taxonomy, category reads may need
profile scoping too.

## 2026-05-18 - Classification And Category Read Surface Review

### Question

Do category or classification reads currently leak cross-client data?

### Answer

Classifications are scoped by target via `scoped_classifications()`. The
dashboard payload also filters per-article `classifications` to the allowed
article target keys.

Categories are not scoped. Today they are seeded from the shared base taxonomy
(`Causa Animal`, `Economia`, `Turismo`, etc.) and are not client records by
themselves. That is acceptable for this first product loop, but only while the
taxonomy remains shared and non-private.

### Change Made

Updated `SYSTEM_REVIEW_CHECKLIST.md` so future loops explicitly check:

- admin mutation CSRF;
- reviewable profile scopes;
- readonly viewer shell before payload load;
- shared-vs-private category taxonomy;
- static export not being the private paid-client surface.

### Decision

Do not add profile-specific category tables in this sprint. If paid clients get
custom private taxonomy later, `/api/categories` must become scoped before that
feature is exposed to viewers.

## 2026-05-18 - Deployment Environment Memory Added

### Question

Can a future agent configure the password/product loop without hardcoding
passwords, creating another site, or guessing the Render env contract?

### Answer

Not clearly enough before this pass.

### Change Made

Added `DEPLOYMENT_ENVIRONMENT.md` documenting:

- required env vars;
- optional profile override env vars;
- the password-free profile scope file;
- the FastAPI-only private product surface;
- local smoke command and expected checks.

### Decision

Passwords remain env-only. `data/viewer_profiles.json` is reviewable product
scope, not a secret store.

## 2026-05-18 - Active Next Action File Added

### Question

How does this loop avoid stopping again after a single technical checkpoint?

### Answer

It needs an explicit active-action file that future agents can read after the
long-term goals and before choosing work.

### Change Made

Added `ACTIVE_NEXT_ACTION.md` with:

- current phase;
- completed local working-tree capabilities;
- latest verification state;
- next technical step;
- next product step after browser smoke;
- explicit "do not do next" boundaries.

### Current Next Step

Run Playwright browser smoke against the local FastAPI app and record results
here.

## 2026-05-18 - Playwright Browser Smoke Completed

### Question

Does the actual browser experience match the server-side segregation contract?

### Smoke Environment

Local FastAPI server:

```text
http://127.0.0.1:8765
```

Environment:

```text
CLIPPING_ADMIN_PASSWORD=test-password
CLIPPING_SESSION_SECRET=local-segmentation-secret
CLIPPING_VIEWER_PASSWORDS={"flavio":"viewer-flavio","shakira":"viewer-shakira","rio_economico":"viewer-rio","demo_cliente":"viewer-demo"}
```

### Browser Checks

Passed:

```text
logged_out_login_shell: PASS
flavio_viewer_readonly_shell: PASS
flavio_operator_controls_hidden: PASS
flavio_targets_present_without_shakira: PASS
shakira_viewer_clean_empty: PASS
shakira_no_flavio_text: PASS
admin_operator_controls_visible: PASS
```

### Interpretation

The browser UI now matches the first product promise locally:

- logged-out users see login, not dashboard data;
- Flavio viewer sees a readonly scoped view without Shakira targets;
- Shakira viewer gets a clean empty local view instead of Flavio leakage;
- admin sees operator controls.

### Next Product Step

Start Axis 2 packaging notes: define the first sellable client package without
adding billing/payment or new repos.

## 2026-05-18 - Axis 2 First Sellable Package Drafted

### Question

Once scoped login works locally, what exactly is the first thing Otavio can sell
without creating a new repo/site or overpromising custom automation?

### Answer

A readonly, password-gated, scoped clipping dashboard operated by Otavio/admin.
The client gets clean access to its own monitored targets and articles; Otavio
keeps update, target-management, export, and classification controls.

### Change Made

Added `FIRST_SELLABLE_PACKAGE.md` defining:

- product promise;
- minimum paid offer;
- what V1 deliberately does not include;
- operator responsibilities;
- cost discipline;
- demo shape;
- pricing questions for later market research;
- V1 acceptance criteria.

### Decision

Do not add billing/payment or a separate client site before production Render
segregation is verified.

## 2026-05-18 - Axis 3 Rio Economic Indicator Track Drafted

### Question

How can the future Rio economic indicator start without polluting Flavio or
paid-client views?

### Answer

Treat Rio economic monitoring as a separate profile/project and start with
methodology, dimensions, term-design risks, and validation loops. Do not add a
large generic target list to the Flavio view.

### Change Made

Added `RIO_ECONOMIC_INDICATOR_TRACK.md` documenting:

- Rio economic monitoring as a separate profile/project;
- possible output formats;
- candidate dimensions;
- term-design risks;
- safer query patterns;
- validation loop before any numeric index;
- segregation rules;
- future implementation questions.

### Decision

No collection/index implementation yet. The next technical prerequisite remains
production verification of password-gated segregation.

## 2026-05-18 - Render Production Checklist Added

### Question

What must be checked after deploy before anyone treats segregation as production
ready?

### Answer

Local tests are necessary but not enough. Production must prove env secrets,
profile config, logged-out blocking, viewer scoping, admin controls, admin CSRF,
and the static-export boundary on the actual Render URL.

### Change Made

Added `RENDER_PRODUCTION_CHECKLIST.md`.

### Decision

Do not mark the product ready to sell until this checklist is executed and the
results are appended to `WORK_LOG.md`.

## 2026-05-18 - Market Research Plan Added

### Question

Can this loop prepare market research without hallucinating prices or treating
unresearched assumptions as facts?

### Answer

Yes: create the research plan, buyer hypotheses, evidence fields, and interview
questions, but do not claim market findings until a sourced research pass is
actually run.

### Change Made

Added `MARKET_RESEARCH_PLAN.md`.

### Decision

Do not execute market research before production segregation is verified or
before explicitly doing a sourced web research pass with dated links.

## 2026-05-18 - Initial Sourced Market Research Pass

### Question

Is there public evidence that clipping/monitoring for political or institutional
clients is a paid product category, and what rough feature/price anchors exist?

### Answer

Yes, with caveats. Public sources show:

- low/self-service monitoring plans;
- political-specific quote-based tools;
- SMB clipping plans with alerts/reports/AI add-ons;
- larger public-sector clipping contracts.

This does not yet define Otavio's price. It gives positioning anchors.

### Sources Checked

- Legislatech
- Political Brain
- Simpling
- CService
- Clipei
- EBC/SECOM contract table
- Goias SEINFRA clipping term
- TJMA clipping tender

### Change Made

Added `MARKET_RESEARCH_NOTES_2026-05-18.md` with evidence table, initial
interpretation, pricing hypotheses, product implications, and next research
pass.

### Decision

Do not set final pricing yet. The plausible V1 wedge is political-specific,
private dashboard, scoped setup, grouped stories, and lower complexity than
enterprise monitoring.

## 2026-05-18 - Demo Script And Buyer Assumptions Added

### Question

How can Otavio show the product without overpromising features that do not exist
yet?

### Answer

Use a short demo focused on private scoped access, grouped stories, raw text,
and operator-managed updates. Avoid claiming full intelligence, realtime
coverage, custom sites, or a finished Rio indicator.

### Change Made

Added `DEMO_SCRIPT_AND_BUYER_ASSUMPTIONS.md`.

### Decision

The first sales conversation should validate workflow pain and willingness to
pay, not pitch a fully finished platform.

## 2026-05-18 - Dirty Worktree And Commit Boundary Review

### Question

What would be dangerous to commit or deploy accidentally after this long local
loop?

### Current Status Summary

`git diff --check` passed with no whitespace errors.

Files changed by this loop and safe to consider for a path-limited product-loop
commit:

- `assets/clipping.css`
- `assets/clipping.js`
- `data/viewer_profiles.json`
- `md documents/clipping-segregation-product-loop-2026-05-18/ACTIVE_NEXT_ACTION.md`
- `md documents/clipping-segregation-product-loop-2026-05-18/DEMO_SCRIPT_AND_BUYER_ASSUMPTIONS.md`
- `md documents/clipping-segregation-product-loop-2026-05-18/DEPLOYMENT_ENVIRONMENT.md`
- `md documents/clipping-segregation-product-loop-2026-05-18/FIRST_SELLABLE_PACKAGE.md`
- `md documents/clipping-segregation-product-loop-2026-05-18/MARKET_RESEARCH_NOTES_2026-05-18.md`
- `md documents/clipping-segregation-product-loop-2026-05-18/MARKET_RESEARCH_PLAN.md`
- `md documents/clipping-segregation-product-loop-2026-05-18/README_FOR_ACTIVE_AI.md`
- `md documents/clipping-segregation-product-loop-2026-05-18/RENDER_PRODUCTION_CHECKLIST.md`
- `md documents/clipping-segregation-product-loop-2026-05-18/RIO_ECONOMIC_INDICATOR_TRACK.md`
- `md documents/clipping-segregation-product-loop-2026-05-18/STATIC_EXPORT_POLICY.md`
- `md documents/clipping-segregation-product-loop-2026-05-18/SYSTEM_REVIEW_CHECKLIST.md`
- `md documents/clipping-segregation-product-loop-2026-05-18/WORK_LOG.md`
- `tests/test_admin_ui.py`
- `tools/pages_assets/clipping.css`
- `tools/pages_assets/clipping.js`
- `web_app/app.py`
- `web_app/auth.py`
- `web_app/segmentation.py`

Inherited or generated files that must not be swept into this loop:

- `README.md`
- `assets/clipping-data.json`
- `data/reports/performance_benchmark.md`
- deleted legacy `docs/*` paths and moved `md documents/*` legacy docs;
- `md documents/05-05-26-Iris-Shakira goals.md`
- `md documents/Who_Is_Doing_What-WRITE_WHAT_YOU'RE_DOING_HERE.md`
- `pipeline/__pycache__/*.pyc`
- Shakira screenshots under `data/reports/`;
- `tests/test_live_audit_script.py`
- `tools/live_audit.py`
- generated SQLite sidecars `data/clipping.db-wal` and
  `data/clipping.db-shm`.

Special caution:

- `tests/test_sprint_regression_harness.py` was already untracked before this
  loop. This loop adjusted its cancel-update smoke to send CSRF so local tests
  reflect the new contract, but the file should not be blindly added as part of
  a product-loop commit without reviewing ownership.

### Decision

No `git add .`. Any commit must be path-limited and must consciously decide
what to do with the inherited untracked sprint harness file.

## 2026-05-18 - Final Consistency Check Before Pause

### Checks

Passed:

```bash
git diff --check
diff -q assets/clipping.js tools/pages_assets/clipping.js
diff -q assets/clipping.css tools/pages_assets/clipping.css
python -m py_compile web_app/app.py web_app/auth.py web_app/segmentation.py
```

Last broader test runs in this loop:

```text
104 passed in 3.04s
244 passed, 13 deselected in 13.82s
```

### Current Local Server

Local server is running at:

```text
http://127.0.0.1:8765
```

with local smoke passwords documented in `DEPLOYMENT_ENVIRONMENT.md`.

### Pause State

No commit was made in this resumed loop. No files are staged.

## 2026-05-18 - Render Push Recovery After User Correction

### Why This Entry Exists

Otavio correctly pointed out that a local-only checkpoint was not enough. The
product loop's first implementation target is the live FastAPI/Render app, so
this pass moved from local verification toward a path-limited commit, push, and
production check.

### Remote Coordination

Before pushing, `master` was behind active remote work from the repair/debug
loop. This loop rebased the product commit over the remote commits instead of
force-pushing or overwriting them.

Conflict resolution kept both sides:

- the repair loop's hosted-dashboard fix that rewrites
  `data-clipping-static="1"` to `data-clipping-static="0"` for the FastAPI
  served dashboard;
- the product loop's login/session injection and server-side scoped asset
  handlers;
- the repair loop's new hosted-dashboard polling regression test, adapted to
  log in first because `/` is now private.

The remote also advanced with docs-only repair-loop log commits while this
work was running. Those were rebased under the product commit without editing
the repair-loop files.

### Verification Before Push

Passed after the final rebase:

```bash
python -m py_compile web_app/app.py web_app/auth.py web_app/segmentation.py
diff -q assets/clipping.js tools/pages_assets/clipping.js
diff -q assets/clipping.css tools/pages_assets/clipping.css
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py tests/test_export_mobile_snapshot_pages.py -q
```

Focused result:

```text
99 passed in 3.21s
```

Broader non-live run:

```text
238 passed, 1 failed, 12 deselected in 15.06s
```

Failure:

```text
tests/test_pages_performance.py::TestPagesBenchmark::test_pages_step_by_step
AssertionError: Initial shell has 1483 DOM nodes (expected <500)
```

Interpretation: this failure was in the static Pages performance benchmark,
not in auth, profile scoping, API permissions, or export tests. It generated
`data/reports/performance_benchmark.md` and pycache changes; those artifacts
were stashed and not included in the product-loop commit.

### Commit Boundary

Commit prepared on top of current `origin/master`:

```text
feat: ship password-gated clipping profiles
```

Only product-loop implementation/docs paths are included. Inherited dirty work
remains protected in stash entries and must be restored after deploy checks if
safe.

### Next Action

Push `master`, wait for Render to deploy, then verify the live URL for:

- logged-out dashboard shows login instead of private data;
- private JSON assets are not accessible while logged out;
- admin login works if production env vars are present;
- viewer login works only if `CLIPPING_VIEWER_PASSWORDS` is configured on
  Render.

## 2026-05-19 - Live Render Verification After Push

### Pushes

Implementation commit pushed:

```text
12f836b feat: ship password-gated clipping profiles
```

Render did not immediately flip to the new code, so this loop pushed an empty
trigger commit:

```text
9fa5d81 chore: trigger Render deploy for gated profiles
```

The live site switched to the new behavior during polling at approximately
`2026-05-19 11:50:56 UTC`.

### Live URL Checked

```text
https://clipping-project.onrender.com/
```

### Logged-Out Checks

Passed:

```text
GET /                                                    200 login page
GET /index.html                                          404
GET /assets/clipping-data.json                           401 viewer_login_required
GET /assets/clipping-raw-texts.json                      401 viewer_login_required
GET /api/update/status                                   401 viewer_login_required
GET /api/update/live-results?scope=base&limit=240        401 viewer_login_required
GET /api/targets                                         401 viewer_login_required
GET /api/classifications                                 401 viewer_login_required
GET /api/csrf                                            401 viewer_login_required
```

The deployed `assets/clipping.js` contains the new auth/profile markers:

```text
initialSessionRole
ensureCsrfToken
applyViewerControls
```

### Healthz

Live `/healthz` returned:

```json
{
  "ok": true,
  "dbExists": true,
  "authConfigured": true,
  "loginConfigured": true,
  "viewerAuthConfigured": false,
  "viewerProfilesConfigured": true
}
```

### Result

The server-side privacy gate is live for logged-out users. The remaining
production blocker for client profile testing is environment configuration:
Render does not yet have `CLIPPING_VIEWER_PASSWORDS`, so viewer logins for
`flavio`, `shakira`, `rio_economico`, and `demo_cliente` cannot be proven on
production yet.

Do not call the first segregation sprint fully production-complete until
`CLIPPING_VIEWER_PASSWORDS` is configured on Render and at least one viewer
profile is checked end to end.

## 2026-05-19 - Loop Cycle: Re-Anchor On Product Docs And Env Contract

### Objective Reviewed

Re-read the product-loop docs instead of continuing from memory:

- `LONG_TERM_GOALS.md`
- `DEPENDENCY_MAP.md`
- `CURRENT_SHORT_TERM_LOOP.md`
- `ACTIVE_NEXT_ACTION.md`
- `SYSTEM_REVIEW_CHECKLIST.md`
- `RENDER_PRODUCTION_CHECKLIST.md`
- this `WORK_LOG.md`

Active axis remains Axis 1: functional password-gated segregation on the
current FastAPI/Render app. The live logged-out gate is not enough to close the
axis because viewer profiles still must be proven on production.

### Render Audit

Live URL:

```text
https://clipping-project.onrender.com/
```

Observed:

```text
GET /                                                        200 login page
GET /index.html                                              404
GET /assets/clipping-data.json                               401 viewer_login_required
GET /assets/clipping-raw-texts.json                          401 viewer_login_required
GET /api/update/status                                       401 viewer_login_required
GET /api/update/live-results?scope=base&limit=240            401 viewer_login_required
GET /api/targets                                             401 viewer_login_required
GET /api/classifications                                     401 viewer_login_required
GET /api/csrf                                                401 viewer_login_required
POST /api/login wrong password                               401 invalid_password
POST /api/login viewer-shakira                               401 invalid_password
```

Live JS contains the expected auth/profile markers:

```text
initialSessionRole
ensureCsrfToken
applyViewerControls
```

Live `/healthz` still reports:

```text
loginConfigured=true
viewerProfilesConfigured=true
viewerAuthConfigured=false
```

### Action Taken

The deployment docs already required `CLIPPING_VIEWER_PASSWORDS`, but the
Render blueprint did not declare it. Added `CLIPPING_VIEWER_PASSWORDS` as a
`sync: false` environment variable in `render.yaml` so the production contract
matches the code and checklist without committing any secret.

Added `LOOP_OPERATING_PROTOCOL.md` to this product-loop folder and updated
`ACTIVE_NEXT_ACTION.md` so future cycles must re-read the `.md` authority files
and continue after checkpoints.

### Remaining Blocker

This does not create the secret value in Render by itself. Production should
not be called complete until the Render environment contains
`CLIPPING_VIEWER_PASSWORDS` and a real viewer profile is smoked end to end.

### Next Objective From Docs

After push/deploy verification, return to the docs and continue with the next
unblocked proof:

1. verify the logged-out gate survived the deploy;
2. check whether `/healthz` changed `viewerAuthConfigured`;
3. if still false, run local authenticated contract tests and keep the blocker
   explicit;
4. continue into scoped payload/raw-text/no-fake-UI review instead of stopping.

### Why The Loop Continues

The docs explicitly say a deploy, a live `401`, or a single smoke is not a stop
condition. This cycle improved the Render contract but did not prove live
viewer scoping.

## 2026-05-19 - Loop Cycle: Post-Deploy Gate Check And Local Scoping Contracts

### Objective Reviewed

Returned to the product-loop docs after the deploy checkpoint. The next
unblocked objective from `ACTIVE_NEXT_ACTION.md` and
`SYSTEM_REVIEW_CHECKLIST.md` was: keep the live logged-out privacy gate checked
while proving the authenticated scoping contract locally until Render has
viewer passwords configured.

### Render Audit

Polled production after the path-limited `render.yaml`/loop-protocol commit.
The live surface stayed gated:

```text
root=200/login
assets/clipping-data.json=401
viewerAuthConfigured=false
```

Repeated samples:

```text
12:30:36 root=200/login data=401 "viewerAuthConfigured":false
12:30:52 root=200/login data=401 "viewerAuthConfigured":false
12:31:13 root=200/login data=401 "viewerAuthConfigured":false
12:31:28 root=200/login data=401 "viewerAuthConfigured":false
12:31:44 root=200/login data=401 "viewerAuthConfigured":false
12:32:00 root=200/login data=401 "viewerAuthConfigured":false
12:32:16 root=200/login data=401 "viewerAuthConfigured":false
12:32:32 root=200/login data=401 "viewerAuthConfigured":false
```

### Local Authenticated Contract Tests

Because production cannot accept viewer logins until
`CLIPPING_VIEWER_PASSWORDS` exists on Render, ran focused local contracts for
the same acceptance path:

```bash
.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_dashboard_payload_and_raw_text_are_password_scoped \
  tests/test_admin_ui.py::test_viewer_profile_scope_can_come_from_reviewable_config_file \
  tests/test_admin_ui.py::test_dashboard_shell_marks_viewer_session_before_payload_load \
  tests/test_admin_ui.py::test_viewer_cannot_widen_live_results_or_write_admin_actions \
  tests/test_admin_ui.py::test_admin_write_apis_reject_missing_or_bad_csrf \
  tests/test_admin_ui.py::test_targets_api_is_login_scoped_and_admin_uploads_target_manifest \
  tests/test_admin_ui.py::test_hosted_dashboard_enables_same_origin_api_polling \
  -q
```

Result:

```text
7 passed in 0.67s
```

### Evidence

The local contracts cover:

- scoped dashboard payload and scoped raw texts;
- profile scopes loaded from reviewable config;
- viewer shell marked readonly before payload load;
- direct live-results widening blocked for viewers;
- viewer write/admin actions rejected;
- admin CSRF still required;
- targets API scoped by login;
- hosted dashboard uses same-origin API polling after login.

### Remaining Blocker

Production still reports `viewerAuthConfigured=false`. This is the hard blocker
for proving live viewer profiles. The code, docs, and Render blueprint now all
name `CLIPPING_VIEWER_PASSWORDS`, but the secret value still has to exist in
Render.

### Next Objective From Docs

Re-read the objective docs again and continue with the next unblocked review:

1. inspect client UI hiding/no-fake-UI behavior against the deployed JS and
   local viewer shell;
2. check static export boundaries so private client demos do not point at
   GitHub Pages/Wix/static raw JSON;
3. keep `viewerAuthConfigured=false` visible as the production blocker until a
   live viewer password can be tested.

### Why The Loop Continues

The authenticated scoping tests passed, but the live site still cannot prove a
viewer profile. Passing local contracts is a checkpoint, not completion.

## 2026-05-19 - Loop Cycle: Viewer UI And Static Boundary Review

### Objective Reviewed

Re-read the next unblocked items from `SYSTEM_REVIEW_CHECKLIST.md` and
`STATIC_EXPORT_POLICY.md`: verify viewer UI cleanliness/no-fake-UI behavior and
confirm static exports are not treated as private client surfaces.

### Local Viewer UI Smoke

Started a local FastAPI server with explicit local viewer passwords and logged
in as `shakira`.

Observed browser state:

```text
login=200 role=viewer profile=shakira
bodyClass=viewer-readonly
app data role=viewer
app data profile=shakira
run tab "Rodar atualização" hidden/display none/visible false
run tab "Progresso compartilhado" hidden/display none/visible false
run tab "Base atual" visible true
add-target box hidden/display none/visible false
manage-targets box hidden/display none/visible false
filter chips: Shakira only
visible action buttons: none
```

Checked local scoped payloads for all configured viewer profiles:

```text
flavio        targets=['flavio_valle','pedro_duarte','pedro_angelito','bernardo_rubiao'] article_targets=['bernardo_rubiao','flavio_valle','pedro_angelito','pedro_duarte'] raw=662
shakira       targets=[] article_targets=[] raw=0
rio_economico targets=[] article_targets=[] raw=0
demo_cliente  targets=[] article_targets=[] raw=0
```

The empty local Shakira/Rio/demo payloads reflect the current local static
snapshot, not a production proof. The useful finding is that empty profiles do
not fall back to Flavio data and viewer UI controls remain hidden.

### Static Boundary Audit

Checked GitHub Pages:

```text
https://ottoboop.github.io/clipping-project/                              200 bytes=10404
https://ottoboop.github.io/clipping-project/assets/clipping-data.json      200 bytes=1417213
https://ottoboop.github.io/clipping-project/assets/clipping-raw-texts.json 200 bytes=4565931
```

This confirms the static Pages bundle still serves bundled JSON/raw files. That
is acceptable only as legacy/static/public review material. It must not be used
as a paid private client demo or access path.

### Action Taken

Updated `STATIC_EXPORT_POLICY.md` with the live GitHub Pages boundary evidence.

### Remaining Blocker

Production viewer login remains blocked by
`viewerAuthConfigured=false`/missing `CLIPPING_VIEWER_PASSWORDS` on Render.

### Next Objective From Docs

Return to the docs and continue with:

1. live Render logged-out gate monitoring;
2. local contract checks for profile/raw/API scoping when production viewer
   credentials are unavailable;
3. Rio economic profile methodology/isolation review as the next axis that can
   be improved without production secrets.

### Why The Loop Continues

No-fake-UI and static-boundary evidence are useful checkpoints, but the product
still lacks live viewer-profile proof on Render.

## 2026-05-19 - Loop Cycle: Rio Economic Profile Isolation Review

### Objective Reviewed

Returned to `DEPENDENCY_MAP.md` and `RIO_ECONOMIC_INDICATOR_TRACK.md`. The
next unblocked axis was not to build the indicator, but to verify that the Rio
economic placeholder remains isolated and does not pollute Flavio/Shakira or
start premature collection.

### Audit Performed

Read:

- `RIO_ECONOMIC_INDICATOR_TRACK.md`
- `data/viewer_profiles.json`
- `data/targets.json`
- `web_app/segmentation.py`
- `pipeline/settings.py`

Findings:

```text
viewer_profiles.json has profile rio_economico -> target_keys ["rio_economico"]
web_app/segmentation.py has default profile rio_economico -> target_keys ["rio_economico"]
data/targets.json does not contain rio_economico
```

`pipeline.settings.get_active_targets()` automatically adds a target label to
the target's keywords if the label is missing. Therefore adding a
`rio_economico` row to `data/targets.json` would create real search/matcher
terms before methodology validation.

### Decision

Do not add a `rio_economico` target row yet. The current safe state is a
profile-only placeholder that can render an empty scoped view without falling
back to Flavio data.

### Action Taken

Updated `RIO_ECONOMIC_INDICATOR_TRACK.md` with the implementation audit and
the explicit decision not to add a target row before production segregation and
term validation.

### Remaining Blocker

The Rio profile still cannot be smoked on production because
`CLIPPING_VIEWER_PASSWORDS` is not configured on Render.

### Next Objective From Docs

Re-read the product docs and continue with product packaging/market-research
tracks that do not require Render viewer passwords, while keeping the live
viewer-auth blocker active.

### Why The Loop Continues

The Rio review prevented a likely future pollution mistake, but it did not
complete production viewer segregation.

## 2026-05-19 - Loop Cycle: Sellable Package Readiness Gate

### Objective Reviewed

Returned to `FIRST_SELLABLE_PACKAGE.md`, `DEMO_SCRIPT_AND_BUYER_ASSUMPTIONS.md`,
and `MARKET_RESEARCH_PLAN.md`.

The market-research plan explicitly says not to research yet if production
segregation is not verified, demo data leaks another profile, no clear demo
profile exists, or viewer UI exposes operator controls.

### Audit Performed

Current evidence from prior cycles:

```text
Render logged-out gate: passed
Render viewer login: blocked by viewerAuthConfigured=false
Local viewer scoped payload/raw/API contracts: passed
Local viewer readonly/no-fake-UI smoke: passed
GitHub Pages static boundary: public, not private
Rio economic profile: profile-only placeholder, no collection terms
```

### Decision

Do not start broad buyer outreach or a live external demo yet. The package can
be described internally, but external proof still depends on live Render viewer
credentials.

### Action Taken

Updated `FIRST_SELLABLE_PACKAGE.md` with a current readiness gate:

- allowed now: internal/local controlled demo, technical proof discussion,
  continued planning;
- not allowed yet: sending a live client password, pitching static exports as
  private access, claiming production multi-client segregation complete, or
  starting outreach that depends on live demo.

### Remaining Blocker

Same blocker: `CLIPPING_VIEWER_PASSWORDS` is still missing on Render.

### Next Objective From Docs

Re-read the docs and continue with one of the remaining unblocked items:

1. live logged-out gate monitoring;
2. local profile/raw/API regression checks;
3. review operations/cost discipline so Otavio does not create an expensive
   bespoke service by accident.

### Why The Loop Continues

The package readiness gate prevents overpromising, but the product loop still
has not proven live viewer profiles.

## 2026-05-19 - Loop Cycle: Operator Cost Discipline

### Objective Reviewed

Returned to `LONG_TERM_GOALS.md`, `DEPENDENCY_MAP.md`,
`FIRST_SELLABLE_PACKAGE.md`, and `MARKET_RESEARCH_PLAN.md`.

The long-term goal says the product should help fund AI/tooling instead of
creating more manual work and cost. Existing docs had cost warnings but no
single operating guardrail.

### Audit Performed

Searched the product-loop docs and code references for cost, tooling, operator
burden, pricing, manual work, custom work, and maintenance.

Finding:

```text
Cost discipline existed as scattered warnings, not as a dedicated checklist.
```

### Action Taken

Added `OPERATOR_COST_DISCIPLINE.md` with V1 boundaries:

- sell bounded monitoring first, not bespoke intelligence work;
- keep profile/password, agreed targets, periodic updates, grouped stories,
  scoped raw text, basic review, and occasional manual export in V1;
- keep unlimited targets, realtime alerts, custom frontends/repos, daily AI
  narrative reports, social/TV/radio/print monitoring, and Rio methodology work
  out of the base price;
- track update time, review time, number of targets, source complexity, AI/tool
  usage, report time, and support burden before setting pricing.

### Remaining Blocker

The live product is still not externally demoable until Render has
`CLIPPING_VIEWER_PASSWORDS` and a viewer profile is smoked end to end.

### Next Objective From Docs

Re-read the docs and continue with live gate monitoring plus any remaining
system checklist gaps that do not require production viewer credentials.

### Why The Loop Continues

Cost discipline reduces product risk, but it does not complete Axis 1
production segregation.

## 2026-05-19 - Loop Cycle: System Review Status Snapshot

### Objective Reviewed

Returned to `SYSTEM_REVIEW_CHECKLIST.md` after another live Render gate check.
The loop needed a status matrix separating what is proven live, what is proven
locally, and what remains blocked by production environment.

### Render Audit

Current live check:

```text
GET / -> 200 login page
GET /assets/clipping-data.json -> 401 viewer_login_required
GET /assets/clipping-raw-texts.json -> 401 viewer_login_required
GET /api/update/status -> 401 viewer_login_required
GET /healthz -> loginConfigured=true, viewerProfilesConfigured=true, viewerAuthConfigured=false
```

### Action Taken

Created `SYSTEM_REVIEW_STATUS_2026-05-19.md` and linked it from
`ACTIVE_NEXT_ACTION.md`.

The snapshot records:

- live Render logged-out proofs;
- local authenticated contract proofs;
- static boundary status;
- production checks still blocked by missing `CLIPPING_VIEWER_PASSWORDS`;
- the exact full production checklist to run once viewer auth exists.

### Remaining Blocker

Same blocker: live viewer profile testing requires `CLIPPING_VIEWER_PASSWORDS`
on Render.

### Next Objective From Docs

Continue the loop from `ACTIVE_NEXT_ACTION.md` and this status snapshot:

1. keep monitoring the Render gate;
2. avoid market outreach/live demo until viewer auth is configured;
3. run/update local contract tests if code or profile config changes;
4. once credentials exist, run the full production viewer checklist.

### Why The Loop Continues

A status snapshot improves continuity for future agents, but it is not live
viewer proof.
