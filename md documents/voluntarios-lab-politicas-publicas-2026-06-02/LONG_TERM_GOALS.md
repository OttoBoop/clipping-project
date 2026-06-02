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
