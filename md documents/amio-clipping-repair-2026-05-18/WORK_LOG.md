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
