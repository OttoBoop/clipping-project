# Long-Term Goals - Voluntarios Lab Politicas Publicas Backfill

Created 2026-06-02 for the production onboarding/backfill of
Voluntarios-Lab-Politicas-Publicas.

## Contract

This is an online production task. Local commands may inspect code and create
operator memory files, but the profile, targets, password, ingestion job, and
monitoring must happen against the production clipping app.

Viewer profile:

- label: `Voluntários-Lab-Políticas-Públicas`
- key: `voluntarios_lab_politicas`
- type: standard passworded viewer, not demo/read-only
- target scope: all 18 requested code-level primary targets
- default targets: all 18 requested code-level primary targets

The phrase primary target means the clipping code field:

- `primary: true`
- `className: "primary"`

Primary targets must appear as primary chips, be default-selected in the
dashboard, and be checked by default in the update runner.

## Exact Primary Targets

- Segurança Presente
- Programa Segurança Presente
- Operação Segurança Presente
- segurança
- insegurança
- crime
- criminalidade
- violência
- assalto
- roubo
- furto
- medo
- policiamento
- patrulhamento
- percepção de segurança
- sensação de segurança
- reforço no policiamento
- ordem pública

Expected keys, unless production already has active duplicates:

- `seguranca_presente`
- `programa_seguranca_presente`
- `operacao_seguranca_presente`
- `seguranca`
- `inseguranca`
- `crime`
- `criminalidade`
- `violencia`
- `assalto`
- `roubo`
- `furto`
- `medo`
- `policiamento`
- `patrulhamento`
- `percepcao_de_seguranca`
- `sensacao_de_seguranca`
- `reforco_no_policiamento`
- `ordem_publica`

## Backfill Rule

Run one production update job:

- preset: `custom`
- collector: `all`
- target keys: all 18 production keys
- date from: `2014-01-01`
- date to: `2026-06-02`
- export: `true`

This is intentionally large. Do not start a duplicate full job. If the job
fails, becomes resumable, or reports source failures, inspect and resume/fix
from the recorded state.

## Active Recovery Loop - 2026-06-04

Treat the current run as an incident recovery, not a new backfill.

- active production job id: `0b36e332911a`
- success condition: all `22912` source-runs complete for the exact 18 primary
  targets from `2014-01-01` through `2026-06-02`
- do not call `/api/update/start` for this task unless the user explicitly
  revokes the one-job rule
- use `/api/update/resume` only for job `0b36e332911a` when production reports
  `interrupted_resumable`
- current documented recovery floor after deploy/storage interruption:
  `complete=23`; no newer verified checkpoint was available from the safe
  operator surface
- Render connector visibility is limited unless the user selects a workspace;
  deployment state must be inferred from production endpoints when the connector
  reports `no workspace set`

Dedicated operator script:

- `python3 tools/voluntarios_backfill_operator.py audit`
- `python3 tools/voluntarios_backfill_operator.py repair-password`
- `python3 tools/voluntarios_backfill_operator.py resume-same-job`
- `python3 tools/voluntarios_backfill_operator.py monitor --cycles 4 --interval 60 --stall-cycles 3 --memory-danger-cycles 2`
- `.venv_playwright/bin/python tools/voluntarios_backfill_operator.py ui-check`

The script must read credentials without printing them and write append-only
entries to `LOGS.md`. Password drift is repaired by resetting only the
`voluntarios_lab_politicas` viewer password and saving the plaintext only in
`/home/otavio/Documents/clipping-project senhas.md`.

Current production fix deployed for this incident:

- commit `d6e8dc6 fix(storage): stream sqlite checkpoint uploads`
- purpose: avoid materializing the full SQLite snapshot and gzipped DB in memory
  during live/current artifact uploads
- post-deploy monitoring evidence: live results, asset timestamps, and source
  events advanced while RSS stayed below the danger band across monitored
  checkpoint cycles
- commit `97e75c1 fix(jobs): throttle empty source checkpoints`
- purpose: avoid forcing live checkpoint uploads after empty source-runs and
  give the single-process web service a small cooperative yield between durable
  source-runs
- operational rule: source-runs with saved articles may force checkpoint
  durability; empty source-runs must use the normal checkpoint throttle unless
  an explicit repair action overrides it
- post-deploy evidence: after resume and password repair, 4 monitor cycles had
  no barriers, HTTP endpoints stayed responsive, live/assets advanced when
  saved articles appeared, and Playwright verified the exact viewer contract

Backend scheduler correction prepared after low-volume review:

- durable jobs with more than one `target_key` must be treated as grouped
  source coverage, not as a serial queue of one full source plan per target
- grouped source-runs use target key `__all_targets__` and must ingest against
  every selected target snapshot from the job spec
- the source ledger for this task should remain approximately one row per
  source/window/query-page family, not 18 duplicated source ledgers
- if job `0b36e332911a` resumes with legacy per-target source-run rows, the
  backend may migrate those rows to the grouped ledger for the same job id; this
  is not a duplicate job and must be logged as `source_run_ledger_migrated`
- after deploying this correction, acceptance monitoring must verify
  `sourceRunTargetCounts` is grouped under `__all_targets__`, source type counts
  match the grouped plan, events include all 18 `target_keys`, and live results
  advance from broad targets as well as `seguranca_presente`

## Monitoring Protocol

Before starting the job, verify:

- production health is reachable;
- admin login and CSRF work;
- storage is enabled;
- there is no conflicting active job;
- `/api/update/status` is usable through the authenticated session.

During the job, record in `LOGS.md`:

- timestamp;
- job id;
- status and coverage state;
- current target/source;
- source-run counts;
- article/mention/story totals;
- memory and disk status;
- recent source-run events;
- live-results proof;
- any barrier and the next action.

Danger signs:

- `failed_needs_fix`;
- `interrupted_resumable`;
- repeated 5xx responses;
- `disk I/O error`;
- dangerous memory pressure near the Render process limit;
- long stalls with no source-run progress.

When any danger sign appears, stop blind waiting, log the barrier, inspect the
source-run events, and continue with the next safe operational step.

## Recovery Rules

- Never print passwords in chat or logs.
- Save the generated viewer password only in
  `/home/otavio/Documents/clipping-project senhas.md`.
- Production state is source of truth for this task.
- Local docs are operational memory, not a substitute for live verification.
- Keep the log append-only except for correcting a typo in the current entry.
