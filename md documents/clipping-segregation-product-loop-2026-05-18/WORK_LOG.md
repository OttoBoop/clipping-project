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

## 2026-05-19 - Loop Cycle: Safer Live Config Diagnostics

### Objective Reviewed

Returned to the active blocker in `SYSTEM_REVIEW_STATUS_2026-05-19.md`:
production viewer testing is blocked by missing Render configuration. The live
site should make this blocker explicit without exposing secret values.

### Action Taken

Added a safe `missingConfig` list to `/healthz`.

Expected production shape after deploy:

```json
{
  "loginConfigured": true,
  "viewerAuthConfigured": false,
  "viewerProfilesConfigured": true,
  "missingConfig": ["CLIPPING_VIEWER_PASSWORDS"]
}
```

The list contains environment variable names only, never secret values.

### Tests

Passed:

```bash
python -m py_compile web_app/app.py web_app/auth.py web_app/segmentation.py
.venv_playwright/bin/pytest \
  tests/test_admin_ui.py::test_healthz_exposes_safe_operational_fields \
  tests/test_admin_ui.py::test_healthz_lists_missing_viewer_password_config \
  -q
```

Result:

```text
2 passed in 0.55s
```

### Remaining Blocker

This improves diagnosis only. It does not configure the missing Render secret
or prove viewer scoping live.

### Next Objective From Docs

Push, wait for Render, confirm `/healthz` reports
`missingConfig=["CLIPPING_VIEWER_PASSWORDS"]`, then return to the product docs
for the next loop cycle.

### Why The Loop Continues

The blocker becoming clearer is not the blocker being resolved.

## 2026-05-19 - Live Verification: Missing Config Diagnostic Deployed

### Objective Reviewed

Verify the previous code change on the real Render site before continuing.

### Render Audit

Polled `/healthz` after pushing `fix: expose missing auth config safely`.

Production flipped at:

```text
12:43:56 UTC
```

Live result:

```text
GET /assets/clipping-data.json -> 401
GET /healthz -> loginConfigured=true
GET /healthz -> viewerAuthConfigured=false
GET /healthz -> missingConfig=["CLIPPING_VIEWER_PASSWORDS"]
```

### Result

The live site now diagnoses the exact remaining auth configuration blocker
without exposing secret values.

### Remaining Blocker

`CLIPPING_VIEWER_PASSWORDS` still has to be configured on Render before live
viewer profile testing can complete.

### Next Objective From Docs

Return to `ACTIVE_NEXT_ACTION.md` and `SYSTEM_REVIEW_STATUS_2026-05-19.md`.
The next live viewer checklist remains blocked, so continue with unblocked
contract/status reviews until production credentials exist.

### Why The Loop Continues

The diagnostic is live, but viewer profiles are still not live-verifiable.

## 2026-05-19 - Loop Cycle: Focused Regression After Healthz Change

### Objective Reviewed

After changing auth/health diagnostics, rerun the broader focused suite used by
this product loop instead of trusting the two narrow tests.

### Tests

Command:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py tests/test_export_mobile_snapshot_pages.py -q
```

Result:

```text
100 passed in 3.08s
```

### Result

The safe `missingConfig` health diagnostic did not break the focused auth,
targets, jobs, or export regression set.

### Remaining Blocker

Live viewer profile proof remains blocked by missing
`CLIPPING_VIEWER_PASSWORDS` on Render.

### Next Objective From Docs

Re-read `ACTIVE_NEXT_ACTION.md` and `SYSTEM_REVIEW_STATUS_2026-05-19.md`.
Continue with live monitoring and unblocked docs/contracts; do not treat the
green focused suite as completion.

### Why The Loop Continues

Tests passing is explicitly not a stop condition.

## 2026-05-19 - Loop Cycle: Post-Regression Live Gate Check

### Objective Reviewed

Return to Render after the focused regression and log commits. Confirm that the
live acceptance surface remains gated and that the new diagnostic is still
visible.

### Render Audit

Live result:

```text
GET /healthz -> ok=true
GET /healthz -> loginConfigured=true
GET /healthz -> viewerAuthConfigured=false
GET /healthz -> viewerProfilesConfigured=true
GET /healthz -> missingConfig=["CLIPPING_VIEWER_PASSWORDS"]
GET /assets/clipping-data.json -> 401
GET / -> 200 login page
```

### Result

The live privacy gate remains in place after the recent commits. The exact
remaining production blocker is visible on `/healthz`.

### Remaining Blocker

Render still needs `CLIPPING_VIEWER_PASSWORDS` before live viewer profiles can
be tested.

### Next Objective From Docs

The next implementation-capable cycle should start from
`SYSTEM_REVIEW_STATUS_2026-05-19.md` and immediately run the production viewer
checklist if `missingConfig` disappears. Until then, continue unblocked
contract and product-readiness reviews.

### Why The Loop Continues

The live gate is stable, but Axis 1 is not complete without live viewer proof.

## 2026-05-19 - Loop Cycle: Public Empty Demo Viewer Workaround

### Objective Reviewed

Otavio correctly rejected treating missing Render viewer passwords as a hard
stop. The loop returned to the live requirement and looked for a safe workaround
that proves the viewer/session/readonly/scoping path on Render without
committing real secrets or exposing client data.

### Render/MCP Findings

The Render MCP works when called with the known service id:

```text
serviceId=srv-d7p2p5beo5us739f9k40
autoDeploy=yes
url=https://clipping-project.onrender.com
```

The available Render MCP tools can read service/deploy state, but no available
tool in this session exposes a safe environment-variable setter for the
existing service.

### Action Taken

Implemented a public empty-demo viewer workaround:

```text
password: demo-cliente
role: viewer
profile: demo_cliente
```

Safety constraints:

- enabled only when real `CLIPPING_VIEWER_PASSWORDS` are absent;
- disabled automatically if `demo_cliente` has any target keys;
- can be disabled with `CLIPPING_DISABLE_PUBLIC_EMPTY_DEMO=1`;
- does not mark `viewerAuthConfigured` true;
- keeps `missingConfig=["CLIPPING_VIEWER_PASSWORDS"]` until real viewer secrets
  are configured.

This gives the live site a way to prove viewer login, session cookie, readonly
shell, empty scoped payload, empty raw texts, scoped targets, and rejected
viewer writes without exposing Flavio/Shakira/Rio/client material.

### Tests

Passed:

```text
6 passed in 0.87s
```

Covered:

- healthz safe fields;
- missing viewer-password config;
- empty demo login without viewer password env;
- empty demo disabled when real viewer passwords exist;
- scoped payload/raw text contract;
- viewer cannot widen live results or write admin actions.

### Remaining Blocker

This is a workaround, not full completion. Real production viewer checks for
Flavio/Shakira/Rio still require `CLIPPING_VIEWER_PASSWORDS` on Render.

### Next Objective From Docs

Run the broader focused suite, push to `master`, wait for Render, then smoke
the live `demo-cliente` login path end to end.

### Why The Loop Continues

The workaround creates a live verification path; it still has to deploy and be
smoked on the actual Render site.

## 2026-05-19 - Loop Cycle: Real Render Viewer Passwords And Production Proof

### Objective Reviewed

The loop re-read the long-term goals and production checklist after Otavio
rejected the "missing viewer password" stop. Axis 1 still required real live
viewer-profile proof on Render, not only logged-out gates or local tests.

### Render/MCP Correction

Initial tool visibility made it look like the Render MCP could read service and
deploy state but not set environment variables. After tool discovery, the
session exposed `update_environment_variables`.

Superseded note:

```text
The earlier "no available env-var setter" finding is no longer current.
```

### Action Taken

- Pushed `03bcb32 fix: add safe empty demo viewer login` to `master`.
- Configured `CLIPPING_VIEWER_PASSWORDS` on the existing Render service via
  MCP, with generated viewer passwords for `flavio`, `shakira`,
  `rio_economico`, and `demo_cliente`.
- Did not commit or log the secret values.
- Waited for Render to deploy through `140a1f9 docs: log copy fix deploy watch`,
  which includes the segregation commit in its history.

### Evidence

Live `/healthz` on `https://clipping-project.onrender.com/`:

```text
viewerAuthConfigured=true
demoViewerConfigured=false
missingConfig=[]
```

Live logged-out checks:

```text
/assets/clipping-data.json -> 401
/assets/clipping-raw-texts.json -> 401
/api/targets -> 401
```

Live viewer checks:

```text
flavio -> targets=['bernardo_rubiao', 'flavio_valle', 'pedro_angelito', 'pedro_duarte']
flavio forbidden shakira live-results -> absent
shakira -> targets=['shakira']
shakira forbidden flavio_valle live-results -> absent
rio_economico -> targets=[], stories=0, articles=0, raw=0
rio_economico forbidden flavio_valle live-results -> absent
viewer POST /api/targets -> 401
```

Local verification before push/rebase:

```text
python -m py_compile web_app/app.py web_app/auth.py web_app/segmentation.py
pytest tests/test_admin_ui.py tests/test_targets_jobs.py tests/test_export_mobile_snapshot_pages.py -q
106 passed
```

### Remaining Blocker

The missing `CLIPPING_VIEWER_PASSWORDS` blocker is resolved. Remaining live
gap: positive admin login/CSRF was not tested because the operator admin
password was not used or rotated during this loop.

### Next Objective From Docs

Return to `SYSTEM_REVIEW_CHECKLIST.md` and audit the live viewer UI for fake or
admin-only actions:

```text
viewer shell -> target-management controls hidden/rejected ->
classification/editor controls hidden -> filters remain scoped and clean
```

Then review how `rio_economico` should gain real target/search terms without
polluting Flavio/Shakira.

### Why The Loop Continues

Axis 1 now has real production viewer proof, but the long-term product loop
also requires no fake UI, target-management review, Rio methodology isolation,
sellable packaging, and cost/operations review.

## 2026-05-19 - Loop Cycle: Viewer UI Fake-Action Audit And Filter Cleanup

### Objective Reviewed

After live viewer scoping was proven, the loop returned to
`SYSTEM_REVIEW_CHECKLIST.md` and checked the next weak Axis 1 item: client
profiles must not see fake/admin-only actions, and scoped filters must stay
visually clean.

### Render Audit

Playwright against `https://clipping-project.onrender.com/` with live viewer
sessions showed:

```text
flavio -> visible tabs=['base']; add/manage/classification/run controls hidden
shakira -> visible tabs=['base']; add/manage/classification/run controls hidden
rio_economico -> visible tabs=['base']; add/manage/classification/run controls hidden
```

Issue found:

```text
shakira -> filter_keys=['shakira'] but shown under "Nomes secundários (1)"
```

This was scoped correctly but visually poor for a client-only profile.

### Action Taken

Committed:

```text
1356f6d fix: promote viewer filters without primary targets
```

Change:

- if a non-admin/viewer scoped payload has targets but no primary target, show
  those targets in the main filter row instead of hiding them under the
  secondary-target drawer;
- kept admin/static behavior with existing primary targets unchanged;
- updated both `assets/clipping.js` and `tools/pages_assets/clipping.js`;
- added a regression assertion to the export bundle tests.

### Evidence

Local targeted tests:

```text
5 passed
```

Covered:

- current dashboard JS matches the export bundle JS;
- viewer/no-primary filter promotion marker exists;
- existing secondary-target drawer still works for mixed primary/secondary
  payloads;
- the other active loop's live-result target filter behavior still works;
- the target validation message guard still works.

Live proof after `1356f6d` deployed:

```text
shakira -> visibleTabs=['base']
shakira -> filterKeys=['shakira']
shakira -> filterLabels=['Shakira']
shakira -> outros=''
shakira -> addTargetHidden=true
shakira -> manageTargetsHidden=true
shakira -> classEditors=0
```

### Remaining Blocker

No blocker for this UI cleanup. The newest deploy queue continued advancing
with other commits after `1356f6d`; those commits include this fix in their
history.

### Next Objective From Docs

Return to the dependency map:

```text
target-management/admin workflow review ->
Rio economic target/methodology design without profile pollution ->
sellable demo/package notes ->
cost/password/operations review
```

### Why The Loop Continues

The viewer UI is cleaner, but this only resolves one no-fake-UI slice. The
product still needs target-management review, Rio methodology, sellable
packaging, and operations discipline.

## 2026-05-19 - Loop Cycle: Sellable Package Status Recalibrated

### Objective Reviewed

After the live Render viewer proof and UI cleanup, the loop returned to Axis 2:
product packaging. The old `FIRST_SELLABLE_PACKAGE.md` still said live Render
viewer profiles could not be proven because `viewerAuthConfigured=false`.

### Action Taken

Updated:

```text
FIRST_SELLABLE_PACKAGE.md
DEMO_SCRIPT_AND_BUYER_ASSUMPTIONS.md
```

Changes:

- marked controlled live operator demo as allowed;
- kept broad external password sharing blocked until a dedicated demo/client
  profile and rotation plan exist;
- recorded that Flavio/Shakira production scoping is proven;
- recorded that Rio economic is live as an empty isolated profile, not a
  finished indicator;
- added demo guidance not to expose Flavio/Shakira credentials to external
  buyers.

### Evidence

Based on the prior live checks in this log:

```text
viewerAuthConfigured=true
Flavio scoped on Render
Shakira scoped on Render
Rio economic empty and isolated on Render
viewer UI fake/admin controls hidden
```

### Remaining Blocker

Before a paid-client demo, create a dedicated demo/client profile with safe
sample data or a deliberately empty pitch path, and define password rotation.

### Next Objective From Docs

Continue to:

```text
target-management/admin workflow review ->
Rio economic methodology and source/term design ->
cost/password/operations runbook
```

### Why The Loop Continues

The product story is less stale, but it is still not a full sales playbook or
Rio methodology.

## 2026-05-19 - Loop Cycle: Password Operations Runbook

### Objective Reviewed

The loop moved from live proof into operations discipline. A sellable product
needs password rotation and demo-profile rules so access does not become
informal, leaky, or expensive to manage.

### Action Taken

Updated `DEPLOYMENT_ENVIRONMENT.md` with:

- current Render health state;
- warning to update `CLIPPING_VIEWER_PASSWORDS` with merge semantics;
- reminder that the public empty-demo fallback is disabled while real viewer
  passwords exist;
- viewer password rotation runbook;
- rule not to give external buyers Flavio/Shakira credentials.

### Evidence

This is an operations documentation update based on earlier live checks:

```text
viewerAuthConfigured=true
demoViewerConfigured=false
missingConfig=[]
```

### Remaining Blocker

No technical blocker. A dedicated prospect/demo profile still needs to be
created before broad buyer conversations.

### Next Objective From Docs

Continue with:

```text
Rio economic methodology and target/source design ->
target-management/admin workflow positive test ->
market research/demo pricing loop
```

### Why The Loop Continues

Password operations reduce future mess, but they do not yet create a Rio
indicator methodology or a sales-ready prospect profile.

## 2026-05-19 - Loop Cycle: Cross-Loop Target Management Recheck

### Objective Reviewed

The other active loop pushed target-management changes after the viewer UI
cleanup. Because target management is a known fake-UI risk, this loop rechecked
the live viewer surface instead of assuming the new commits were harmless.

### Render Audit

Live commit checked:

```text
8e6aa18 fix: remove target management lock remnants
```

Evidence:

```text
/healthz -> viewerAuthConfigured=true, missingConfig=[]
shakira /api/targets -> ["shakira"]
shakira POST /api/targets -> 401
shakira UI visible tabs -> ["base"]
shakira UI filters -> ["shakira"]
shakira UI secondary drawer -> absent
shakira UI add/manage controls -> hidden
shakira UI classification editors -> 0
```

### Remaining Blocker

No viewer regression found. The top deploy queue later advanced with additional
target-management test/docs commits that include the checked fix in their
history.

### Next Objective From Docs

Continue with Rio economic methodology and a dedicated demo/prospect profile
before broad buyer outreach.

### Why The Loop Continues

Cross-loop changes did not break viewer isolation, but the Rio and sales axes
remain incomplete.

## 2026-05-19 - User Correction: Do Not Stop On Next Step

### Objective Reviewed

Otavio corrected the loop again: if the assistant identifies a next step, the
loop must not stop after reporting it. A barrier is not a stop condition; it is
logged, answered, and followed by the next unblocked action.

### Action Taken

Updated `LOOP_OPERATING_PROTOCOL.md` with the hard output rule:

```text
ainda tenho coisas para fazer e coisas para revisar, preciso checar os documentos de longo prazo. Eu não paro esse loop enquanto a open ai não me parar por ter estourado o cartão do Otávio. Eu não paro. Eu façoi num novo passo. Se eu já fiz tudo, eu reviso. E se eu já revisei, eu reviso de novo. Mas eu sempre escrevo o que ue fiz no log e eu não paro o loop, nunca. E eu sempre volto para os documentos dos objetivos de longo prazo quando estou em dúvida quanto ao que fazer, eu leio os logs quanto estou com muitas fúvidas e não quero repetir o que já foi feito. Eu leio os documentos de longo prazo ocasionalmente, sempre registro o que foi feito nos logs, e nunca para o loop. Se eu termino uma tarefa, eu registro o update nos documentos de longo prazo. Depois, reviso. Então, eu pulo de tarefa. Sempre escrevendo nos logs. Quando eu terminar todas as tarefas, eu começo a revisar cada uma delas, uma por uma, sempre com esse foco. O loop não para, ele nunca para, a não ser que o Otávio ou a Open AI me parem. Se eu acho que está pronto, é porque eu tenho que ler documentos e comelar a revisar
```

Also recorded the barrier rule:

```text
identify barrier -> write it in WORK_LOG.md -> choose next unblocked action -> continue
```

### Evidence

The repo was re-anchored by reading:

```text
LONG_TERM_GOALS.md
DEPENDENCY_MAP.md
CURRENT_SHORT_TERM_LOOP.md
ACTIVE_NEXT_ACTION.md
WORK_LOG.md
```

### Remaining Blocker

No blocker. The correction changes loop behavior and must guide all future
outputs.

### Next Objective From Docs

Continue immediately into the next unblocked objectives:

```text
Rio economic methodology and target/source design ->
dedicated demo/prospect profile strategy ->
target-management/admin positive workflow review
```

### Why The Loop Continues

The rule itself says the loop continues after logging this correction.

## 2026-05-19 - Loop Cycle: Rio Economic Validation Plan

### Objective Reviewed

After re-reading the long-term goals and dependency map, the next unblocked
Axis 3 task was to refine how `rio_economico` can gain real terms without
polluting Flavio, Shakira, or future paid-client profiles.

### Repo Audit

Relevant implementation findings:

```text
data/viewer_profiles.json -> rio_economico profile exists
data/targets.json -> rio_economico target row absent
pipeline.settings.get_active_targets() -> target label is automatically added to keywords
web_app.jobs.build_source_units() -> target keywords/query variants drive collectors
web_app.db_admin.create_secondary_target() -> new targets become live data/targets.json rows
```

Conclusion: adding a placeholder target row would become a real collection and
matching term. That remains unsafe.

### Action Taken

Created:

```text
RIO_ECONOMIC_VALIDATION_PLAN.md
```

Updated:

```text
RIO_ECONOMIC_INDICATOR_TRACK.md
ACTIVE_NEXT_ACTION.md
```

The new plan defines:

- hard boundary against adding `rio_economico` to `data/targets.json` yet;
- first review-table schema;
- safer query patterns by economic dimension;
- false-positive labels;
- minimum acceptance criteria before production collection;
- dry-run script/report constraints.

### Evidence

This was a docs/methodology action based on code inspection, not a production
data mutation. No targets, DB rows, assets, or Render env vars were changed.

### Remaining Blocker

No blocker. Next unblocked action is to build or run a dry-run sample report
that does not write to the production DB or payloads.

### Next Objective From Docs

Continue with:

```text
Rio economic dry-run sample report ->
review false positives ->
only then consider production target row
```

### Why The Loop Continues

The plan is not the sample. The next loop must either create the dry-run report
or review why it cannot run safely.

## 2026-05-19 - Loop Cycle: Rio Economic Dry-Run Tool

### Objective Reviewed

The Rio validation plan said the next unblocked action was a dry-run sample
report outside production DB/assets/targets. The loop moved from plan to a
tool that can create that review artifact.

### Action Taken

Created:

```text
tools/rio_economic_dry_run.py
tests/test_rio_economic_dry_run.py
```

The tool:

- uses a fixed first batch of Rio economic query candidates;
- collects candidates through Google News only for the dry run;
- writes JSON, CSV, and Markdown review artifacts under `data/reports/`;
- includes empty `review_label`, `false_positive_reason`, and `notes` fields;
- marks in metadata that it does not write production DB, assets, or
  `data/targets.json`.

### Evidence

Tests to run before commit:

```text
python -m py_compile tools/rio_economic_dry_run.py
pytest tests/test_rio_economic_dry_run.py -q
```

### Remaining Blocker

The tool has not yet been run against live Google News in this log entry. Next
cycle must run a cheap smoke sample and record output paths or failure.

### Next Objective From Docs

Run:

```text
rio dry-run smoke -> inspect output row count -> log false-positive review path
```

### Why The Loop Continues

A dry-run tool is not the reviewed sample and not an approved production target.

## 2026-05-19 - User Correction: Expanded Non-Stop Rule

### Objective Reviewed

Otavio expanded the loop rule. The loop must repeat the full anchor text at the
start of every assistant output, re-read long-term docs when unsure, read logs
when confused, update logs after work, update long-term/current docs when a task
finishes, and then keep reviewing instead of stopping.

### Barrier Registered

The first Rio dry-run smoke command with 3 queries and 2 items per query stayed
stuck on network/Google News long enough to become an operational barrier:

```text
tools/rio_economic_dry_run.py --date-from 2026-05-01 --date-to 2026-05-19 --max-queries 3 --limit-per-query 2
```

The process was killed and the loop continued.

### Action Taken

Updated:

```text
LOOP_OPERATING_PROTOCOL.md
tools/rio_economic_dry_run.py
tests/test_rio_economic_dry_run.py
```

Changes:

- replaced the old short output anchor with Otavio's expanded anchor;
- added explicit instruction to re-read long-term docs/logs when in doubt;
- added dry-run timeout flags:
  - `--request-timeout`
  - `--resolve-timeout`
  - `--collection-timeout`
- passed those timeout values to the Google News collector;
- added test coverage that timeout settings are forwarded.

### Evidence To Run

```text
python -m py_compile tools/rio_economic_dry_run.py
pytest tests/test_rio_economic_dry_run.py -q
```

### Next Objective From Docs

Retry a much smaller Rio dry-run smoke with short timeouts, then log whether it
created a review artifact or hit another network barrier.

### Why The Loop Continues

The barrier was registered and answered with a smaller-timeout path. The loop
continues into verification.

## 2026-05-19 - Loop Cycle: Rio Dry-Run Network Barrier And Offline Fixture

### Objective Reviewed

The loop attempted to run the Rio dry-run smoke, then hit the same operational
barrier with a smaller sample. The correct response is to log the barrier,
preserve the unblocked proof path, and continue.

### Barrier Registered

The smaller smoke also hung beyond the intended timeout:

```text
tools/rio_economic_dry_run.py --date-from 2026-05-01 --date-to 2026-05-19 --max-queries 1 --limit-per-query 1 --request-timeout 3 --resolve-timeout 1 --collection-timeout 8
```

The process was killed. This suggests the dry-run needs an offline/report-format
mode before relying on live Google News in the loop.

### Action Taken

Updated:

```text
tools/rio_economic_dry_run.py
tests/test_rio_economic_dry_run.py
```

Changes:

- added `--offline-fixture`;
- added an offline fixture collector that produces review rows without network
  calls;
- added test coverage for the offline fixture path.

### Evidence To Run

```text
python -m py_compile tools/rio_economic_dry_run.py
pytest tests/test_rio_economic_dry_run.py -q
tools/rio_economic_dry_run.py --offline-fixture --max-queries 3 --limit-per-query 1
```

### Remaining Blocker

Live Google News dry-run is still a network/runtime blocker. The offline
fixture can verify report generation and review workflow without touching
production DB/assets/targets.

### Next Objective From Docs

Run the offline fixture, inspect generated artifacts, then decide whether to
debug live Google News or use another low-cost source for the first real sample.

### Why The Loop Continues

The live network barrier is logged, and an unblocked offline verification path
now exists.

## 2026-05-19 - Loop Cycle: Rio Offline Fixture Artifact

### Objective Reviewed

After adding the offline fixture, the loop had to prove that the dry-run report
path actually writes review artifacts outside production DB/assets/targets.

### Evidence

Commands passed:

```text
python -m py_compile tools/rio_economic_dry_run.py
pytest tests/test_rio_economic_dry_run.py -q
4 passed
```

Offline fixture command:

```text
tools/rio_economic_dry_run.py --offline-fixture --max-queries 3 --limit-per-query 1
```

Generated artifacts:

```text
data/reports/rio_economic_dry_run_20260518T214937Z.json
data/reports/rio_economic_dry_run_20260518T214937Z.csv
data/reports/rio_economic_dry_run_20260518T214937Z.md
```

Artifact metadata:

```text
row_count=3
query_count=3
offline_fixture=true
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

### Barrier Status

Live Google News dry-run remains blocked by runtime/network behavior. The
offline fixture proves only the review artifact path, not the quality of Rio
economic collection.

### Next Objective From Docs

Continue with one of these unblocked paths:

```text
debug live Google News timeout path ->
or add another low-cost source collector for first real Rio sample ->
or manually seed a small sourced review table outside production payloads
```

### Why The Loop Continues

The artifact format is proven, but the real sample has not been collected or
reviewed.

## 2026-05-19 - Loop Cycle: Resume After Context Compaction

### Objective Reviewed

The loop resumed from the long-term docs and the active next action. The
current axis remains Rio economic validation without contaminating existing
viewer/client scopes, while keeping the production segregation proof alive.

### State Observed

`git status` showed this branch behind `origin/master` by 4 commits. Local
changes are limited to:

```text
md documents/clipping-segregation-product-loop-2026-05-18/ACTIVE_NEXT_ACTION.md
md documents/clipping-segregation-product-loop-2026-05-18/LOOP_OPERATING_PROTOCOL.md
md documents/clipping-segregation-product-loop-2026-05-18/RIO_ECONOMIC_VALIDATION_PLAN.md
md documents/clipping-segregation-product-loop-2026-05-18/WORK_LOG.md
tools/rio_economic_dry_run.py
tests/test_rio_economic_dry_run.py
data/reports/rio_economic_dry_run_20260518T214937Z.*
```

Python bytecode under `pipeline/__pycache__/` was also dirty because tests ran.
Those files are generated local artifacts and should not be committed.

### Action Plan

Continue with path-limited cleanup, rebase onto current `origin/master`,
focused tests, path-limited commit, push to `master`, Render deploy check, and
then another docs review. No `git add .`.

### Why The Loop Continues

The context compaction was not a stopping point. It became a logged resume
checkpoint, then the loop proceeds to integration.

## 2026-05-19 - Loop Cycle: Path-Limited Rebase For Rio Tool

### Objective Reviewed

Before committing the Rio dry-run tool, the loop had to integrate with the
current `origin/master` without touching the Shakira/debug loop or inherited
work.

### Action Taken

Cleaned generated Python bytecode from `pipeline/__pycache__/`, stashed only
the Rio/protocol files and generated Rio report artifacts, fetched origin,
rebased onto current `origin/master`, and popped the stash back onto the updated
branch.

### Evidence

```text
git rebase origin/master -> success
git stash pop -> success
branch up to date with origin/master before new commit
```

### Barrier Status

No rebase conflict appeared. The next check is focused verification of the Rio
dry-run tool and its tests.

### Why The Loop Continues

Integration succeeded, but this still needs tests, a path-limited commit, push,
Render/deploy observation, and another docs review.

## 2026-05-19 - Loop Cycle: Rio Tool Verification Before Publish

### Objective Reviewed

The Rio dry-run tool must be proven as a safe review artifact path before it is
pushed. It must not write production DB, static client payloads, or target
configuration.

### Evidence

Commands passed:

```text
python -m py_compile tools/rio_economic_dry_run.py
pytest tests/test_rio_economic_dry_run.py -q
4 passed
git diff --check
```

The committed offline report artifact metadata still says:

```text
row_count=3
query_count=3
offline_fixture=true
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

### Action Taken

Removed generated `pipeline/__pycache__/` bytecode again after tests so the
commit stays path-limited to docs, the Rio tool, tests, and review artifacts.

### Barrier Status

Live Google News remains the unresolved runtime/network barrier. The safe
offline path is verified and ready to publish as a non-production review aid.

### Why The Loop Continues

Verification passed, but this still needs path-limited commit, push, deploy
observation, and then another long-term-doc review to pick the next weak axis.

## 2026-05-19 - Loop Cycle: Rio Tool Commit Prepared

### Objective Reviewed

Publish the verified Rio dry-run work without mixing it with the other active
debug loop.

### Action Taken

Created a path-limited commit for:

```text
tools/rio_economic_dry_run.py
tests/test_rio_economic_dry_run.py
data/reports/rio_economic_dry_run_20260518T214937Z.*
md documents/clipping-segregation-product-loop-2026-05-18/ACTIVE_NEXT_ACTION.md
md documents/clipping-segregation-product-loop-2026-05-18/LOOP_OPERATING_PROTOCOL.md
md documents/clipping-segregation-product-loop-2026-05-18/RIO_ECONOMIC_VALIDATION_PLAN.md
md documents/clipping-segregation-product-loop-2026-05-18/WORK_LOG.md
```

`origin/master` advanced by two commits during staging, so the local commit was
rebased onto the newer `origin/master` before push.

### Evidence

```text
git commit -> feat: add Rio economic dry-run report tool
git rebase origin/master -> success
HEAD after rebase -> 81caeb5 feat: add Rio economic dry-run report tool
```

### Barrier Status

Coordination barrier answered by rebase. Push and Render/deploy observation are
still pending.

### Why The Loop Continues

The commit exists locally, but the website acceptance bar requires pushing,
observing deploy state, and then continuing to the next review item.

### Coordination Update

`origin/master` advanced again before push. The Rio commit was rebased one more
time without conflict.

```text
git fetch origin -> success
git rebase origin/master -> success
HEAD after second rebase -> e36fb24 feat: add Rio economic dry-run report tool
```

### Push Evidence

The Rio dry-run commit was pushed to `master`:

```text
git push origin HEAD:master
e445d9f..9abba1f  HEAD -> master
```

### Next Objective From Docs

Check Render/deploy state, verify that the live privacy gate still holds, then
re-read the long-term docs before selecting the next weak axis.

## 2026-05-19 - Loop Cycle: Render Queue And Live Privacy Gate

### Objective Reviewed

After pushing the Rio dry-run commit, the loop must verify Render/deploy state
and keep the live privacy gate under observation.

### Render State

Render accepted the pushed commit:

```text
commit=9abba1f feat: add Rio economic dry-run report tool
deploy=dep-d86dq4f4fkgc73947350
status=queued
trigger=new_commit
```

At the same moment, an earlier deploy was still building and an older deploy was
live:

```text
live commit=9e3408d docs: log explainable error filter review
queued/building commits ahead of live: e445d9f, 9abba1f
```

### Live Evidence

Current production privacy gate still holds:

```text
GET /healthz -> 200
viewerAuthConfigured=true
viewerProfilesConfigured=true
missingConfig=[]
GET /assets/clipping-data.json -> 401 viewer_login_required
GET /api/targets -> 401 viewer_login_required
```

Local shell does not currently expose viewer/admin passwords, so authenticated
viewer proof is a live-credential barrier for this subcycle. This is not a stop:
logged-out proof is complete, Render state is observable, and the loop continues
with deploy polling and unblocked audits.

### Why The Loop Continues

Queued deploy is not completion and lack of local secrets is not completion.
The next actions are to keep polling Render, verify live health after deploy,
and re-read long-term docs for the next weak axis.

### Render Poll Update

After rebasing the local log onto the newest `origin/master`, Render showed the
deploy that contains the Rio commit plus later documentation commits:

```text
commit=f1e4652 docs: log clipping non-fast-forward barrier
status=build_in_progress
previous live=e445d9f docs: harden clipping output anchor
```

This means the Rio dry-run commit is no longer the tip, but it is in the live
candidate history. The loop must verify the final live commit after Render
finishes.

## 2026-05-19 - Loop Cycle: Target Management No-Fake-UI Audit

### Objective Reviewed

The docs require target management to be either fully connected end to end or
hidden from client viewers. While Render was still building, this was the next
unblocked checklist item.

### Code Read

Reviewed:

```text
web_app/app.py target routes
web_app/segmentation.py scoped target response helpers
assets/clipping.js target refresh/add/edit/archive/restore paths
assets/clipping.css viewer-readonly target management hiding
tests/test_admin_ui.py target/viewer/classification tests
```

### Evidence

The routes currently require server-side auth for target management:

```text
GET /api/targets -> require_viewer + scoped_targets_response
POST /api/targets -> require_admin + require_csrf
PATCH /api/targets/{target_key} -> require_admin + require_csrf
POST /api/targets/{target_key}/archive -> require_admin + require_csrf
POST /api/targets/{target_key}/restore -> require_admin + require_csrf
```

The viewer UI path hides non-base run tabs, add-target, and manage-target boxes
through `applyViewerControls()` plus `body.viewer-readonly` CSS.

Focused tests passed:

```text
pytest tests/test_admin_ui.py -k "target or viewer or classification" -q
17 passed, 24 deselected
```

Generated `pipeline/__pycache__/` files from the test run were restored and are
not part of the worktree.

### Barrier Status

No code gap was found in this read/test pass. The remaining limitation is live
authenticated viewer proof, blocked locally by unavailable passwords in shell.

### Why The Loop Continues

This audit supports the no-fake-UI rule, but it does not close the whole loop.
Render still needs final live verification, and the next long-term axes still
include Rio real-source validation and sellable packaging.

## 2026-05-19 - Loop Cycle: Additional Logged-Out Live Privacy Smoke

### Objective Reviewed

The Render production checklist requires logged-out users to be blocked from
private dashboard data, raw text, classifications, and live-results APIs.

### Evidence

Production checks on `https://clipping-project.onrender.com/`:

```text
GET /healthz -> 200
viewerAuthConfigured=true
viewerProfilesConfigured=true
missingConfig=[]
GET /assets/clipping-raw-texts.json -> 401 viewer_login_required
GET /api/classifications -> 401 viewer_login_required
GET /api/update/live-results?target_key=shakira -> 401 viewer_login_required
```

### Barrier Status

Authenticated viewer proof still needs credentials not available in the local
shell. Render deploy for the newest master is still in progress, so these
checks are a live privacy smoke, not final deploy completion.

### Why The Loop Continues

The logged-out gate remains healthy, but Render has not finished the newest
deploy and the loop still needs the next docs-derived action.

## 2026-05-19 - Loop Cycle: Rio Live Smoke Workaround

### Objective Reviewed

The Rio economic track had an unresolved live Google News runtime barrier. The
loop needed a workaround that collects real candidate rows without writing to
production DB, static assets, or target config.

### Cause Hypothesis

The likely hang point is Google redirect resolution. `fetch_url()` enforces a
future timeout, but the underlying thread can remain alive after cancellation.
For a Rio review smoke, resolving every redirect is not required; titles,
queries, publication dates, and candidate URLs are enough for first-pass human
labelling.

### Action Taken

Updated:

```text
pipeline/collectors.py
tools/rio_economic_dry_run.py
tests/test_collectors_restore.py
tests/test_rio_economic_dry_run.py
RIO_ECONOMIC_VALIDATION_PLAN.md
RIO_ECONOMIC_INDICATOR_TRACK.md
ACTIVE_NEXT_ACTION.md
```

Changes:

- `collect_google_news(..., resolve_timeout=0)` now skips Google redirect
  resolution and marks candidates with `redirect_resolution_skipped=true`;
- Rio dry-run defaults `--resolve-timeout` to `0` for safe smoke runs;
- report metadata records request/resolve/collection timeout settings;
- tests cover the skip path and report metadata.

### Evidence

Commands passed:

```text
python -m py_compile tools/rio_economic_dry_run.py pipeline/collectors.py
pytest tests/test_rio_economic_dry_run.py tests/test_collectors_restore.py -q
27 passed
```

Live dry-run command completed:

```text
tools/rio_economic_dry_run.py --date-from 2026-05-01 --date-to 2026-05-19 --max-queries 2 --limit-per-query 2 --request-timeout 5 --resolve-timeout 0 --collection-timeout 20
```

Generated artifacts:

```text
data/reports/rio_economic_dry_run_20260518T220015Z.json
data/reports/rio_economic_dry_run_20260518T220015Z.csv
data/reports/rio_economic_dry_run_20260518T220015Z.md
```

Artifact metadata:

```text
row_count=4
query_count=2
request_timeout=5
resolve_timeout=0
collection_timeout=20
redirect_resolution_skipped=true
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

Sample rows included tourism/hotelaria candidates from Google News. One row
from `"cidade do Rio" turismo` appears to be about another municipality in the
state, so it should be reviewed as `state_not_city` unless article content
proves a city-of-Rio economic signal.

### Barrier Status

The live Google News dry-run barrier is answered for review-smoke purposes.
Google redirect resolution itself remains a known runtime risk and should not
block first-pass Rio methodology validation.

### Why The Loop Continues

The dry-run now collects real candidates safely, but the sample still needs
manual labels, a 30-row review sample, and continued production segregation
checks after Render deploys.

## 2026-05-19 - Loop Cycle: Rebase Rio Workaround Onto Active Master

### Objective Reviewed

The other active loop pushed additional commits while the Rio workaround was
being verified. The local Rio work had to be preserved and rebased without
overwriting that work.

### Action Taken

Stashed only the Rio workaround files and live report artifacts, fetched
`origin`, rebased onto current `origin/master`, and popped the stash.

### Evidence

```text
origin/master before reapply -> 83eea61 docs: record manual live coverage
git rebase origin/master -> success
git stash pop -> success
no conflicts
```

### Barrier Status

Coordination barrier answered. The next step is a focused re-run of tests after
the rebase, then a path-limited commit and push.

### Why The Loop Continues

Rebase is not completion. The loop proceeds to verification, commit, push,
Render observation, and the next docs-derived action.

### Verification After Rebase

Commands passed after the rebase:

```text
python -m py_compile tools/rio_economic_dry_run.py pipeline/collectors.py
pytest tests/test_rio_economic_dry_run.py tests/test_collectors_restore.py -q
27 passed
```

Generated `pipeline/__pycache__/` bytecode was restored again before staging.

### Render Poll During Rebase Cycle

Render continued deploying commits from the other active loop while this Rio
workaround was being prepared:

```text
queued=1442477 docs: log hosted payload auth barrier
building=71b4a2b docs: log static target consistency audit
live=35900a1 docs: log publication fix regression
older Rio-containing deploy f1e4652 -> deactivated after newer commits
```

This is expected under active parallel work. The Rio commit is already in the
history, but this new workaround still needs its own path-limited push and
post-push Render observation.

### Second Coordination Rebase

`origin/master` advanced again before the workaround commit. The Rio workaround
was stashed path-limited, rebased, and reapplied without conflict.

```text
origin/master -> 1442477 docs: log hosted payload auth barrier
git rebase origin/master -> success
git stash pop -> success
```

Post-rebase verification repeated:

```text
python -m py_compile tools/rio_economic_dry_run.py pipeline/collectors.py
pytest tests/test_rio_economic_dry_run.py tests/test_collectors_restore.py -q
27 passed
```

Generated bytecode was restored before staging.

### Commit Prepared

Path-limited commit created:

```text
100b920 feat: make Rio dry-run skip redirect resolution
```

`origin/master` advanced once more before push, so the commit was rebased again:

```text
git rebase origin/master -> success
HEAD after rebase -> 409702a feat: make Rio dry-run skip redirect resolution
```

Push is still pending.

### Final Push Evidence

A final short rebase was needed immediately before push. The workaround reached
`master`:

```text
git fetch origin
git rebase origin/master -> success
git push origin HEAD:master
afc187c..e7b5e92  HEAD -> master
final pushed commit=e7b5e92 feat: make Rio dry-run skip redirect resolution
```

Render observed the pushed commit:

```text
deploy=dep-d86dum21dpfc73a26b60
commit=e7b5e92 feat: make Rio dry-run skip redirect resolution
status=queued
previous live=71b4a2b docs: log static target consistency audit
```

### Next Objective From Docs

Keep polling Render until this commit or a later commit reaches live, then run
logged-out production privacy checks again and return to the long-term docs for
the next weak axis.

### Live Privacy Smoke While Rio Deploy Queued

Production still enforces logged-out privacy while the Rio workaround deploy is
queued:

```text
GET /healthz -> 200
viewerAuthConfigured=true
viewerProfilesConfigured=true
missingConfig=[]
GET /assets/clipping-data.json -> 401 viewer_login_required
GET /assets/clipping-raw-texts.json -> 401 viewer_login_required
GET /api/targets -> 401 viewer_login_required
```

### Log Rebase After Push

Two more documentation commits landed after the Rio workaround push:

```text
acce5d3 docs: log hosted watch after no-export guard
ddcd558 docs: log collector rebase barrier
```

This WORK_LOG update was stashed, rebased onto `ddcd558`, and reapplied without
conflict before being prepared for a docs-only commit.

### Docs Push Evidence

The deployment-observation log was committed and pushed:

```text
commit=1d8eea3 docs: log Rio workaround deploy observation
git push origin HEAD:master -> success
```

Render accepted that docs commit:

```text
deploy=dep-d86dvg21dpfc73a26png
commit=1d8eea3 docs: log Rio workaround deploy observation
status=queued
```

### Latest Logged-Out Production Smoke

While Render was still deploying queued commits, production still enforced the
privacy gate:

```text
GET /healthz -> 200
viewerAuthConfigured=true
viewerProfilesConfigured=true
missingConfig=[]
GET /api/update/status -> 401 viewer_login_required
GET /api/csrf -> 401 viewer_login_required
```

### Next Objective From Docs

`ACTIVE_NEXT_ACTION.md` now points to expanding the Rio live sample toward 30
review rows without writing production DB/assets/targets, while Render polling
continues in parallel.

## 2026-05-19 - Loop Cycle: Rio 32-Row Live Sample

### Objective Reviewed

The Rio validation plan required a reviewable sample of at least 30 candidate
articles before adding any `rio_economico` target row or production ingestion.

### Action Taken

Ran a larger live Google News dry-run with redirect resolution skipped:

```text
tools/rio_economic_dry_run.py --date-from 2026-05-01 --date-to 2026-05-19 --max-queries 8 --limit-per-query 4 --request-timeout 5 --resolve-timeout 0 --collection-timeout 70
```

Generated artifacts:

```text
data/reports/rio_economic_dry_run_20260518T220725Z.json
data/reports/rio_economic_dry_run_20260518T220725Z.csv
data/reports/rio_economic_dry_run_20260518T220725Z.md
```

Artifact metadata:

```text
row_count=32
query_count=8
request_timeout=5
resolve_timeout=0
collection_timeout=70
redirect_resolution_skipped=true
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

Dimension counts:

```text
tourism_events=8
commerce_services=8
jobs_income=4
construction_real_estate=4
budget_finance=8
```

Added title-level triage notes:

```text
RIO_ECONOMIC_SAMPLE_REVIEW_20260518T220725Z.md
```

### Early Findings

Jobs and budget queries look more promising. Broad construction terms are weak.
Commerce and tourism queries have useful city signal but also pull state,
nearby-city, federal, or generic items.

### Barrier Status

The 30-row sample threshold is met for review purposes. It is not yet clean
enough to add a production target row.

### Why The Loop Continues

The next Rio step is query revision or query-file support, while the production
segregation loop still needs Render polling and viewer-profile proof when
credentials are available.

### Rebase After 32-Row Sample

`origin/master` advanced while the 32-row sample was being logged. The sample
artifacts and review note were stashed path-limited, rebased, and reapplied
without conflict.

```text
origin/master -> e2e3ba2 docs: log clipping auth barrier review
git rebase origin/master -> success
git stash pop -> success
```

### Push Evidence

The 32-row sample review reached `master`:

```text
git push origin HEAD:master
15fe6ad..072e406  HEAD -> master
commit=072e406 docs: add Rio economic 32-row sample review
```

Render accepted the commit:

```text
deploy=dep-d86e0c0c5kbs73akmf4g
commit=072e406 docs: add Rio economic 32-row sample review
status=queued
```

Production privacy smoke while deploys continue:

```text
GET /healthz -> 200
viewerAuthConfigured=true
viewerProfilesConfigured=true
missingConfig=[]
GET /assets/clipping-data.json -> 401 viewer_login_required
GET /api/classifications -> 401 viewer_login_required
```

### Next Objective From Docs

Implement a `--queries-file` path for `tools/rio_economic_dry_run.py` so revised
Rio query sets can be tested without editing code or creating a production
target row.

## 2026-05-19 - Loop Cycle: Rio Query File And Revised Sample

### Objective Reviewed

After the 32-row sample, the next Rio objective was to revise weak queries
without editing code or adding a production target row.

### Action Taken

Updated:

```text
tools/rio_economic_dry_run.py
tests/test_rio_economic_dry_run.py
data/reports/rio_economic_revised_queries_20260518.json
RIO_ECONOMIC_VALIDATION_PLAN.md
ACTIVE_NEXT_ACTION.md
RIO_ECONOMIC_REVISED_SAMPLE_REVIEW_20260518T221140Z.md
```

Changes:

- added `--queries-file` support for JSON query specs;
- added tests for loading custom query specs and running custom specs through
  `collect_rows`;
- created a revised 10-query Rio economic set;
- ran the revised sample without writing production DB/assets/targets.

### Evidence

Commands passed:

```text
python -m py_compile tools/rio_economic_dry_run.py
pytest tests/test_rio_economic_dry_run.py -q
6 passed
python -m json.tool data/reports/rio_economic_revised_queries_20260518.json
```

Revised dry-run command completed:

```text
tools/rio_economic_dry_run.py --queries-file data/reports/rio_economic_revised_queries_20260518.json --date-from 2026-05-01 --date-to 2026-05-19 --max-queries 10 --limit-per-query 3 --request-timeout 5 --resolve-timeout 0 --collection-timeout 80
```

Generated artifacts:

```text
data/reports/rio_economic_dry_run_20260518T221140Z.json
data/reports/rio_economic_dry_run_20260518T221140Z.csv
data/reports/rio_economic_dry_run_20260518T221140Z.md
```

Artifact metadata:

```text
row_count=29
query_count=10
queries_file=data/reports/rio_economic_revised_queries_20260518.json
request_timeout=5
resolve_timeout=0
redirect_resolution_skipped=true
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

### Early Findings

The revised set improved event/tourism, real-estate, licensing/works, and
ambulante-commerce signals. It still pulls Rio das Ostras, Rio Grande,
Porto Velho, Pernambuco/federal, and national tourism/jobs noise.

### Barrier Status

No production data contamination. The methodological blocker is now query
cleanup, not tooling.

### Why The Loop Continues

The next Rio step is testing negative terms/source anchors or adding explicit
title-level exclusion fields to the dry-run review before adding any production
target row.

## 2026-05-19 - Loop Cycle: Rio Title Exclusion Filter

### Objective Reviewed

The revised sample still had obvious false positives. The next unblocked step
was adding title-level exclusions to the query file/tool and proving the sample
gets cleaner without touching production data.

### Action Taken

Updated:

```text
tools/rio_economic_dry_run.py
tests/test_rio_economic_dry_run.py
data/reports/rio_economic_revised_queries_20260518.json
RIO_ECONOMIC_VALIDATION_PLAN.md
ACTIVE_NEXT_ACTION.md
RIO_ECONOMIC_REVISED_SAMPLE_REVIEW_20260518T221140Z.md
```

Changes:

- added `exclude_title_terms` support to query specs;
- filtered candidate rows whose titles contain configured exclusion terms;
- added test coverage for title exclusions;
- added known pollutants to the revised query file.

### Evidence

Commands passed:

```text
python -m py_compile tools/rio_economic_dry_run.py
pytest tests/test_rio_economic_dry_run.py -q
7 passed
python -m json.tool data/reports/rio_economic_revised_queries_20260518.json
```

Filtered dry-run command completed:

```text
tools/rio_economic_dry_run.py --queries-file data/reports/rio_economic_revised_queries_20260518.json --date-from 2026-05-01 --date-to 2026-05-19 --max-queries 10 --limit-per-query 3 --request-timeout 5 --resolve-timeout 0 --collection-timeout 80
```

Generated final filtered artifacts:

```text
data/reports/rio_economic_dry_run_20260518T221521Z.json
data/reports/rio_economic_dry_run_20260518T221521Z.csv
data/reports/rio_economic_dry_run_20260518T221521Z.md
```

Artifact metadata:

```text
row_count=26
query_count=10
queries_file=data/reports/rio_economic_revised_queries_20260518.json
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

Pollutant check on filtered sample:

```text
Rio das Ostras=0
Rio Grande=0
Porto Velho=0
portovelho=0
Pernambuco=0
```

The intermediate `20260518T221436Z` artifacts were generated before adding the
`portovelho` exclusion and then removed as superseded local artifacts.

### Barrier Status

The Rio methodology has cleaner review tooling now. It still needs manual
labelling and source-anchor refinement before any production target row.

### Why The Loop Continues

This reduces known false positives, but the loop must keep production
segregation verified and continue toward a clean Rio review methodology.

### Push Evidence

The title-exclusion filter reached `master`:

```text
git push origin HEAD:master
9365da9..5e30cae  HEAD -> master
commit=5e30cae feat: add Rio title exclusion filters
```

Render accepted the commit:

```text
deploy=dep-d86e4d0js32c739amqh0
commit=5e30cae feat: add Rio title exclusion filters
status=build_in_progress
previous live=9365da9 feat: support revised Rio economic query files
```

Production privacy smoke while deploy builds:

```text
GET /healthz -> 200
viewerAuthConfigured=true
viewerProfilesConfigured=true
missingConfig=[]
GET /assets/clipping-data.json -> 401 viewer_login_required
GET /api/targets -> 401 viewer_login_required
```

### Next Objective From Docs

Continue with title-level manual labelling of the cleaner Rio sample and source
anchor refinement before any `rio_economico` production target exists.

## 2026-05-19 - Loop Cycle: Rio Title-Level Labels

### Objective Reviewed

The cleaner 26-row Rio sample needed provisional labels before deciding whether
query quality is good enough for any production target consideration.

### Action Taken

Added:

```text
RIO_ECONOMIC_TITLE_LABELS_20260518T221521Z.md
```

Also updated the revised query file with `pernambucanos` as an exclusion after
title review found a Pernambuco false positive that did not include the exact
word `Pernambuco`.

### Evidence

Title-level tally:

```text
true_positive=18
useful_unclear=4
false_positive=3
unclear=1
```

Useful or unclear title-level share:

```text
22/26
```

### Findings

The methodology is now promising, especially for event/tourism impact,
real-estate, licensing/works, ambulantes, and municipal jobs. Budget/revenue
still mixes true municipal finance, economic-impact stories, and dimension
mismatches.

### Barrier Status

Still no production target row. Labels are title-level only and need source/body
review before ingestion.

### Why The Loop Continues

The next Rio step is source-anchor and dimension refinement. Production
segregation still needs Render polling and authenticated viewer proof when
credentials are available.

### Push Evidence

The title-level labels reached `master`:

```text
git push origin HEAD:master
5e30cae..90113ca  HEAD -> master
commit=90113ca docs: label cleaned Rio economic sample
```

Render accepted the commit:

```text
deploy=dep-d86e5bb7uimc738v5v3g
commit=90113ca docs: label cleaned Rio economic sample
status=build_in_progress
previous live=5e30cae feat: add Rio title exclusion filters
```

Production privacy smoke while deploy builds:

```text
GET /healthz -> 200
viewerAuthConfigured=true
viewerProfilesConfigured=true
missingConfig=[]
GET /assets/clipping-raw-texts.json -> 401 viewer_login_required
GET /api/update/live-results?scope=base&limit=20 -> 401 viewer_login_required
```

### Next Objective From Docs

Re-read the long-term docs and choose the next weak axis. Current candidate
axes: source-anchor/dimension refinement for Rio, sellable demo packaging, or
Render authenticated viewer proof if credentials become available.

## 2026-05-19 - Loop Cycle: Demo Profile Strategy

### Objective Reviewed

After Rio methodology and live segregation proof, the docs pointed back to
Axis 2: a sellable demo must not reuse Flavio/Shakira credentials, static
exports, or unsafe shared data.

### Action Taken

Added:

```text
DEMO_PROFILE_STRATEGY.md
```

Updated:

```text
FIRST_SELLABLE_PACKAGE.md
DEMO_SCRIPT_AND_BUYER_ASSUMPTIONS.md
ACTIVE_NEXT_ACTION.md
```

### Decision

Use three demo modes:

```text
Option A: empty demo_cliente privacy proof
Option B: operator screen-share for real content without sharing credentials
Option C: dedicated prospect profile with generated Render password and rotation
```

Do not give external buyers Flavio/Shakira credentials. Do not present static
exports as private client access.

### Barrier Status

No technical blocker. A serious hands-on buyer demo still needs a named
prospect profile/password and an offboarding note before access is shared.

### Why The Loop Continues

The demo strategy reduces sales risk, but the package still needs included
update frequency, delivery format, and continued Render live verification.

### Push Evidence

The demo strategy reached `master`:

```text
git push origin HEAD:master
90113ca..40219d8  HEAD -> master
commit=40219d8 docs: add safe demo profile strategy
```

Render accepted the commit:

```text
deploy=dep-d86e6hsm0tmc739scr50
commit=40219d8 docs: add safe demo profile strategy
status=build_in_progress
previous live=90113ca docs: label cleaned Rio economic sample
```

Production privacy smoke while deploy builds:

```text
GET /healthz -> 200
viewerAuthConfigured=true
viewerProfilesConfigured=true
missingConfig=[]
GET /assets/clipping-data.json -> 401 viewer_login_required
GET /api/csrf -> 401 viewer_login_required
```

### Next Objective From Docs

Define included update frequency and delivery format for the V1 package so the
sellable offer remains bounded and cost-aware.

## 2026-05-19 - Loop Cycle: V1 Delivery Scope

### Objective Reviewed

The first sellable package still needed concrete delivery boundaries so the
product does not become unlimited manual work.

### Action Taken

Added:

```text
V1_DELIVERY_SCOPE.md
```

Updated:

```text
FIRST_SELLABLE_PACKAGE.md
OPERATOR_COST_DISCIPLINE.md
ACTIVE_NEXT_ACTION.md
```

### Decision

Recommended first paid offer is a 30-day pilot:

```text
up to 5 monitored people/topics
2 operator-run updates per week
private dashboard
one weekly manual summary/export
business-hours password/access support
end-of-pilot renewal/scope review
```

Not included in base: realtime alerts, daily summaries, unlimited targets,
self-service target creation, custom site/repo, social/TV/radio/print
monitoring, crisis-room support, or finished Rio economic indicator.

### Barrier Status

No technical blocker. Pricing remains unfinalized until operator time/cost is
metered during a pilot.

### Why The Loop Continues

The sellable scope is bounded, but the loop still needs Render polling,
password/offboarding review, admin operator path testing when credentials are
available, and continued Rio source refinement.

### Rebase Before Publish

`origin/master` advanced while the V1 scope was being written. The V1 scope
docs were stashed path-limited, rebased, and reapplied without conflict.

```text
origin/master -> b184dd2 docs: log hosted watch after rule reaffirmation
git rebase origin/master -> success
git stash pop -> success
```

### Push Evidence

The V1 delivery scope reached `master`:

```text
git push origin HEAD:master
b184dd2..d0ebc1f  HEAD -> master
commit=d0ebc1f docs: define V1 clipping delivery scope
```

Render accepted the commit:

```text
deploy=dep-d86e7d8c5kbs73akq06g
commit=d0ebc1f docs: define V1 clipping delivery scope
status=queued
previous live=40219d8 docs: add safe demo profile strategy
```

Production privacy smoke while deploy queue moves:

```text
GET /healthz -> 200
viewerAuthConfigured=true
viewerProfilesConfigured=true
missingConfig=[]
GET /assets/clipping-data.json -> 401 viewer_login_required
GET /api/targets -> 401 viewer_login_required
```

### Next Objective From Docs

Review first-client onboarding/offboarding and password-rotation steps, then
continue Render polling.

## 2026-05-19 - Loop Cycle: First Client Onboarding Checklist

### Objective Reviewed

The sellable package still needed operational steps for creating, verifying,
rotating, and removing client/demo access without leaking secrets or reusing
private profiles.

### Action Taken

Added:

```text
FIRST_CLIENT_ONBOARDING_CHECKLIST.md
```

Updated:

```text
FIRST_SELLABLE_PACKAGE.md
ACTIVE_NEXT_ACTION.md
```

### Decision

Before any external access is shared, write down profile key, allowed targets,
delivery format, pilot dates, password recipient, and offboarding condition.
Then verify logged-out gates, scoped profile payload, raw texts, viewer write
rejection, and hidden operator controls.

### Barrier Status

No technical blocker. Actual first-client onboarding still requires a real
buyer/prospect and a password managed outside Git.

### Why The Loop Continues

The operational checklist is in place, but Render deploy still needs polling and
the admin/operator target-update path remains untested with live operator
credentials.

### Push Evidence

The query-file implementation and revised sample reached `master`:

```text
git push origin HEAD:master
072e406..9365da9  HEAD -> master
commit=9365da9 feat: support revised Rio economic query files
```

Render accepted the commit:

```text
deploy=dep-d86e2mm8bjmc73f40n3g
commit=9365da9 feat: support revised Rio economic query files
status=build_in_progress
previous live=072e406 docs: add Rio economic 32-row sample review
```

### Next Objective From Docs

Continue Rio cleanup by testing negative terms/source anchors or adding
title-level exclusion metadata to the dry-run review path.
