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

## 2026-05-18 - First Technical Loop: Password-Gated Scoped Views

### Changes Made

- Added viewer-profile sessions alongside the existing admin session.
- Added `CLIPPING_VIEWER_PASSWORDS` support for profile passwords and default
  profile scopes for `flavio`, `shakira`, `rio_economico`, and `demo_cliente`.
- Replaced open static serving for `assets/clipping-data.json` and
  `assets/clipping-raw-texts.json` with authenticated scoped handlers.
- Added server-side payload filtering for targets, stories, articles,
  classifications, live results, and raw text.
- Gated update, export, target mutation, category creation, and classification
  writes to admin sessions.
- Updated the dashboard so non-admin viewers land on Base atual and do not see
  runner, target-management, or classification-editor controls.
- Preserved static export usability with `data-clipping-static="1"` and
  `apiAvailable` guards so generated static bundles do not call protected
  `/api/*` routes.
- Added tests proving logged-out JSON access is blocked, Shakira viewer payloads
  exclude Flavio data, raw text is filtered, direct live-results query params
  cannot widen scope, and viewer writes are rejected.

### Coordination And Dirty Worktree Notes

- `web_app/app.py` already had an inherited `recent_jobs(include_observability=False)`
  diff. This implementation touched the same endpoint and kept that behavior
  intentionally because status polling must stay lightweight.
- `md documents/amio-clipping-repair-2026-05-18/WORK_LOG.md` became dirty with a
  separate static-export loop entry while this work was in progress. This loop
  does not own that file, so it must not be staged here.
- The shared `Who_Is_Doing_What` file remains dirty from inherited coordination
  work and was not edited by this loop.

### Verification

Passed:

```bash
python -m py_compile web_app/auth.py web_app/segmentation.py web_app/app.py
```

Passed:

```bash
.venv_playwright/bin/pytest tests/test_admin_ui.py tests/test_targets_jobs.py tests/test_sprint_regression_harness.py tests/test_export_mobile_snapshot_pages.py -q
```

Result: `99 passed in 2.47s`.

Passed:

```bash
.venv_playwright/bin/pytest -q
```

Result: `251 passed, 1 skipped in 189.04s`.
