# Logs - Voluntarios Lab Politicas Publicas Backfill

Append-only operational log for the production onboarding and 2014-2026
backfill.

## 2026-06-02 16:13 America/Sao_Paulo - Start

- Received implementation request for the approved production plan.
- Confirmed local repo is already dirty with inherited changes; this task will
  touch only this task folder plus the external password note.
- Confirmed `/home/otavio/Documents/clipping-project senhas.md` exists.
- Production `/healthz` returned HTTP 200 with storage enabled and
  `localWritesAllowed=false`.
- Production `/healthz` also returned `job=status_unavailable`; this is a
  preflight risk. Next step is authenticated admin status verification before
  starting any update job.

## 2026-06-02 16:27 America/Sao_Paulo - Restart After Crash

- Previous Playwright attempt recovered its summary after the local crash.
- Admin login succeeded and the page loaded 32 existing targets.
- No target actions, viewer action, password write, or update job start were
  recorded by that attempt.
- The attempt failed while filling `#addPrimaryTargetForm textarea[name="keywords"]`
  because the field lives inside the collapsed `Ajustar busca` details element.
- Resume rule: use Playwright through the visible UI, explicitly opening both
  the primary-target details and its advanced-search details before adding or
  reusing targets.

## 2026-06-02 16:44 America/Sao_Paulo - Authenticated Production Probe

- Confirmed admin credential from the local password note without printing it.
- Playwright UI login succeeded by selecting authenticated access before
  filling the password.
- `/api/targets?include_archived=1` returned HTTP 200 in 167 ms with 32 total
  targets.
- Requested target state: 14 of 18 requested keys exist, all primary and not
  archived.
- Missing target keys: `percepcao_de_seguranca`,
  `sensacao_de_seguranca`, `reforco_no_policiamento`, `ordem_publica`.
- `/api/admin/viewers` returned HTTP 200 in 240 ms; profile
  `voluntarios_lab_politicas` does not exist yet.
- `/api/update/status`, `/api/admin/debug/memory`, and
  `/api/admin/debug/disk` returned HTTP 200; status payload currently reports
  `status_unavailable`.
- Next action: create the four missing primary targets through the visible UI,
  then re-run the authenticated state check before creating the viewer profile.

## 2026-06-02 16:50 America/Sao_Paulo - Primary Target UI Submit Bug

- Tried to create `percepcao_de_seguranca` through the visible
  `Adicionar nome principal` UI after opening both the outer details and
  `Ajustar busca`.
- Pre-click diagnostics: form was valid, display/keyword fields were visible
  and enabled, and the submit button was visible and enabled.
- Actual click did not send any `/api/targets/primary` request.
- Browser navigated to `/?display_name=...&keywords=...&exact_aliases=`,
  meaning the form fell back to native GET submission.
- Production impact: the primary-target submit handler is not attached for this
  form in the deployed UI, so an end user cannot currently add a primary target
  from the UI even though the form appears usable.
- No target was created by this failed UI attempt.
- Next action: inspect deployed JS/page errors, then choose the safest
  production recovery that still records this UI-facing defect.

## 2026-06-02 16:55 America/Sao_Paulo - Operator Error And Correction

- Mistake: after finding the broken `Adicionar nome principal` UI, I tried a
  secondary-create-then-promote recovery path without stopping to fix the
  broken primary-target UI first.
- Production state check after that mistake: `percepcao_de_seguranca` exists
  as a secondary target (`primary=false`, `archived=false`) with the intended
  keyword variants. No other missing phrase target was created.
- User corrected the workflow: when Playwright finds a broken end-user path,
  fix that path. Do not work around it by creating secondary targets.
- Current barrier: deployed `/assets/clipping.js` does not contain the
  `addPrimaryTargetForm` handler or `/api/targets/primary`, while production
  HTML exposes `#addPrimaryTargetForm`. This JS/HTML mismatch is why the visible
  primary form falls back to native GET submission.
- Next action: fix/deploy the primary-target UI path, verify with Playwright,
  then use the repaired primary UI to make production state satisfy the
  code-level primary-target contract.

## 2026-06-02 17:51 America/Sao_Paulo - Primary UI Fix Deployed

- Found the live `/assets/clipping.js` hash matched
  `tools/pages_assets/clipping.js`, not committed `assets/clipping.js`.
- Cause: the snapshot/template bundle lacked the `addPrimaryTargetForm`
  handler even though the root asset had it.
- Pushed deploy trigger commit `faa22ea`; Render marked it live, but the
  served JS remained the old template hash.
- Patched and pushed `cac290b` (`fix(ui): add primary target handler to
  snapshot bundle`) with only the primary-target template handler/visibility
  fix staged.
- Render deploy `dep-d8fk3hrrjlhs73c64lh0` became live at
  `2026-06-02T20:51:46Z`.
- Production `/assets/clipping.js?v=primary-template-fix-cac290b` changed to a
  143726-byte asset containing both `addPrimaryTargetForm` and
  `/api/targets/primary`.
- Next action: use Playwright against production to promote the accidental
  secondary `percepcao_de_seguranca` through the management UI and create the
  remaining missing targets through the repaired primary-target UI.

## 2026-06-02 17:58 America/Sao_Paulo - Targets Repaired Through UI

- Playwright verified production JS contains `addPrimaryTargetForm` and
  `/api/targets/primary`.
- Used the visible management UI to promote the accidental secondary
  `percepcao_de_seguranca`; production state now reports it as
  `primary=true`, `archived=false`.
- Used the repaired `Adicionar nome principal` UI to submit
  `sensacao_de_seguranca`, `reforco_no_policiamento`, and `ordem_publica`.
- Each of those three UI submits sent `POST /api/targets/primary` and created
  a production target with `primary=true`, but the response returned HTTP 500
  after the write. The page therefore showed "Não foi possível salvar este nome
  principal" even though the target was saved.
- State check after the UI submissions: all 18 requested keys exist, are
  `primary=true`, and are not archived.
- User-facing bug fixed next: patched `target_mutation_response` so post-save
  artifact/status warnings do not invert a successful target mutation into HTTP
  500.
- Pushed `25e2cec` (`fix(targets): keep post-save warnings from failing UI`);
  Render deploy `dep-d8fk7d8jo6nc73fp2m70` became live at
  `2026-06-02T20:59:40Z`.
- Next action: create or update viewer profile
  `voluntarios_lab_politicas` through the production UI with all 18 targets,
  save the generated password only in the external password note, and verify
  viewer login/scope.

## 2026-06-02 18:03 America/Sao_Paulo - Viewer Profile Created

- Playwright admin UI confirmed all 18 requested targets are present,
  `primary=true`, and not archived before profile creation.
- Created viewer profile through `Clientes (viewers)` UI:
  `voluntarios_lab_politicas`.
- Label: `Voluntários-Lab-Políticas-Públicas`.
- UI response: HTTP 200, `Cliente "voluntarios_lab_politicas" criado.`
- Admin listing confirms `target_count=18`, `default_count=18`,
  `has_password=true`, no missing keys.
- Generated 28-character password and saved it only in
  `/home/otavio/Documents/clipping-project senhas.md`.
- Fresh viewer login succeeded with session role `viewer`, profile
  `voluntarios_lab_politicas`.
- Viewer `/api/targets` returns exactly the 18 requested keys, all primary, no
  extras.
- Viewer dashboard payload has exactly 18 `defaultTargets`.
- Viewer update runner renders 18 primary checkboxes, all checked by default,
  no extras.
- Next action: production backfill preflight and one UI-started update job for
  `2014-01-01` through `2026-06-02`.

## 2026-06-02 18:07 America/Sao_Paulo - Backfill Start Barrier

- Preflight health: HTTP 200; storage enabled (`documentos`,
  `clipping-project`); `localWritesAllowed=false`.
- CSRF: HTTP 200.
- Target contract before start: all 18 requested keys present, primary, and not
  archived.
- Memory before start: `VmRSS=273.12 MiB`, `VmHWM=598.88 MiB`, Render limit
  512 MiB.
- Disk before start: filesystem free `50235.42 MiB`, DB `140.36 MiB`,
  WAL `0 MiB`.
- `/api/update/status` preflight returned HTTP 200 but payload
  `current.status=status_unavailable`, `debug_error_type=OperationalError`,
  `debug_error_message=disk I/O error`.
- Playwright selected exactly the 18 requested keys in the update runner and
  set dates `01/01/2014` through `02/06/2026`.
- `POST /api/update/start` returned HTTP 500 (`Internal Server Error`), and
  the UI showed `Não foi possível iniciar a atualização.`
- Post-start `/api/update/status` still reports `status_unavailable` with
  `disk I/O error`; no job id was returned and recent jobs are empty.
- `/api/update/live-results?scope=base&limit=60` returned HTTP 500.
- Barrier rule activated: do not retry blindly and do not start a duplicate
  full job. Next action is inspect/fix the production disk I/O/status barrier,
  then start the single full job from the recorded state.

## 2026-06-02 18:12 America/Sao_Paulo - SQLite Barrier Repair Patch

- Re-checked production after the latest deploy: `/healthz` still reports
  `job=status_unavailable`, `/api/update/status` still reports
  `OperationalError: disk I/O error`, and base live results still return HTTP
  500.
- Confirmed production filesystem capacity is not the barrier:
  free space is about `53458.54 MiB`; DB is `140.36 MiB`; WAL is `0 MiB`.
- Confirmed target/profile contract remains correct: all 18 requested keys are
  present as `primary=true`, `className=primary`, not archived; viewer
  `voluntarios_lab_politicas` still has all 18 target/default keys and a
  password.
- Local DB quick/integrity checks pass; local jobs count is 0.
- Render deploy metadata is available, but Render logs are blocked because the
  workspace is not selected in the connector.
- Implemented a narrow repair patch:
  - `web_app/db_admin.py`: app-level SQLite connect now falls back from WAL to
    DELETE journal mode when `PRAGMA journal_mode = WAL` raises the observed
    `disk I/O error`.
  - `web_app/app.py`: added admin+CSRF-only `/api/admin/debug/sqlite` with
    `action=report` and explicit `action=rebuild_from_current` diagnostic/repair
    flow. The rebuild path makes a pre-repair backup, copies the current DB
    through SQLite backup into a clean file, validates `PRAGMA quick_check`, then
    atomically replaces the current DB and uploads artifacts.
- Verification before deploy: `compileall web_app/app.py web_app/db_admin.py`
  passed; focused pytest passed for the WAL fallback and `/healthz` schema.
- Next action: deploy the repair patch, run the SQLite report endpoint, repair
  only if status/live-results remain blocked, then start the single production
  backfill job once through the UI.
