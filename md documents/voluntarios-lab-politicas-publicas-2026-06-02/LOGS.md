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

## 2026-06-02 18:23 America/Sao_Paulo - Stale Auto-Resume Barrier

- Repair deploy `5fce2ff` became live at `2026-06-02T21:16:25Z`.
- The WAL fallback temporarily restored job observability, but startup then
  auto-resumed old job `7c1e4b144df0` from `2026-05-22`.
- This old job is not the requested Voluntarios backfill. Its target list is
  `flavio_valle`, `pedro_angelito`, `smoke_sec_1779237862_2965`, and
  `seguranca_presente`; its date range is `2014-01-01` through `2026-05-22`.
- Because that job was running, the requested 18-target backfill was not
  started. The one-full-job constraint for this task remains intact.
- Source-run events showed the stale job processing `flavio_valle` /
  `wordpress_api` (`Agenda do Poder`) after startup resume.
- Attempted to cancel through the visible UI with Playwright. First UI-login
  attempt did not authenticate; second run authenticated the browser through
  `/api/login`, but the rendered page did not show an enabled cancel button and
  no `/api/update/cancel` request was sent.
- After the stale job resumed, SQLite regressed: `/api/update/status` again
  reports `OperationalError: disk I/O error`; the new SQLite report endpoint
  shows both read-only and app-level probes failing on `journal_mode`,
  `quick_check`, and table queries. Disk capacity remains fine
  (`free_mib` about `52318.62`; DB about `140.39 MiB`; WAL `0 MiB`).
- Implemented a second repair patch:
  - startup auto-resume is now disabled unless `CLIPPING_AUTO_RESUME_JOBS` is
    explicitly true;
  - `/api/admin/debug/sqlite` now has explicit confirmed actions for
    `clear_sidecars` and `restore_latest_backup`;
  - DB replacement paths clear the app-table initialization cache before
    re-checking schema.
- Verification before deploy: `compileall web_app/app.py web_app/db_admin.py`
  passed; focused pytest passed for the WAL fallback and `/healthz` schema.
- Next action: deploy this recovery patch, confirm production starts without
  auto-resuming the stale job, use the SQLite recovery endpoint if needed, then
  verify idle status before starting the requested backfill.

## 2026-06-02 18:29 America/Sao_Paulo - Requested Backfill Started

- Recovery deploy `5c8876b` became live at `2026-06-02T21:26:37Z`.
- Post-deploy production check: SQLite readable (`quickCheck=ok` for read-only
  and app probes), `activeJobsCount=0`, live-results HTTP 200, and no stale job
  auto-resumed.
- Memory before start: `VmRSS=119.99 MiB`, `VmHWM=404.66 MiB`, Render limit
  512 MiB.
- Disk before start: free `49504.2 MiB`; DB `140.7 MiB`; WAL `8.13 MiB`; SHM
  `0.03 MiB`.
- Used the update runner UI with Playwright:
  - 27 target checkboxes rendered in the admin runner.
  - Before correction, admin defaults checked 20 primary targets including
    `flavio_valle` and `pedro_angelito`.
  - Explicitly unchecked all extras and checked exactly the 18 requested
    Voluntarios primary targets.
  - Secondary checked targets: none.
  - Dates set to `01/01/2014` through `02/06/2026`.
  - Heavy-run warning displayed as expected: 12.4-year window and 18 targets.
- Submitted `/api/update/start` through the UI. Response HTTP 200.
- Production job id: `0b36e332911a`.
- Job contract in response:
  - `preset=custom`
  - `collector=all`
  - `date_from=2014-01-01`
  - `date_to=2026-06-02`
  - `export=true`
  - `target_keys` exactly the 18 requested keys.
- Immediate status after start: `running`, totals
  `articles=0`, `mentions=0`, `stories=0`, `coverageState=pending`.
- Next action: monitor status, source-run events, memory, disk, and live
  results continuously; stop blind waiting on failures, 5xx, disk I/O, or
  dangerous memory pressure.

## 2026-06-02 18:30 America/Sao_Paulo - Monitoring Snapshot 1

- Job `0b36e332911a` remains `running`, `coverageState=pending`.
- Endpoint health this cycle: status 200, source-run events 200, memory 200,
  disk 200, live-results 200.
- Totals still `articles=0`, `mentions=0`, `stories=0`.
- Source-run ledger: `sourceRunCount=22912`, visible 80; counts
  `complete=3`, `running=1`, `pending=22908` in the status payload.
- Recent source-run events show initial RSS runs for `seguranca_presente`:
  `VEJA`, `VEJA RSS`, `VEJA Politica`, and `VEJA Cidades` completed with no
  errors; most saw 20 candidates, no saved articles yet.
- Current visible source at snapshot: `seguranca_presente` / RSS /
  `VEJA Cidades`.
- Memory: `VmRSS=211.51 MiB`, `VmHWM=468.75 MiB`, limit 512 MiB.
- Disk: free `47233.27 MiB`; DB `149.7 MiB`; WAL `10.81 MiB`; SHM
  `0.03 MiB`.
- Live-results base endpoint returned 60 items.
- No barrier detected. Next action: continue monitoring for progress, source
  failures, memory pressure, disk I/O, or 5xx responses.

## 2026-06-02 18:32 America/Sao_Paulo - Monitoring Snapshot 2 / Memory Pressure

- Job `0b36e332911a` remained `running`; status endpoint HTTP 200.
- Source-run ledger: `sourceRunCount=22912`; counts moved to
  `complete=7`, `pending=22905`.
- Recent RSS completions for `seguranca_presente`: `Veja Rio`, `G1`,
  `G1 Politica`, all with no source-run errors.
- Totals in the snapshot initially showed `articles=0`, `mentions=0`,
  `stories=0`.
- Memory danger sign: `VmRSS=518.73 MiB`, `VmHWM=518.73 MiB`, above the
  documented 512 MiB Render limit.
- Immediate confirmation check: job still `running`, `coverageState=running`;
  current memory dropped to `VmRSS=267.67 MiB` while `VmHWM=517.96 MiB`.
- Confirmation totals: `articles=0`, `mentions=100`, `stories=100`; recent
  event showed `G1 Rio` RSS completed with 100 candidates and no error.
- Disk during snapshot: free `60722.27 MiB`; DB `149.7 MiB`; WAL `10.81 MiB`.
- Decision: do not cancel while current RSS has dropped and endpoints are
  healthy, but tighten monitoring cadence because peak RSS crossed the limit.
- Next action: continue monitoring closely; cancel/repair if current RSS rises
  back to dangerous pressure, endpoints return 5xx, or job becomes failed /
  interrupted.

## 2026-06-02 18:34 America/Sao_Paulo - Monitoring Snapshot 3 / Source Failure Inspected

- Job `0b36e332911a` still `running`; status/source-events/memory/disk/live
  endpoints all HTTP 200.
- Coverage state now reports `failed_needs_fix` because one source failed while
  the job continues processing remaining sources.
- Source-run counts: `complete=12`, `failed_needs_fix=1`, `running=1`,
  `pending=22898`.
- Failed source isolated:
  - target: `seguranca_presente`
  - source key: `rss:8`
  - source: `O Globo`
  - source type: `rss`
  - error: `not well-formed (invalid token): line 1, column 0`
- Recent healthy RSS completions include `Extra`, `Folha`, `UOL`, `Band`, and
  `Estadao`, with no errors.
- Local check of `https://oglobo.globo.com/rss.xml` returned valid XML, so this
  currently looks like a transient/source-response failure rather than a
  permanent parser bug.
- Memory: current `VmRSS=270.05 MiB`, high-water `VmHWM=530.32 MiB`; continue
  close monitoring because the peak crossed the nominal limit.
- Disk: free `60731.77 MiB`; DB `149.79 MiB`; WAL `10.81 MiB`.
- Decision: do not cancel while the job is still progressing and current RSS is
  stable. If the job ends as `failed_needs_fix`, manually resume/retry failed
  sources from the recorded state rather than starting a duplicate full job.

## 2026-06-02 18:36 America/Sao_Paulo - Monitoring Snapshot 4

- Job `0b36e332911a` still `running`; all monitored endpoints HTTP 200.
- Coverage state remains `failed_needs_fix` because of the earlier O Globo RSS
  failure, but the job is continuing through remaining sources.
- Source-run counts: `complete=18`, `failed_needs_fix=1`, `running=1`,
  `pending=22892`.
- Totals advanced to `articles=33`, `mentions=133`, `stories=133`.
- Source family progress: RSS for `seguranca_presente` has moved through
  `Agencia Brasil`, `Diario do Rio`, `Tempo Real RJ`, `Agenda do Poder`, and
  `Tribuna da Serra`; current event sample shows `Google News` started.
- Memory: current `VmRSS=332.0 MiB`; high-water `VmHWM=536.4 MiB`; continue
  close monitoring.
- Disk: free `60745.99 MiB`; DB `151.25 MiB`; WAL `10.81 MiB`.
- No new source failures in the sample. Next action: continue monitoring,
  especially Google News memory and any additional `failed_needs_fix` sources.

## 2026-06-02 18:40 America/Sao_Paulo - Monitoring Snapshot 5

- Job `0b36e332911a` still `running`; all monitored endpoints HTTP 200.
- Coverage state remains `failed_needs_fix` due to the earlier O Globo RSS
  source failure.
- Source-run counts: `complete=19`, `failed_needs_fix=1`, `running=1`,
  `pending=22891`.
- Google News completed for `seguranca_presente`: 100 candidates, 98 articles,
  98 mentions, 98 stories, no error.
- Totals advanced to `articles=98`, `mentions=198`, `stories=198`.
- Current source family has moved to WordPress API; latest event shows
  `Diario do Rio` started.
- Memory: current `VmRSS=367.98 MiB`; high-water `VmHWM=583.49 MiB`.
- Disk: free `60893.54 MiB`; DB `158.26 MiB`; WAL `0.17 MiB`.
- Decision: continue close monitoring; no cancellation while current RSS is
  below the wall and source progress is healthy, but HWM remains a serious risk
  signal.

## 2026-06-02 18:45 America/Sao_Paulo - SQLite Barrier During Job

- Monitoring snapshot 6 hit a hard barrier:
  - `/api/update/status` HTTP 200 but `current.status=status_unavailable`;
  - `/api/update/live-results?scope=base&limit=60` returned HTTP 500;
  - source-run events endpoint returned HTTP 200 but body included
    `error=disk I/O error`;
  - SQLite debug report showed read-only and app probes failing on
    `journal_mode`, `quick_check`, and table queries.
- File state at barrier: DB `159.99 MiB`; WAL `0 MiB`; no SHM listed.
- Memory at barrier: current `VmRSS=366.37 MiB`; high-water
  `VmHWM=619.19 MiB`.
- Disk capacity remained fine: free `60566.74 MiB`.
- Ran confirmed `/api/admin/debug/sqlite` action `clear_sidecars`. It removed
  `/opt/render/project/src/data/clipping.db-wal`, but post-repair probes still
  failed with `disk I/O error`.
- Current DB is therefore unreadable in-process. Do not blind-wait and do not
  start another full job.
- Recovery decision: trigger a controlled redeploy/restart so startup downloads
  the latest uploaded storage snapshot. Because `CLIPPING_AUTO_RESUME_JOBS` is
  not enabled after commit `5c8876b`, the job should come back as
  interrupted/resumable instead of auto-running. Then inspect state and resume
  manually from the checkpoint if the DB is readable.

## 2026-06-02 18:48 America/Sao_Paulo - Restart Recovery Check

- Log commit/restart deploy `f3b67a8` became live at
  `2026-06-02T21:47:44Z`.
- Post-restart SQLite state is healthy: read-only and app probes both report
  `quickCheck=ok`, `journalMode=wal`, `activeJobsCount=0`.
- Job `0b36e332911a` is now `interrupted_resumable`, not auto-resumed.
- Preserved job totals: `articles=112`, `mentions=212`, `stories=212`.
- Source-run counts after restart: `complete=19`, `failed_needs_fix=1`,
  `interrupted_resumable=22892`.
- Last source events before interruption: `Diario do Rio` WordPress API
  checkpoint saw 25 candidates and saved 6 articles/mentions/stories; previous
  Google News source completed with 98 articles/mentions/stories.
- Memory after restart: `VmRSS=129.82 MiB`, `VmHWM=450.4 MiB`.
- Disk after restart: free `46290.43 MiB`; DB `161.79 MiB`; WAL `8.25 MiB`;
  SHM `0.03 MiB`.
- Recovery decision before manual resume: patch the runner to reduce memory
  pressure by clamping candidate worker concurrency and explicitly releasing
  source candidate batches after each source. Then deploy, verify the job is
  still resumable, and resume manually from `0b36e332911a`.

## 2026-06-02 18:51 America/Sao_Paulo - Memory-Safety Patch Before Resume

- Implemented `web_app/jobs.py` memory-safety patch before resuming:
  - added `effective_candidate_workers(spec)`;
  - default `CLIPPING_MAX_CANDIDATE_WORKERS` clamp is `1`, so a stored spec with
    `candidate_workers=4` now runs source processing with one worker unless an
    operator explicitly raises the env var;
  - both durable and legacy update paths now use the clamp;
  - durable `run_source_run` now clears the candidate batch and calls
    `gc.collect()` in a `finally` block after every source run.
- Added focused unit test for the worker clamp.
- Verification: `compileall web_app/jobs.py` passed; focused pytest passed for
  the worker clamp, WAL fallback, and `/healthz` schema.
- Next action: deploy this patch, verify job `0b36e332911a` remains
  `interrupted_resumable`, then resume manually and monitor memory closely.

## 2026-06-02 18:58 America/Sao_Paulo - Manual Resume After Memory Patch

- Memory-safety deploy `299a154` became live at `2026-06-02T21:54:06Z`.
- Verified job `0b36e332911a` before resume:
  - status `interrupted_resumable`;
  - `resumeAvailable=true`;
  - totals preserved at `articles=112`, `mentions=212`, `stories=212`;
  - target/date contract unchanged.
- Playwright UI check:
  - debug load showed `Retomar atualização` visible with no console errors;
  - two click attempts with API-authenticated Playwright context still observed
    the button hidden despite backend `resumeAvailable=true`;
  - treated this as a timing/auth-context UI flake, not a backend blocker, and
    used the same `/api/update/resume` endpoint directly to avoid delaying the
    production recovery.
- Resume API response HTTP 200 for job `0b36e332911a`.
- Post-resume status: `running`; coverage reset to `pending`; totals preserved
  at `articles=112`, `mentions=212`, `stories=212`.
- Memory after resume: `VmRSS=362.11 MiB`, `VmHWM=453.39 MiB`.
- Next action: continue monitoring with the worker clamp active; watch for
  repeat disk I/O, memory pressure, source failures, or final
  `failed_needs_fix` state.

## 2026-06-02 19:00 America/Sao_Paulo - Post-Resume Monitoring Snapshot 1

- Job `0b36e332911a` is `running`; all monitored endpoints HTTP 200.
- Coverage state is `failed_needs_fix` because O Globo RSS failed again after
  resume with the same XML parse error.
- Source-run counts: `complete=19`, `failed_needs_fix=1`, `running=1`,
  `pending=22891`.
- Current source: `seguranca_presente` / WordPress API / `Diario do Rio`.
- Latest WordPress checkpoint: 25 candidates, 0 new articles, 4 mentions, 4
  stories.
- Totals in status: `articles=112`, `mentions=316`, `stories=316`.
- Memory with worker clamp active: current `VmRSS=274.99 MiB`; high-water
  `VmHWM=523.14 MiB`.
- Disk: free `66139.0 MiB`; DB `161.8 MiB`; WAL `0.2 MiB`; SHM `0.03 MiB`.
- Decision: continue running. O Globo RSS is repeat-failing and should be
  treated as a source fix/retry item later, not a reason to stop the whole
  running job while other sources progress.

## 2026-06-02 19:02 America/Sao_Paulo - O Globo RSS Disabled Before Next Resume

- Durable source ledger can reconcile disabled sources by marking source keys no
  longer present in active config as complete.
- O Globo RSS (`rss:8`) failed twice in production with
  `not well-formed (invalid token): line 1, column 0`.
- Local fetch of `https://oglobo.globo.com/rss.xml` returned valid but empty XML,
  and O Globo remains covered by O Globo Sitemap plus internal search sources.
- Patched `pipeline/settings.py` to set O Globo RSS `disabled=true` with an
  inline reason.
- Verification: `compileall pipeline/settings.py web_app/jobs.py` passed;
  focused pytest passed for worker clamp, WAL fallback, and `/healthz` schema.
- Next action: deploy this source-config fix, accept the controlled interruption,
  verify job `0b36e332911a` returns to `interrupted_resumable`, then resume
  again. The resumed run should reconcile `rss:8` instead of repeating the O
  Globo RSS failure for every target.

## 2026-06-02 19:07 America/Sao_Paulo - Resume After O Globo RSS Disable

- Source-config deploy `c0d330e` became live at `2026-06-02T22:05:42Z`.
- Before resume, job `0b36e332911a` was `interrupted_resumable`,
  `resumeAvailable=true`, with totals `articles=132`, `mentions=336`,
  `stories=336`.
- Source counts before resume: `complete=19`, `failed_needs_fix=1`,
  `interrupted_resumable=22892`.
- Memory before resume after deploy: `VmRSS=136.73 MiB`, `VmHWM=461.26 MiB`.
- Resume API response HTTP 200; job returned to `queued` then `running`.
- Post-resume status: `running`, `coverageState=pending`, totals preserved at
  `articles=132`, `mentions=336`, `stories=336`.
- Memory after resume: `VmRSS=161.89 MiB`, `VmHWM=461.26 MiB`.
- Next action: monitor whether `rss:8` is reconciled out and whether the job
  continues through WordPress sources without repeat disk I/O.

## 2026-06-02 19:13 America/Sao_Paulo - Post-O Globo Resume Monitoring Snapshot 1

- Job `0b36e332911a` is `running`; all monitored endpoints HTTP 200.
- O Globo RSS disable was reconciled by the durable ledger: source-run counts
  are now `complete=20`, `running=1`, `pending=22891`, with no
  `failed_needs_fix` source count.
- Coverage state is `running`; `resumeAvailable=false`.
- Current progress is still on `seguranca_presente` / `Diario do Rio`, date
  window `2014-01-01` through `2026-06-02`.
- Current status totals: `articles=17`, `mentions=19`, `stories=19`; progress
  event totals: `articles=21`, `mentions=23`, `stories=23`; live results
  endpoint returned 53 items.
- Memory: `VmRSS=189.96 MiB`, `VmHWM=489.93 MiB`, `VmSize=436.61 MiB`,
  `VmData=226.11 MiB`.
- Disk: free `55168.08 MiB`; DB `166.17 MiB`, WAL `0.17 MiB`, SHM `0.03 MiB`.
- Monitor note: an apparent `target_keys` count of 316 was caused by treating
  the current job row's JSON text field as a list. Parsed progress and the
  source ledger still point to the requested job contract; no duplicate job was
  started and no scope change was made.
- Next action: continue monitoring for stalls, memory pressure, disk I/O, and
  source-specific failures.

## 2026-06-02 19:16 America/Sao_Paulo - Three-Cycle Watch

- Cycle 1: job `0b36e332911a` `running`, coverage `running`, source counts
  `complete=20`, `running=1`, `pending=22891`; totals `articles=158`,
  `mentions=390`, `stories=390`; live results 53; memory
  `VmRSS=195.18 MiB`, `VmHWM=489.93 MiB`; DB `167.17 MiB`, WAL `0.42 MiB`.
- Cycle 2: job still `running`; totals moved to `articles=167`,
  `mentions=399`, `stories=399`; live results 56; memory `VmRSS=198.5 MiB`,
  `VmHWM=489.93 MiB`; WAL grew to `2.46 MiB`.
- Cycle 3: job still `running`; totals moved to `articles=170`,
  `mentions=402`, `stories=402`; live results 56; memory sample
  `VmRSS=371.57 MiB`, `VmHWM=489.93 MiB`; DB `168.51 MiB`, WAL `0.58 MiB`.
- Immediate memory recheck after the cycle-3 spike dropped to
  `VmRSS=208.93 MiB`, `VmHWM=489.93 MiB`, so the spike appears transient.
- Current target/source remains `seguranca_presente` / `Diario do Rio`; no
  source failure, no 5xx endpoint failure, no disk I/O error, and no duplicate
  job was started.
- Next action: continue monitoring; treat repeated sustained RSS above roughly
  430 MiB, new `failed_needs_fix`, or any SQLite/disk barrier as a stop-and-fix
  condition.

## 2026-06-02 19:23 America/Sao_Paulo - Playwright Viewer Runner Bug

- Production Playwright read-only verification confirmed the profile contract:
  login page lists `Voluntários-Lab-Políticas-Públicas`; viewer login works;
  `/api/targets` returns exactly the 18 requested keys; all are
  `primary=true`, `className=primary`, and not archived; dashboard defaults are
  exactly the same 18 keys; filter chips are all active/primary; runner primary
  grid has exactly the 18 requested keys checked; runner secondary grid has
  zero keys.
- Playwright found a real viewer-facing runner bug: for the viewer profile,
  `runnerStatusPill` stayed `Consultando...` and `runUpdateButton` remained
  enabled while job `0b36e332911a` was actively running.
- Admin UI did not have the bug: admin status pill showed `Atualizando` and
  the run button was disabled; the requested 18 keys were present in the admin
  primary runner grid.
- Root cause in dashboard JS: `pollStatus()` only ran for `viewerIsAdmin()`,
  but authenticated passworded viewers have runner controls too.
- Prepared a minimal hotfix in `assets/clipping.js` and
  `tools/pages_assets/clipping.js`: add a runner-control predicate and poll
  status for admin/simulation/authenticated viewer sessions, excluding demo.
- Next action: deploy the minimal UI hotfix, accept the controlled production
  interruption, verify job `0b36e332911a` becomes resumable, then resume that
  same job without starting a duplicate.

## 2026-06-02 19:29 America/Sao_Paulo - UI Hotfix Deploy, Resume, and Verification

- Committed and pushed `632f499` (`fix(ui): poll status for viewer runner
  sessions`), staging only the runner-status polling hotfix plus this task log;
  unrelated dirty worktree changes were not staged.
- Render deploy `dep-d8flg7rrjlhs73anb8h0` for `632f499` became live at
  `2026-06-02T22:26:38Z`.
- Post-deploy job state: job `0b36e332911a` became
  `interrupted_resumable`, `resumeAvailable=true`; source counts
  `complete=20`, `interrupted_resumable=22892`; totals preserved at
  `articles=203`, `mentions=436`, `stories=436`.
- Resume API response HTTP 200 for the same job id; post-resume state became
  `running`, coverage `pending`, with source counts `complete=20`,
  `pending=22892` and totals still `203/436/436`.
- Post-fix Playwright verification passed for the viewer profile:
  - login page lists `Voluntários-Lab-Políticas-Públicas`;
  - viewer login works as `voluntarios_lab_politicas`;
  - `/api/targets`, dashboard targets, dashboard defaults, filter chips, and
    runner primary grid all match exactly the 18 requested keys;
  - all targets are primary/default active; runner secondary grid has zero
    keys;
  - viewer runner now shows `Atualizando`, `runUpdateButton.disabled=true`,
    and the active-job message;
  - no console errors or page errors.
- Monitoring after resume: all endpoints HTTP 200; job `running`, coverage
  `running`; source counts `complete=20`, `running=1`, `pending=22891`;
  current target/source `seguranca_presente` / `Diario do Rio`; totals
  `articles=206`, `mentions=544`, `stories=544`; live results 50.
- Memory after resume: current `VmRSS=233.41 MiB`, but `VmHWM=502.62 MiB`;
  this high-water value is close to the Render free limit and remains a watch
  item even though current RSS dropped.
- Disk after resume: free `54708.7 MiB`; DB `173.27 MiB`, WAL `0.02 MiB`, SHM
  `0.03 MiB`.
- Next action: continue monitoring memory and source progress; stop and fix if
  RSS stays high or the service restarts/returns to `interrupted_resumable`.

## 2026-06-02 19:32 America/Sao_Paulo - Post-Hotfix Memory Watch

- Cycle 1 after hotfix resume: job `0b36e332911a` `running`, coverage
  `pending`, source counts `complete=20`, `pending=22892`; status totals
  temporarily showed `articles=6`, `mentions=13`, `stories=13` while the
  resumed source-run accounting settled; memory was high at
  `VmRSS=406.57 MiB`, `VmHWM=503.21 MiB`.
- Cycle 2: job `running`, coverage `running`, source counts `complete=20`,
  `running=1`, `pending=22891`; totals moved to `articles=217`,
  `mentions=555`, `stories=555`; live results 51.
- Cycle 2 memory dropped back to `VmRSS=234.2 MiB`; high-water increased to
  `VmHWM=507.5 MiB`.
- Current target/source remains `seguranca_presente` / `Diario do Rio`; latest
  source events show checkpoints/starts without errors.
- Disk remains usable: free `51445.22 MiB`; DB `173.52 MiB`, WAL `1.87 MiB`,
  SHM `0.03 MiB`.
- Decision: continue the job because current RSS recovered and the source
  ledger is progressing, but keep memory as a high-risk watch item. A sustained
  high RSS climb or another restart becomes a recovery/fix barrier.

## 2026-06-02 19:34 America/Sao_Paulo - Memory Danger-Line Recheck

- One-minute follow-up sample: all monitored endpoints HTTP 200; job
  `0b36e332911a` `running`, coverage `pending`; source counts
  `complete=20`, `pending=22892`; current target/source
  `seguranca_presente` / `Diario do Rio`.
- The sample hit the memory danger line: `VmRSS=430.77 MiB`,
  `VmHWM=510.89 MiB`. Latest source event still reported RSS around
  `215.5 MiB`, suggesting a transient allocation.
- Immediate recheck: job still `running`, coverage `running`; source counts
  `complete=20`, `running=1`, `pending=22891`; totals advanced to
  `articles=228`, `mentions=566`, `stories=566`.
- Immediate recheck memory dropped to `VmRSS=222.37 MiB`; `VmHWM` remains
  `510.89 MiB`.
- Decision: no duplicate job and no new deploy/fix right now. Continue
  monitoring. Treat a sustained current RSS near/above `430 MiB`, an OOM
  restart, or `interrupted_resumable` as the next recovery barrier.

## 2026-06-02 19:39 America/Sao_Paulo - Contract Check After User Question

- Re-read `LONG_TERM_GOALS.md`: required production job is one custom/all run
  for all 18 keys, `date_from=2014-01-01`, `date_to=2026-06-02`.
- Live production status confirms job `0b36e332911a` is configured with
  `preset=custom`, `collector=all`, `target_keys_count=18`,
  `date_from=2014-01-01`, `date_to=2026-06-02`.
- The job has not completed the full backfill. It is still `running`, coverage
  `running`, with source counts `complete=20`, `running=1`, `pending=22891`
  out of `sourceRunCount=22912`.
- Current target/source remains `seguranca_presente` / `Diario do Rio`.
- Current totals: `articles=243`, `mentions=581`, `stories=581`.
- Answer to user: the job was correctly launched from 2014, but the complete
  all-target/all-source 2014-2026 backfill is not done yet.

## 2026-06-02 19:44 America/Sao_Paulo - Live Website Publish Monitoring

- User correctly flagged that monitoring must include continuous live website
  updates, not only job status.
- Verified the code path: after source runs save articles,
  `publish_incremental_snapshot()` should export the dashboard and upload
  artifacts; `upload_live_checkpoint()` separately uploads DB checkpoints for
  live results.
- Cycle 1:
  - all checked endpoints HTTP 200;
  - job `0b36e332911a` `running`, coverage `running`;
  - totals `articles=251`, `mentions=589`, `stories=589`;
  - `publishedAt=2026-06-02T22:41:01.192002+00:00`;
  - `incremental_publish_complete` uploaded 7 artifacts including
    `assets/clipping-data.json` and `assets/clipping-raw-texts.json`;
  - dashboard asset `generatedAt=02/06/2026 22:40 UTC`;
  - live-results latest saved item `2026-06-02T22:41:52.614378+00:00`;
  - memory `VmRSS=219.64 MiB`, `VmHWM=510.89 MiB`.
- Cycle 2:
  - job still `running`, coverage `running`;
  - totals advanced to `articles=256`, `mentions=594`, `stories=594`;
  - `publishedAt=2026-06-02T22:42:38.783391+00:00`;
  - another `incremental_publish_complete` uploaded 7 artifacts;
  - dashboard asset `generatedAt=02/06/2026 22:42 UTC`;
  - live-results latest saved item `2026-06-02T22:42:53.800377+00:00`;
  - memory `VmRSS=234.78 MiB`, `VmHWM=517.82 MiB`.
- Cycle 3:
  - job still `running`, coverage `running`;
  - totals advanced to `articles=262`, `mentions=600`, `stories=600`;
  - live-results latest saved item advanced to
    `2026-06-02T22:43:46.942848+00:00`;
  - `live_checkpoint_uploaded` occurred at `2026-06-02T22:43:21.865010+00:00`;
  - no new `incremental_publish_complete` appeared in this sample, likely
    within the 90-second incremental publish throttle;
  - memory `VmRSS=242.03 MiB`, `VmHWM=526.95 MiB`.
- Decision: live-results and artifact publishing are moving, but continue
  monitoring the next publish window and memory high-water. Current RSS remains
  acceptable; high-water remains risky.

## 2026-06-02 19:47 America/Sao_Paulo - Publish Window Confirmation

- Waited through an additional incremental publish window after the prior
  live-update sample.
- Job `0b36e332911a` remained `running`, coverage `running`; source counts
  `complete=20`, `running=1`, `pending=22891`.
- Totals advanced to `articles=272`, `mentions=610`, `stories=610`.
- Incremental dashboard publish succeeded again:
  - `publishedAt=2026-06-02T22:46:02.224579+00:00`;
  - `export_complete` at `2026-06-02T22:45:46.424733+00:00`;
  - `incremental_publish_complete` uploaded 7 artifacts, including
    `assets/clipping-data.json`, `assets/clipping-raw-texts.json`, and the
    compressed DB.
- Dashboard asset moved to `generatedAt=02/06/2026 22:45 UTC`,
  `totalStories=883`, `totalArticles=1118`.
- Live results remained fresh: latest saved item
  `2026-06-02T22:46:56.839988+00:00`; base live-results states
  `published=57`, `saved=3`.
- Live DB checkpoints uploaded at `22:45:36Z`, `22:46:12Z`, and `22:46:46Z`.
- Memory current `VmRSS=233.94 MiB`; high-water remains risky at
  `VmHWM=526.95 MiB`.
- Decision: live website update requirement is currently being met. Continue
  monitoring because the backfill is far from complete and memory high-water is
  above the nominal Render free limit.

## 2026-06-02 19:51 America/Sao_Paulo - Active Loop After User Warning

- Ran another active monitoring loop after confirming live-publish behavior.
- Cycle 1:
  - job `0b36e332911a` `running`, coverage `running`;
  - totals `articles=276`, `mentions=614`, `stories=614`;
  - live-results latest saved item advanced to
    `2026-06-02T22:47:48.441086+00:00`;
  - asset remained at `generatedAt=02/06/2026 22:45 UTC`;
  - memory `VmRSS=235.89 MiB`, `VmHWM=526.95 MiB`.
- Cycle 2:
  - totals advanced to `articles=280`, `mentions=618`, `stories=618`;
  - `publishedAt` advanced to `2026-06-02T22:48:36.156558+00:00`;
  - dashboard asset advanced to `generatedAt=02/06/2026 22:48 UTC`,
    `totalStories=888`, `totalArticles=1125`;
  - live-results latest saved item advanced to
    `2026-06-02T22:49:14.909377+00:00`;
  - memory sample hit danger line at `VmRSS=453.23 MiB`.
- Immediate memory recheck after cycle 2:
  - job still `running`, coverage `running`;
  - totals advanced to `articles=282`, `mentions=620`, `stories=620`;
  - current memory recovered to `VmRSS=236.87 MiB`.
- Cycle 3:
  - totals advanced to `articles=283`, `mentions=621`, `stories=621`;
  - live-results latest saved item advanced to
    `2026-06-02T22:50:22.672983+00:00`;
  - memory sample again hit danger line at `VmRSS=433.02 MiB`.
- Immediate memory recheck after cycle 3:
  - job still `running`, coverage `running`;
  - totals advanced to `articles=285`, `mentions=623`, `stories=623`;
  - current memory recovered to `VmRSS=240.13 MiB`;
  - high-water increased to `VmHWM=530.04 MiB`.
- Decision: live website update behavior is being met during this window
  (`publishedAt`, asset `generatedAt`, and live-results all moved). Memory
  spikes remain the main operational risk and must be checked immediately when
  sampled above the danger threshold.

## 2026-06-02 20:55 America/Sao_Paulo - Current Status Check

- All monitored endpoints HTTP 200: status, memory, disk, source-run events,
  base live-results, and dashboard asset.
- Job `0b36e332911a` is still `running`, coverage `running`,
  `resumeAvailable=false`.
- Contract still intact: `date_from=2014-01-01`, `date_to=2026-06-02`.
- Source ledger unchanged in shape: `complete=20`, `running=1`,
  `pending=22891` out of `sourceRunCount=22912`.
- Current target/source remains `seguranca_presente` / `Diario do Rio`.
- Totals advanced to `articles=531`, `mentions=869`, `stories=869`.
- Live website update path is currently working:
  - `publishedAt=2026-06-02T23:54:51.269540+00:00`;
  - dashboard asset `generatedAt=02/06/2026 23:54 UTC`;
  - asset totals `totalStories=1060`, `totalArticles=1378`;
  - base live-results latest saved item
    `2026-06-02T23:55:21.995378+00:00`;
  - live-results states among latest 60: `published=58`, `saved=2`.
- Memory current is acceptable at `VmRSS=248.25 MiB`; high-water is very risky
  at `VmHWM=585.19 MiB`.
- Disk remains usable: free `66664.33 MiB`; DB `212.74 MiB`, WAL `0.58 MiB`,
  SHM `0.03 MiB`.
- Decision: continue monitoring. No duplicate job and no fix action right now
  because current RSS is low, endpoints are healthy, live publishing is fresh,
  and source events continue; memory high-water remains the main risk.

## 2026-06-03 13:42 America/Sao_Paulo - Restarted Check, Found Source Barrier

- Restarted monitoring after the prior check stopped.
- Production comparison against the long-term plan:
  - viewer website still matches the profile contract via Playwright;
  - login page lists `Voluntários-Lab-Políticas-Públicas`;
  - viewer login works as `voluntarios_lab_politicas`;
  - `/api/targets`, dashboard targets, dashboard defaults, chips, and runner
    primary grid all match exactly the 18 requested keys;
  - all are primary/default-active; runner secondary grid has zero keys;
  - runner shows `Atualizando` and blocks duplicate start;
  - no browser console or page errors.
- Viewer-scoped dashboard asset at check time:
  - `generatedAt=03/06/2026 04:51 UTC`;
  - `totalStories=929`, `totalArticles=1550`;
  - latest viewer live result `2026-06-03T04:50:45.673824+00:00`.
- Admin production status changed materially since the last log:
  - job `0b36e332911a` still `running`;
  - contract still intact: `date_from=2014-01-01`, `date_to=2026-06-02`;
  - coverage now `failed_needs_fix`;
  - source counts `complete=2705`, `failed_needs_fix=1`, `pending=20206`;
  - totals `articles=1173`, `mentions=1180`, `stories=1180`;
  - current source moved to `seguranca_presente` / `O Globo Sitemap`;
  - dashboard publish is fresh at `publishedAt=2026-06-03T04:51:20.805007+00:00`;
  - admin asset `generatedAt=03/06/2026 04:51 UTC`,
    `totalStories=1490`, `totalArticles=2225`.
- Failed source inspected:
  - target `seguranca_presente`;
  - source `Agenda do Poder`;
  - source key `wordpress_api_v2:2:0`;
  - cursor page 25, page size 25;
  - accumulated `600` candidates and `131` saved articles/mentions/stories;
  - error `fetch_url hard timeout (35s)` on the WordPress API page-25 URL;
  - last failed at `2026-06-03T01:14:08.135194+00:00`.
- Memory is an active barrier:
  - first recheck `VmRSS=669.88 MiB`, `VmHWM=828.84 MiB`;
  - follow-up `VmRSS=659.21 MiB`, `VmHWM=850.37 MiB`.
- Prepared production hotfix:
  - late WordPress hard timeouts after multiple successful pages are treated
    as end-of-pagination instead of a fatal source failure;
  - first/early WordPress timeouts still fail normally;
  - focused tests passed:
    `test_late_wordpress_hard_timeout_completes_source_run`,
    `test_early_wordpress_hard_timeout_still_fails_source_run`, and
    `test_durable_wordpress_source_runs_use_small_api_pages`;
  - `compileall web_app/jobs.py` passed.
- Next action: deploy the focused hotfix, accept controlled interruption,
  verify job `0b36e332911a` becomes resumable, resume that same job, then
  confirm the failed source is requeued and can complete without starting a
  duplicate full job.

## 2026-06-04 20:27:03 -03 - Production Recovery Baseline

- Job `0b36e332911a` status `interrupted_resumable`, coverage `interrupted_resumable`, resumeAvailable `True`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "interrupted_resumable": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `805`, stories `301`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `03/06/2026 19:41 UTC`, stories `1485`, articles `2007`, targets `27`.
- Live results: latest `2026-06-03T16:51:31.525271+00:00`, count `51`.
- Viewer profile/login: login ok `False`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `154.02` MiB, VmHWM `682.22` MiB, limit `512` MiB.
- Disk: free `71900.06` MiB, DB `254.16` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.31, "status": 200}, "disk": {"elapsed": 0.41, "status": 200}, "events": {"elapsed": 0.41, "status": 200}, "health": {"elapsed": 0.86, "status": 200}, "live": {"elapsed": 0.64, "status": 200}, "memory": {"elapsed": 0.61, "status": 200}, "sqlite": {"elapsed": 8.19, "status": 200}, "status": {"elapsed": 1.24, "status": 200}, "targets": {"elapsed": 0.24, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "error": ""}, {"at": "2026-06-03T01:36:25.606763+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "pending", "error": ""}]`.
- Barriers: `["job_status:interrupted_resumable", "coverage:interrupted_resumable", "viewer_login_failed"]`.

## 2026-06-04 20:27:45 -03 - Password Repair Applied

- Job `0b36e332911a` status `interrupted_resumable`, coverage `interrupted_resumable`, resumeAvailable `True`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "interrupted_resumable": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `805`, stories `301`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `03/06/2026 19:41 UTC`, stories `1485`, articles `2007`, targets `27`.
- Live results: latest `2026-06-03T16:51:31.525271+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `160.52` MiB, VmHWM `682.22` MiB, limit `512` MiB.
- Disk: free `71906.5` MiB, DB `254.16` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.11, "status": 200}, "disk": {"elapsed": 0.24, "status": 200}, "events": {"elapsed": 0.24, "status": 200}, "health": {"elapsed": 0.96, "status": 200}, "live": {"elapsed": 0.32, "status": 200}, "memory": {"elapsed": 0.23, "status": 200}, "sqlite": {"elapsed": 0.59, "status": 200}, "status": {"elapsed": 0.84, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "error": ""}, {"at": "2026-06-03T01:36:25.606763+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "pending", "error": ""}]`.
- Barriers: `["job_status:interrupted_resumable", "coverage:interrupted_resumable"]`.

## 2026-06-04 20:31 America/Sao_Paulo - Checkpoint Recovery Decision

- Implemented and ran the dedicated operator loop at
  `tools/voluntarios_backfill_operator.py`.
- Focused operator tests passed: `6 passed`.
- Production credential drift was repaired through the admin viewer API:
  saved viewer password now logs in as `voluntarios_lab_politicas`; plaintext
  was updated only in `/home/otavio/Documents/clipping-project senhas.md`.
- Playwright UI verification passed after the repair:
  - login page lists `Voluntários-Lab-Políticas-Públicas`;
  - UI login returns HTTP 200;
  - `/api/targets` under the viewer returns HTTP 200;
  - runner primary keys and checked primary keys are exactly the 18 requested
    target keys;
  - runner secondary keys are empty;
  - no browser console/page errors were observed.
- Storage/checkpoint comparison:
  - production health reports storage enabled with prefix `clipping-project`;
  - current production SQLite `quickCheck` is `ok`;
  - current DB is `254.16 MiB` with source ledger
    `{"complete": 23, "interrupted_resumable": 22889}`;
  - local Supabase service-key env is unavailable to the operator script, so
    direct storage object metadata cannot be listed locally;
  - Render MCP log access is installed but has no workspace selected in this
    session, so logs cannot be queried without user-side workspace selection.
- Decision: no verified newer valid checkpoint is accessible through the
  current safe operator surface. The recovery floor is therefore the current
  production ledger: job `0b36e332911a`, `complete=23`,
  `interrupted_resumable=22889`. Resume this same job only; do not start a
  duplicate full job.

## 2026-06-04 20:36 America/Sao_Paulo - Monitor False-Positive Corrected

- Resumed job `0b36e332911a` successfully through `/api/update/resume`.
- Post-resume status: `running`, coverage `pending/running`,
  source ledger moved to `{"complete": 23, "pending": 22888, "running": 1}`.
- The active source is `seguranca_presente` / `Agenda do Poder`; events show
  fresh `source_run_started` and checkpoint events at `2026-06-04T23:32Z`,
  `23:33Z`, and `23:34Z`.
- Live website updates resumed:
  - live-results latest timestamp advanced to `2026-06-04T23:35:53Z`;
  - `publishedAt` advanced to `2026-06-04T23:34:15Z`;
  - asset `generatedAt` advanced to `04/06/2026 23:34 UTC`.
- The first monitor implementation incorrectly flagged
  `source_stall_cycles:3` because the same source-run stayed active for
  multiple cycles. That is not a real stall when articles, live-results,
  events, or publish timestamps are moving.
- Operator script was patched so stall detection now includes article,
  mention, story, publish, and live-results movement, not only source-run
  counts/current source.

## 2026-06-04 20:37 America/Sao_Paulo - Memory Spike Recheck

- Corrected monitor immediately found a real risk sample:
  `VmRSS=563.04 MiB`, above the nominal `512 MiB` Render limit.
- The sample still showed active work:
  - fresh Agenda do Poder checkpoint at `2026-06-04T23:36:19Z`;
  - live-results latest `2026-06-04T23:36:06Z`;
  - `publishedAt=2026-06-04T23:36:21Z`;
  - asset `generatedAt=04/06/2026 23:36 UTC`.
- Immediate follow-up audit showed memory recovered to `VmRSS=262.98 MiB`;
  SQLite remained `quickCheck=ok`; job stayed `running`; no barrier remained.
- Decision: treat the high-RSS sample as a transient memory spike, not a
  restart/fix barrier. Operator script was patched so monitor records first
  high-RSS sample as a warning and stops only when high RSS is sustained across
  consecutive cycles.

## 2026-06-04 20:29:33 -03 - Playwright UI Contract Check

- Job `None` status `None`, coverage `n/a`, resumeAvailable `None`.
- Contract: date `None` to `None`, collector `None`, preset `None`, exact 18 keys `None`.
- Source ledger: total `None`, counts `{}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `None`, stories `None`, publishedAt `None`.
- Website asset: generatedAt `None`, stories `None`, articles `None`, targets `None`.
- Live results: latest `None`, count `None`.
- Viewer profile/login: login ok `None`, profile `None`.
- Target contract: `None`.
- Memory: VmRSS `None` MiB, VmHWM `None` MiB, limit `None` MiB.
- Disk: free `None` MiB, DB `None` MiB.
- Storage diagnostic: enabled `None`, reason ``.
- HTTP timings/status: `{}`.
- Recent source events: `[]`.
- Barriers: `["ui_primaryExact_failed", "ui_checkedPrimaryExact_failed", "ui_targets_http:401", "ui_target_contract_failed", "ui_console_or_page_errors"]`.

## 2026-06-04 20:30:38 -03 - Playwright UI Contract Check

- Job `None` status `None`, coverage `n/a`, resumeAvailable `None`.
- Contract: date `None` to `None`, collector `None`, preset `None`, exact 18 keys `None`.
- Source ledger: total `None`, counts `{}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `None`, stories `None`, publishedAt `None`.
- Website asset: generatedAt `None`, stories `None`, articles `None`, targets `None`.
- Live results: latest `None`, count `None`.
- Viewer profile/login: login ok `None`, profile `None`.
- Target contract: `None`.
- Memory: VmRSS `None` MiB, VmHWM `None` MiB, limit `None` MiB.
- Disk: free `None` MiB, DB `None` MiB.
- Storage diagnostic: enabled `None`, reason ``.
- HTTP timings/status: `{}`.
- Recent source events: `[]`.
- Barriers: `[]`.

## 2026-06-04 20:31:53 -03 - Resumed Same Production Job

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `805`, stories `301`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `03/06/2026 19:41 UTC`, stories `1485`, articles `2007`, targets `27`.
- Live results: latest `2026-06-03T16:51:31.525271+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `218.2` MiB, VmHWM `721.84` MiB, limit `512` MiB.
- Disk: free `71627.46` MiB, DB `254.18` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.78, "status": 200}, "disk": {"elapsed": 0.27, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 2.17, "status": 200}, "live": {"elapsed": 0.31, "status": 200}, "memory": {"elapsed": 0.22, "status": 200}, "sqlite": {"elapsed": 0.86, "status": 200}, "status": {"elapsed": 1.25, "status": 200}, "targets": {"elapsed": 0.27, "status": 200}, "viewers": {"elapsed": 0.27, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "error": ""}, {"at": "2026-06-03T01:36:25.606763+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "pending", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:32:25 -03 - Monitor Cycle 1

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22888, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `805`, stories `301`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `03/06/2026 19:41 UTC`, stories `1485`, articles `2007`, targets `27`.
- Live results: latest `2026-06-03T16:51:31.525271+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `215.3` MiB, VmHWM `721.84` MiB, limit `512` MiB.
- Disk: free `71634.51` MiB, DB `254.18` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.11, "status": 200}, "disk": {"elapsed": 0.25, "status": 200}, "events": {"elapsed": 0.24, "status": 200}, "health": {"elapsed": 0.97, "status": 200}, "live": {"elapsed": 0.42, "status": 200}, "memory": {"elapsed": 0.24, "status": 200}, "sqlite": {"elapsed": 0.59, "status": 200}, "status": {"elapsed": 1.04, "status": 200}, "targets": {"elapsed": 0.26, "status": 200}, "viewers": {"elapsed": 0.24, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:32:16.043928+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:33:35 -03 - Monitor Cycle 2

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22888, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `865`, mentions `1303`, stories `1303`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `03/06/2026 19:41 UTC`, stories `1485`, articles `2007`, targets `27`.
- Live results: latest `2026-06-04T23:33:34.038244+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `243.51` MiB, VmHWM `721.84` MiB, limit `512` MiB.
- Disk: free `71628.75` MiB, DB `254.18` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.93, "status": 200}, "disk": {"elapsed": 0.28, "status": 200}, "events": {"elapsed": 0.24, "status": 200}, "health": {"elapsed": 1.82, "status": 200}, "live": {"elapsed": 0.33, "status": 200}, "memory": {"elapsed": 0.24, "status": 200}, "sqlite": {"elapsed": 0.91, "status": 200}, "status": {"elapsed": 0.91, "status": 200}, "targets": {"elapsed": 0.24, "status": 200}, "viewers": {"elapsed": 0.22, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:32:16.043928+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:34:44 -03 - Monitor Cycle 3

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22888, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `7`, mentions `7`, stories `7`, publishedAt `2026-06-04T23:34:15.391707+00:00`.
- Website asset: generatedAt `04/06/2026 23:34 UTC`, stories `1485`, articles `1957`, targets `27`.
- Live results: latest `2026-06-04T23:33:59.015776+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `243.52` MiB, VmHWM `721.84` MiB, limit `512` MiB.
- Disk: free `71642.63` MiB, DB `254.71` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.71, "status": 200}, "disk": {"elapsed": 0.25, "status": 200}, "events": {"elapsed": 0.25, "status": 200}, "health": {"elapsed": 0.96, "status": 200}, "live": {"elapsed": 0.33, "status": 200}, "memory": {"elapsed": 0.23, "status": 200}, "sqlite": {"elapsed": 0.67, "status": 200}, "status": {"elapsed": 0.82, "status": 200}, "targets": {"elapsed": 0.25, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:34:27.390700+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:33:59.096683+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:32:16.043928+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:35:56 -03 - Monitor Cycle 4

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22888, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `873`, mentions `1311`, stories `1311`, publishedAt `2026-06-04T23:34:15.391707+00:00`.
- Website asset: generatedAt `04/06/2026 23:34 UTC`, stories `1485`, articles `1957`, targets `27`.
- Live results: latest `2026-06-04T23:35:53.743800+00:00`, count `57`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `248.74` MiB, VmHWM `721.84` MiB, limit `512` MiB.
- Disk: free `71634.73` MiB, DB `254.71` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.94, "status": 200}, "disk": {"elapsed": 0.61, "status": 200}, "events": {"elapsed": 0.35, "status": 200}, "health": {"elapsed": 1.36, "status": 200}, "live": {"elapsed": 0.44, "status": 200}, "memory": {"elapsed": 0.31, "status": 200}, "sqlite": {"elapsed": 0.82, "status": 200}, "status": {"elapsed": 1.33, "status": 200}, "targets": {"elapsed": 0.26, "status": 200}, "viewers": {"elapsed": 0.26, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:34:27.390700+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:33:59.096683+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:32:16.043928+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}]`.
- Barriers: `["source_stall_cycles:3"]`.

## 2026-06-04 20:36:39 -03 - Monitor Cycle 1

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `16`, mentions `16`, stories `16`, publishedAt `2026-06-04T23:36:21.272789+00:00`.
- Website asset: generatedAt `04/06/2026 23:36 UTC`, stories `1485`, articles `1961`, targets `27`.
- Live results: latest `2026-06-04T23:36:06.557537+00:00`, count `57`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `563.04` MiB, VmHWM `721.84` MiB, limit `512` MiB.
- Disk: free `71641.68` MiB, DB `255.82` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.73, "status": 200}, "disk": {"elapsed": 0.43, "status": 200}, "events": {"elapsed": 0.24, "status": 200}, "health": {"elapsed": 2.05, "status": 200}, "live": {"elapsed": 0.43, "status": 200}, "memory": {"elapsed": 0.57, "status": 200}, "sqlite": {"elapsed": 1.54, "status": 200}, "status": {"elapsed": 1.66, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:36:19.672268+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:34:27.390700+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:33:59.096683+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:32:16.043928+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}]`.
- Barriers: `["memory_rss_danger:563.04"]`.

## 2026-06-04 20:36:57 -03 - Production Recovery Baseline

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22888, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `16`, mentions `16`, stories `16`, publishedAt `2026-06-04T23:36:38.579555+00:00`.
- Website asset: generatedAt `04/06/2026 23:36 UTC`, stories `1485`, articles `1961`, targets `27`.
- Live results: latest `2026-06-04T23:36:06.557537+00:00`, count `57`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `262.98` MiB, VmHWM `721.84` MiB, limit `512` MiB.
- Disk: free `71639.54` MiB, DB `255.82` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.1, "status": 200}, "disk": {"elapsed": 0.25, "status": 200}, "events": {"elapsed": 0.24, "status": 200}, "health": {"elapsed": 1.23, "status": 200}, "live": {"elapsed": 0.3, "status": 200}, "memory": {"elapsed": 0.35, "status": 200}, "sqlite": {"elapsed": 0.56, "status": 200}, "status": {"elapsed": 1.44, "status": 200}, "targets": {"elapsed": 0.24, "status": 200}, "viewers": {"elapsed": 0.26, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:36:52.646575+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:36:19.672268+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:34:27.390700+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:33:59.096683+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:32:16.043928+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:37:36 -03 - Monitor Cycle 1

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22888, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `877`, mentions `1315`, stories `1315`, publishedAt `2026-06-04T23:36:38.579555+00:00`.
- Website asset: generatedAt `04/06/2026 23:36 UTC`, stories `1485`, articles `1961`, targets `27`.
- Live results: latest `2026-06-04T23:36:06.557537+00:00`, count `57`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `262.0` MiB, VmHWM `721.84` MiB, limit `512` MiB.
- Disk: free `71636.5` MiB, DB `255.82` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.02, "status": 200}, "disk": {"elapsed": 0.42, "status": 200}, "events": {"elapsed": 0.22, "status": 200}, "health": {"elapsed": 1.19, "status": 200}, "live": {"elapsed": 0.43, "status": 200}, "memory": {"elapsed": 0.49, "status": 200}, "sqlite": {"elapsed": 0.73, "status": 200}, "status": {"elapsed": 0.98, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:36:52.646575+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:36:19.672268+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:34:27.390700+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:33:59.096683+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:32:16.043928+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:38:53 -03 - Monitor Cycle 2

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `22`, mentions `22`, stories `22`, publishedAt `2026-06-04T23:38:37.804853+00:00`.
- Website asset: generatedAt `04/06/2026 23:38 UTC`, stories `1485`, articles `1964`, targets `27`.
- Live results: latest `2026-06-04T23:38:30.601672+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `523.26` MiB, VmHWM `721.84` MiB, limit `512` MiB.
- Disk: free `71640.55` MiB, DB `256.57` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.22, "status": 200}, "disk": {"elapsed": 0.41, "status": 200}, "events": {"elapsed": 0.25, "status": 200}, "health": {"elapsed": 1.74, "status": 200}, "live": {"elapsed": 0.34, "status": 200}, "memory": {"elapsed": 0.59, "status": 200}, "sqlite": {"elapsed": 1.04, "status": 200}, "status": {"elapsed": 1.98, "status": 200}, "targets": {"elapsed": 0.24, "status": 200}, "viewers": {"elapsed": 0.24, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:38:36.035642+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:36:52.646575+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:36:19.672268+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:34:27.390700+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:33:59.096683+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:32:16.043928+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:40:08 -03 - Monitor Cycle 3

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22888, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `884`, mentions `1322`, stories `1322`, publishedAt `2026-06-04T23:38:56.455415+00:00`.
- Website asset: generatedAt `04/06/2026 23:38 UTC`, stories `1485`, articles `1964`, targets `27`.
- Live results: latest `2026-06-04T23:39:51.509987+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `534.66` MiB, VmHWM `721.84` MiB, limit `512` MiB.
- Disk: free `71634.28` MiB, DB `256.57` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.68, "status": 200}, "disk": {"elapsed": 0.36, "status": 200}, "events": {"elapsed": 0.24, "status": 200}, "health": {"elapsed": 1.99, "status": 200}, "live": {"elapsed": 0.45, "status": 200}, "memory": {"elapsed": 0.24, "status": 200}, "sqlite": {"elapsed": 0.64, "status": 200}, "status": {"elapsed": 1.73, "status": 200}, "targets": {"elapsed": 0.25, "status": 200}, "viewers": {"elapsed": 0.25, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:39:08.007887+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:38:36.035642+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:36:52.646575+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:36:19.672268+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:34:27.390700+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:33:59.096683+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:32:16.043928+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}]`.
- Barriers: `["memory_rss_danger:534.66"]`.

## 2026-06-04 20:42 America/Sao_Paulo - Streaming SQLite Upload Fix Deployed

- Sustained memory barrier identified while the job was actively saving and
  publishing: `VmRSS=523.26 MiB` followed by `VmRSS=534.66 MiB`.
- Inspected code path and found the likely root cause:
  `ArtifactStore.upload_sqlite_snapshot()` materialized a full SQLite snapshot
  in memory and then gzip-compressed that full byte buffer in memory for every
  live checkpoint/current artifact upload.
- Implemented focused fix in `web_app/storage_bridge.py`:
  - create SQLite backup into a temp `.db` file;
  - gzip it into a temp `.db.gz` file via streaming copy;
  - stream the gzip file object to Supabase instead of passing a giant bytes
    payload to `requests.post`;
  - route `.db` backup uploads through the same streaming path.
- Added tests in `tests/test_storage_bridge.py` and kept the operator tests.
- Verification before deploy:
  - `python3 -m py_compile web_app/storage_bridge.py tools/voluntarios_backfill_operator.py`;
  - `pytest tests/test_storage_bridge.py tests/test_voluntarios_backfill_operator.py tests/test_targets_jobs.py::test_sqlite_snapshot_includes_uncheckpointed_wal_rows -q`;
  - result: `10 passed`.
- Committed and pushed `d6e8dc6 fix(storage): stream sqlite checkpoint uploads`
  to `master`. This should trigger a controlled Render deploy, interrupting
  job `0b36e332911a`; next action is to verify interruption/resume state and
  resume the same job only.

## 2026-06-04 20:42:27 -03 - Production Recovery Baseline

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22888, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `890`, mentions `1328`, stories `1328`, publishedAt `2026-06-04T23:41:06.262665+00:00`.
- Website asset: generatedAt `04/06/2026 23:40 UTC`, stories `1485`, articles `1961`, targets `27`.
- Live results: latest `2026-06-04T23:42:23.588775+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `277.28` MiB, VmHWM `721.84` MiB, limit `512` MiB.
- Disk: free `71375.23` MiB, DB `256.95` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.12, "status": 200}, "disk": {"elapsed": 0.25, "status": 200}, "events": {"elapsed": 0.24, "status": 200}, "health": {"elapsed": 1.36, "status": 200}, "live": {"elapsed": 0.44, "status": 200}, "memory": {"elapsed": 0.25, "status": 200}, "sqlite": {"elapsed": 0.61, "status": 200}, "status": {"elapsed": 1.5, "status": 200}, "targets": {"elapsed": 0.26, "status": 200}, "viewers": {"elapsed": 0.24, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:41:18.060561+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:40:48.853261+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:39:08.007887+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:38:36.035642+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:36:52.646575+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:36:19.672268+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:34:27.390700+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:33:59.096683+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:45:35 -03 - Production Recovery Baseline

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `36`, mentions `36`, stories `36`, publishedAt `2026-06-04T23:45:16.258259+00:00`.
- Website asset: generatedAt `04/06/2026 23:44 UTC`, stories `1485`, articles `1968`, targets `27`.
- Live results: latest `2026-06-04T23:44:51.790816+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `273.9` MiB, VmHWM `721.84` MiB, limit `512` MiB.
- Disk: free `68124.34` MiB, DB `258.18` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.1, "status": 200}, "disk": {"elapsed": 0.62, "status": 200}, "events": {"elapsed": 0.24, "status": 200}, "health": {"elapsed": 3.07, "status": 200}, "live": {"elapsed": 0.45, "status": 200}, "memory": {"elapsed": 0.41, "status": 200}, "sqlite": {"elapsed": 0.86, "status": 200}, "status": {"elapsed": 2.05, "status": 200}, "targets": {"elapsed": 0.25, "status": 200}, "viewers": {"elapsed": 0.25, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:45:31.233712+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:44:57.415298+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:43:21.224752+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:42:53.406519+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:41:18.060561+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:40:48.853261+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:39:08.007887+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:38:36.035642+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:45:55 -03 - Render Deploy Visibility Limit

- Tried to use the Render connector to inspect deploy status and service logs
  after pushing `d6e8dc6`; the connector returned `no workspace set`.
- No workspace was selected or changed from automation. Until the workspace is
  selected on the user's side, deploy state must be inferred from production
  app endpoints and observable worker behavior.
- Current rule remains: do not start a duplicate full job; resume only
  `0b36e332911a` if production enters `interrupted_resumable`.

## 2026-06-04 20:46:31 -03 - Monitor Cycle 1

- Job `0b36e332911a` status `interrupted_resumable`, coverage `interrupted_resumable`, resumeAvailable `True`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "interrupted_resumable": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `805`, stories `301`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `04/06/2026 23:44 UTC`, stories `1485`, articles `1968`, targets `27`.
- Live results: latest `2026-06-03T16:51:31.525271+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `121.52` MiB, VmHWM `681.3` MiB, limit `512` MiB.
- Disk: free `120153.9` MiB, DB `254.16` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.09, "status": 200}, "disk": {"elapsed": 0.28, "status": 200}, "events": {"elapsed": 0.25, "status": 200}, "health": {"elapsed": 1.35, "status": 200}, "live": {"elapsed": 0.31, "status": 200}, "memory": {"elapsed": 0.61, "status": 200}, "sqlite": {"elapsed": 0.6, "status": 200}, "status": {"elapsed": 1.11, "status": 200}, "targets": {"elapsed": 0.24, "status": 200}, "viewers": {"elapsed": 0.22, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "error": ""}, {"at": "2026-06-03T01:36:25.606763+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "pending", "error": ""}]`.
- Barriers: `["job_status:interrupted_resumable", "coverage:interrupted_resumable"]`.

## 2026-06-04 20:47:12 -03 - Resumed Same Production Job

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `805`, stories `301`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `04/06/2026 23:44 UTC`, stories `1485`, articles `1968`, targets `27`.
- Live results: latest `2026-06-03T16:51:31.525271+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `181.14` MiB, VmHWM `681.3` MiB, limit `512` MiB.
- Disk: free `119576.19` MiB, DB `254.17` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.68, "status": 200}, "disk": {"elapsed": 0.41, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 1.43, "status": 200}, "live": {"elapsed": 0.41, "status": 200}, "memory": {"elapsed": 0.41, "status": 200}, "sqlite": {"elapsed": 0.59, "status": 200}, "status": {"elapsed": 1.84, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.24, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "error": ""}, {"at": "2026-06-03T01:36:25.606763+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "pending", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:47:27 -03 - Monitor Cycle 1

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `805`, stories `301`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `04/06/2026 23:44 UTC`, stories `1485`, articles `1968`, targets `27`.
- Live results: latest `2026-06-03T16:51:31.525271+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `198.68` MiB, VmHWM `681.3` MiB, limit `512` MiB.
- Disk: free `119877.43` MiB, DB `254.17` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.05, "status": 200}, "disk": {"elapsed": 0.22, "status": 200}, "events": {"elapsed": 0.24, "status": 200}, "health": {"elapsed": 1.1, "status": 200}, "live": {"elapsed": 0.32, "status": 200}, "memory": {"elapsed": 0.22, "status": 200}, "sqlite": {"elapsed": 0.91, "status": 200}, "status": {"elapsed": 1.27, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.22, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "error": ""}, {"at": "2026-06-03T01:36:25.606763+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "pending", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:48:42 -03 - Monitor Cycle 2

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `16`, mentions `16`, stories `16`, publishedAt `2026-06-04T23:48:10.492457+00:00`.
- Website asset: generatedAt `04/06/2026 23:47 UTC`, stories `1485`, articles `1954`, targets `27`.
- Live results: latest `2026-06-04T23:48:29.709607+00:00`, count `57`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `221.09` MiB, VmHWM `681.3` MiB, limit `512` MiB.
- Disk: free `119611.07` MiB, DB `255.8` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.9, "status": 200}, "disk": {"elapsed": 0.27, "status": 200}, "events": {"elapsed": 0.36, "status": 200}, "health": {"elapsed": 1.43, "status": 200}, "live": {"elapsed": 0.81, "status": 200}, "memory": {"elapsed": 0.47, "status": 200}, "sqlite": {"elapsed": 0.94, "status": 200}, "status": {"elapsed": 1.44, "status": 200}, "targets": {"elapsed": 0.33, "status": 200}, "viewers": {"elapsed": 0.37, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:48:30.033760+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:48:21.624937+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:47:55.639510+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:47:38.374702+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:49:53 -03 - Monitor Cycle 3

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `36`, mentions `36`, stories `36`, publishedAt `2026-06-04T23:49:38.987843+00:00`.
- Website asset: generatedAt `04/06/2026 23:49 UTC`, stories `1485`, articles `1968`, targets `27`.
- Live results: latest `2026-06-04T23:49:36.454283+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `222.41` MiB, VmHWM `681.3` MiB, limit `512` MiB.
- Disk: free `119583.84` MiB, DB `258.16` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.89, "status": 200}, "disk": {"elapsed": 0.25, "status": 200}, "events": {"elapsed": 0.25, "status": 200}, "health": {"elapsed": 1.21, "status": 200}, "live": {"elapsed": 0.34, "status": 200}, "memory": {"elapsed": 0.24, "status": 200}, "sqlite": {"elapsed": 0.85, "status": 200}, "status": {"elapsed": 1.25, "status": 200}, "targets": {"elapsed": 0.24, "status": 200}, "viewers": {"elapsed": 0.25, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:49:37.768378+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:49:33.304979+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:49:21.967941+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:49:15.821585+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:49:03.844442+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:48:59.851952+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:48:48.614725+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:48:43.188511+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:51:03 -03 - Monitor Cycle 4

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22888, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `40`, mentions `40`, stories `40`, publishedAt `2026-06-04T23:49:55.297512+00:00`.
- Website asset: generatedAt `04/06/2026 23:49 UTC`, stories `1485`, articles `1968`, targets `27`.
- Live results: latest `2026-06-04T23:50:12.919266+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `223.23` MiB, VmHWM `681.3` MiB, limit `512` MiB.
- Disk: free `119875.77` MiB, DB `258.65` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.59, "status": 200}, "disk": {"elapsed": 0.23, "status": 200}, "events": {"elapsed": 0.25, "status": 200}, "health": {"elapsed": 1.01, "status": 200}, "live": {"elapsed": 0.43, "status": 200}, "memory": {"elapsed": 0.47, "status": 200}, "sqlite": {"elapsed": 0.58, "status": 200}, "status": {"elapsed": 1.04, "status": 200}, "targets": {"elapsed": 0.24, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:50:27.852400+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:50:16.249711+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:50:06.445039+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:49:37.768378+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:49:33.304979+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:49:21.967941+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:49:15.821585+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:49:03.844442+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-04 20:51:08 -03 - Playwright UI Contract Check

- Job `None` status `None`, coverage `n/a`, resumeAvailable `None`.
- Contract: date `None` to `None`, collector `None`, preset `None`, exact 18 keys `None`.
- Source ledger: total `None`, counts `{}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `None`, stories `None`, publishedAt `None`.
- Website asset: generatedAt `None`, stories `None`, articles `None`, targets `None`.
- Live results: latest `None`, count `None`.
- Viewer profile/login: login ok `None`, profile `None`.
- Target contract: `None`.
- Memory: VmRSS `None` MiB, VmHWM `None` MiB, limit `None` MiB.
- Disk: free `None` MiB, DB `None` MiB.
- Storage diagnostic: enabled `None`, reason ``.
- HTTP timings/status: `{}`.
- Recent source events: `[]`.
- Barriers: `[]`.

## 2026-06-04 20:52:04 -03 - Playwright UI Contract Check

- Profile listed: `True`.
- Viewer login HTTP: `200`; `/api/targets` HTTP: `200`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Primary keys exact: `True`; default-checked exact: `True`.
- Primary keys: `["seguranca_presente", "programa_seguranca_presente", "operacao_seguranca_presente", "seguranca", "inseguranca", "crime", "criminalidade", "violencia", "assalto", "roubo", "furto", "medo", "policiamento", "patrulhamento", "percepcao_de_seguranca", "sensacao_de_seguranca", "reforco_no_policiamento", "ordem_publica"]`.
- Checked primary keys: `["seguranca_presente", "programa_seguranca_presente", "operacao_seguranca_presente", "seguranca", "inseguranca", "crime", "criminalidade", "violencia", "assalto", "roubo", "furto", "medo", "policiamento", "patrulhamento", "percepcao_de_seguranca", "sensacao_de_seguranca", "reforco_no_policiamento", "ordem_publica"]`.
- Secondary keys: `[]`; secondary empty `True`.
- Runner status: `Atualizando`.
- Browser errors/warnings: `[]`.
- Barriers: `[]`.

## 2026-06-05 09:15:27 -03 - Corrected Article-Save Assumption

- User challenged the assumption that it would be normal to wait a long time
  for a saved article with broad targets over a 12-year backfill.
- Correction: that assumption was wrong. Article saves should be visible
  quickly when a source returns relevant candidates; a long interval with
  candidates but no saves is a collection/matching/dedupe/date-range warning.
- Pulled full `source_run_*` payloads instead of the previous compact event
  summary. Recent `Agenda do Poder` checkpoints show saves:
  - `2026-06-05T12:10:38Z`: `25` candidates, `7` articles inserted;
  - `2026-06-05T12:13:06Z`: `25` candidates, `9` articles inserted;
  - `2026-06-05T12:15:15Z`: `25` candidates, `6` articles inserted.
- The misleading signal was `sourceRunCounts.complete` staying at `23` while
  one paginated source-run remained `pending`. That count tracks completed
  source-run units, not per-page article saves.
- Updated the operator event summary to include candidate/article/mention/story
  metrics so future monitoring does not hide this distinction.

## 2026-06-05 09:13:34 -03 - Post-Repair Monitoring Result

- User corrected the stopping point; active monitoring resumed.
- Production entered HTTP unavailability/slowdown: `/healthz` and `/api/csrf`
  timed out at 20s, and an operator monitor cycle recorded endpoint timeouts
  across the public/admin surface while SQLite debug still reported
  `activeJobsCount=1` and `quickCheck=ok`.
- Root cause candidate in code: durable source-runs were forcing
  `upload_live_checkpoint(..., force=True)` after every source-run, even when
  no articles were saved. This was especially risky during fast empty runs such
  as `O Globo Sitemap`.
- Implemented and deployed `97e75c1 fix(jobs): throttle empty source checkpoints`:
  - empty source-runs now use throttled live checkpoint uploads;
  - source-runs with saved articles still force a checkpoint;
  - durable loop now yields briefly between source-runs.
- Tests before deploy: `12 passed` for the focused durable-runner,
  storage-bridge, and operator tests.
- Deploy interrupted the job as expected; resumed only job `0b36e332911a`.
- Credential drift recurred after deploy; repaired `voluntarios_lab_politicas`
  password through production admin and saved plaintext only in the password
  note.
- Bad but confirmed state: the pre-deploy progress around `complete=2508` did
  not survive as a recoverable checkpoint. Production resumed from the known
  floor `complete=23`.
- Post-repair monitor result: 4 cycles with no barriers, endpoints responsive
  (`health/status/live/assets` under the 30s barrier), RSS around `200-230 MiB`,
  SQLite quick check `ok`, live results and assets advanced when saved articles
  appeared.
- Playwright UI check passed at `2026-06-05 09:13:19 -03`: profile listed,
  viewer login HTTP 200, exactly 18 primary/default-checked targets, no
  secondary leakage, runner status `Atualizando`.

## 2026-06-04 20:52:35 -03 - Production Recovery Baseline

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `45`, mentions `46`, stories `46`, publishedAt `2026-06-04T23:52:21.591294+00:00`.
- Website asset: generatedAt `04/06/2026 23:52 UTC`, stories `1485`, articles `1971`, targets `27`.
- Live results: latest `2026-06-04T23:52:05.924302+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `241.58` MiB, VmHWM `681.3` MiB, limit `512` MiB.
- Disk: free `119134.59` MiB, DB `259.27` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.77, "status": 200}, "disk": {"elapsed": 0.26, "status": 200}, "events": {"elapsed": 0.24, "status": 200}, "health": {"elapsed": 1.36, "status": 200}, "live": {"elapsed": 0.43, "status": 200}, "memory": {"elapsed": 0.23, "status": 200}, "sqlite": {"elapsed": 0.82, "status": 200}, "status": {"elapsed": 1.09, "status": 200}, "targets": {"elapsed": 0.25, "status": 200}, "viewers": {"elapsed": 0.24, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-04T23:52:06.065107+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:50:27.852400+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:50:16.249711+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:50:06.445039+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:49:37.768378+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:49:33.304979+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-04T23:49:21.967941+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-04T23:49:15.821585+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 08:47:39 -03 - Production Recovery Baseline

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 2491, "pending": 20421}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `286`, mentions `295`, stories `295`, publishedAt `2026-06-05T02:25:30.041855+00:00`.
- Website asset: generatedAt `05/06/2026 02:25 UTC`, stories `1483`, articles `2004`, targets `27`.
- Live results: latest `2026-06-05T02:26:09.998522+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `280.14` MiB, VmHWM `681.3` MiB, limit `512` MiB.
- Disk: free `120021.01` MiB, DB `295.0` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.56, "status": 200}, "disk": {"elapsed": 0.61, "status": 200}, "events": {"elapsed": 0.26, "status": 200}, "health": {"elapsed": 1.28, "status": 200}, "live": {"elapsed": 0.3, "status": 200}, "memory": {"elapsed": 0.61, "status": 200}, "sqlite": {"elapsed": 1.01, "status": 200}, "status": {"elapsed": 1.44, "status": 200}, "targets": {"elapsed": 0.94, "status": 200}, "viewers": {"elapsed": 0.24, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T11:47:25.401580+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:47:24.608137+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:47:11.930090+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:47:11.166634+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:46:58.540280+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:46:57.660007+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:46:45.002857+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:46:44.238691+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 08:48:03 -03 - Monitor Cycle 1

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 2493, "pending": 20419}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `286`, mentions `295`, stories `295`, publishedAt `2026-06-05T02:25:30.041855+00:00`.
- Website asset: generatedAt `05/06/2026 02:25 UTC`, stories `1483`, articles `2004`, targets `27`.
- Live results: latest `2026-06-05T02:26:09.998522+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `287.27` MiB, VmHWM `681.3` MiB, limit `512` MiB.
- Disk: free `120040.71` MiB, DB `295.0` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.65, "status": 200}, "disk": {"elapsed": 0.31, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 0.79, "status": 200}, "live": {"elapsed": 0.33, "status": 200}, "memory": {"elapsed": 0.38, "status": 200}, "sqlite": {"elapsed": 0.98, "status": 200}, "status": {"elapsed": 1.29, "status": 200}, "targets": {"elapsed": 0.24, "status": 200}, "viewers": {"elapsed": 0.25, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T11:47:54.903134+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:47:53.986300+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:47:41.151019+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:47:40.335245+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:47:25.401580+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:47:24.608137+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:47:11.930090+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:47:11.166634+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 08:49:13 -03 - Monitor Cycle 2

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 2498, "pending": 20414}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `286`, mentions `295`, stories `295`, publishedAt `2026-06-05T02:25:30.041855+00:00`.
- Website asset: generatedAt `05/06/2026 02:25 UTC`, stories `1483`, articles `2004`, targets `27`.
- Live results: latest `2026-06-05T02:26:09.998522+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `286.41` MiB, VmHWM `681.3` MiB, limit `512` MiB.
- Disk: free `120051.6` MiB, DB `295.01` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.54, "status": 200}, "disk": {"elapsed": 0.23, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 0.92, "status": 200}, "live": {"elapsed": 0.56, "status": 200}, "memory": {"elapsed": 0.44, "status": 200}, "sqlite": {"elapsed": 0.93, "status": 200}, "status": {"elapsed": 0.84, "status": 200}, "targets": {"elapsed": 0.24, "status": 200}, "viewers": {"elapsed": 0.24, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T11:49:05.203468+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:49:04.330868+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:48:50.918705+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:48:50.184349+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:48:37.716762+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:48:36.785691+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:48:23.600544+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:48:22.866289+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 08:50:31 -03 - Monitor Cycle 3

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 2503, "pending": 20409}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `286`, mentions `295`, stories `295`, publishedAt `2026-06-05T02:25:30.041855+00:00`.
- Website asset: generatedAt `05/06/2026 02:25 UTC`, stories `1483`, articles `2004`, targets `27`.
- Live results: latest `2026-06-05T02:26:09.998522+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `288.38` MiB, VmHWM `681.3` MiB, limit `512` MiB.
- Disk: free `119660.46` MiB, DB `295.02` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 2.21, "status": 200}, "disk": {"elapsed": 0.25, "status": 200}, "events": {"elapsed": 0.25, "status": 200}, "health": {"elapsed": 1.42, "status": 200}, "live": {"elapsed": 0.67, "status": 200}, "memory": {"elapsed": 0.45, "status": 200}, "sqlite": {"elapsed": 1.04, "status": 200}, "status": {"elapsed": 1.65, "status": 200}, "targets": {"elapsed": 0.24, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T11:50:13.612909+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:50:12.865700+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:50:00.236097+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:49:59.351497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:49:46.577704+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:49:45.637197+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:49:33.036217+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:49:32.067530+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 08:52:07 -03 - Monitor Cycle 4

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 2508, "pending": 20404}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `286`, mentions `295`, stories `295`, publishedAt `2026-06-05T02:25:30.041855+00:00`.
- Website asset: generatedAt `05/06/2026 02:25 UTC`, stories `1483`, articles `2004`, targets `27`.
- Live results: latest `2026-06-05T02:26:09.998522+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `319.3` MiB, VmHWM `681.3` MiB, limit `512` MiB.
- Disk: free `119613.67` MiB, DB `295.04` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.12, "status": 200}, "disk": {"elapsed": 0.25, "status": 200}, "events": {"elapsed": 0.28, "status": 200}, "health": {"elapsed": 2.24, "status": 200}, "live": {"elapsed": 20.16, "status": 200}, "memory": {"elapsed": 0.31, "status": 200}, "sqlite": {"elapsed": 1.42, "status": 200}, "status": {"elapsed": 2.48, "status": 200}, "targets": {"elapsed": 0.32, "status": 200}, "viewers": {"elapsed": 0.3, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T11:51:30.510808+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:51:29.646685+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:51:13.847175+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:51:13.087599+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:50:58.658216+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:50:57.737485+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}, {"at": "2026-06-05T11:50:43.354144+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "error": ""}, {"at": "2026-06-05T11:50:42.537977+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 08:52:20 -03 - Publication Freshness Interpretation

- Resumed active monitoring after user corrected the stopping point.
- The production job is still `running` on the same job id `0b36e332911a`;
  no duplicate job was started.
- Source ledger advanced during the 4-cycle monitor from `2493` complete to
  `2508` complete.
- `articles/mentions/stories` stayed flat at `286/295/295` during those same
  cycles, while recent events were `O Globo Sitemap` start/complete pairs.
- Because no new saved articles were observed in this interval, the stale
  website/live timestamps (`generatedAt 05/06/2026 02:25 UTC`,
  live latest `2026-06-05T02:26:09.998522+00:00`) are not yet proof of broken
  publication. They remain a watched condition: if saved article counts advance
  and asset/live timestamps do not, enter repair mode.
- Noted slowdown: final `/api/update/live-results` call returned HTTP 200 but
  took `20.16s`, below the 30s barrier but high enough to keep monitoring.

## 2026-06-05 09:00:35 -03 - Monitor Cycle 1

- Job `` status ``, coverage `n/a`, resumeAvailable `False`.
- Contract: date `` to ``, collector ``, preset ``, exact 18 keys `False`.
- Source ledger: total `0`, counts `{}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `None`, stories `None`, publishedAt ``.
- Website asset: generatedAt ``, stories `0`, articles `None`, targets `0`.
- Live results: latest ``, count `0`.
- Viewer profile/login: login ok `False`, profile `{'found': False, 'profileCount': 0}`.
- Target contract: `{'count': 0, 'missing': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'extra': [], 'primaryExact': False}`.
- Memory: VmRSS `None` MiB, VmHWM `None` MiB, limit `None` MiB.
- Disk: free `None` MiB, DB `295.04` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 70.34, "status": 0}, "disk": {"elapsed": 45.11, "status": 0}, "events": {"elapsed": 45.25, "status": 0}, "health": {"elapsed": 45.18, "status": 0}, "live": {"elapsed": 45.11, "status": 0}, "memory": {"elapsed": 45.11, "status": 0}, "sqlite": {"elapsed": 2.28, "status": 200}, "status": {"elapsed": 70.2, "status": 0}, "targets": {"elapsed": 45.18, "status": 0}, "viewers": {"elapsed": 45.12, "status": 0}}`.
- Recent source events: `[]`.
- Barriers: `["target_keys_not_exact", "date_range_mismatch", "viewer_login_failed", "target_contract_failed", "viewer_profile_target_scope_failed", "endpoint_failed:health:0", "endpoint_slow:health:45.18", "endpoint_failed:status:0", "endpoint_slow:status:70.2", "endpoint_failed:memory:0", "endpoint_slow:memory:45.11", "endpoint_failed:disk:0", "endpoint_slow:disk:45.11", "endpoint_failed:events:0", "endpoint_slow:events:45.25", "endpoint_failed:live:0", "endpoint_slow:live:45.11", "endpoint_failed:asset:0", "endpoint_slow:asset:70.34", "endpoint_failed:targets:0", "endpoint_slow:targets:45.18", "endpoint_failed:viewers:0", "endpoint_slow:viewers:45.12"]`.

## 2026-06-05 09:08:23 -03 - Resumed Same Production Job

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `805`, stories `301`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `05/06/2026 02:25 UTC`, stories `1483`, articles `2004`, targets `27`.
- Live results: latest `2026-06-03T16:51:31.525271+00:00`, count `51`.
- Viewer profile/login: login ok `False`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `174.35` MiB, VmHWM `674.27` MiB, limit `512` MiB.
- Disk: free `56657.53` MiB, DB `254.16` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.1, "status": 200}, "disk": {"elapsed": 0.24, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 1.37, "status": 200}, "live": {"elapsed": 0.43, "status": 200}, "memory": {"elapsed": 0.34, "status": 200}, "sqlite": {"elapsed": 0.56, "status": 200}, "status": {"elapsed": 1.71, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "error": ""}, {"at": "2026-06-03T01:36:25.606763+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "pending", "error": ""}]`.
- Barriers: `["viewer_login_failed"]`.

## 2026-06-05 09:09:21 -03 - Password Repair Applied

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22888, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `805`, stories `301`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `05/06/2026 02:25 UTC`, stories `1483`, articles `2004`, targets `27`.
- Live results: latest `2026-06-03T16:51:31.525271+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `198.56` MiB, VmHWM `674.27` MiB, limit `512` MiB.
- Disk: free `56961.2` MiB, DB `254.16` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.65, "status": 200}, "disk": {"elapsed": 0.24, "status": 200}, "events": {"elapsed": 0.26, "status": 200}, "health": {"elapsed": 1.2, "status": 200}, "live": {"elapsed": 0.44, "status": 200}, "memory": {"elapsed": 0.38, "status": 200}, "sqlite": {"elapsed": 0.57, "status": 200}, "status": {"elapsed": 1.23, "status": 200}, "targets": {"elapsed": 0.24, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T12:08:59.012998+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 09:09:35 -03 - Monitor Cycle 1

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22888, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `805`, stories `301`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `05/06/2026 02:25 UTC`, stories `1483`, articles `2004`, targets `27`.
- Live results: latest `2026-06-03T16:51:31.525271+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `200.55` MiB, VmHWM `674.27` MiB, limit `512` MiB.
- Disk: free `56962.49` MiB, DB `254.16` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.08, "status": 200}, "disk": {"elapsed": 0.24, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 0.92, "status": 200}, "live": {"elapsed": 0.44, "status": 200}, "memory": {"elapsed": 0.27, "status": 200}, "sqlite": {"elapsed": 0.58, "status": 200}, "status": {"elapsed": 0.83, "status": 200}, "targets": {"elapsed": 0.25, "status": 200}, "viewers": {"elapsed": 0.24, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T12:08:59.012998+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 09:10:53 -03 - Monitor Cycle 2

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `7`, mentions `7`, stories `7`, publishedAt `2026-06-05T12:10:40.269653+00:00`.
- Website asset: generatedAt `05/06/2026 12:10 UTC`, stories `1483`, articles `1954`, targets `27`.
- Live results: latest `2026-06-05T12:10:38.175798+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `220.84` MiB, VmHWM `674.27` MiB, limit `512` MiB.
- Disk: free `56678.38` MiB, DB `254.7` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.13, "status": 200}, "disk": {"elapsed": 0.41, "status": 200}, "events": {"elapsed": 0.24, "status": 200}, "health": {"elapsed": 1.39, "status": 200}, "live": {"elapsed": 0.31, "status": 200}, "memory": {"elapsed": 0.62, "status": 200}, "sqlite": {"elapsed": 1.2, "status": 200}, "status": {"elapsed": 1.48, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T12:10:38.664956+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-05T12:08:59.012998+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 09:12:02 -03 - Monitor Cycle 3

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22888, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `869`, mentions `1307`, stories `1307`, publishedAt `2026-06-05T12:10:56.487423+00:00`.
- Website asset: generatedAt `05/06/2026 12:10 UTC`, stories `1483`, articles `1954`, targets `27`.
- Live results: latest `2026-06-05T12:11:44.892377+00:00`, count `52`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `229.87` MiB, VmHWM `674.27` MiB, limit `512` MiB.
- Disk: free `56000.73` MiB, DB `254.7` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.61, "status": 200}, "disk": {"elapsed": 0.25, "status": 200}, "events": {"elapsed": 0.28, "status": 200}, "health": {"elapsed": 0.96, "status": 200}, "live": {"elapsed": 0.3, "status": 200}, "memory": {"elapsed": 0.22, "status": 200}, "sqlite": {"elapsed": 0.54, "status": 200}, "status": {"elapsed": 0.8, "status": 200}, "targets": {"elapsed": 0.22, "status": 200}, "viewers": {"elapsed": 0.26, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T12:11:08.076237+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-05T12:10:38.664956+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-05T12:08:59.012998+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 09:13:14 -03 - Monitor Cycle 4

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `16`, mentions `16`, stories `16`, publishedAt `2026-06-05T12:13:08.402229+00:00`.
- Website asset: generatedAt `05/06/2026 12:13 UTC`, stories `1483`, articles `1958`, targets `27`.
- Live results: latest `2026-06-05T12:13:04.502483+00:00`, count `57`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `230.04` MiB, VmHWM `674.27` MiB, limit `512` MiB.
- Disk: free `55754.66` MiB, DB `255.81` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.05, "status": 200}, "disk": {"elapsed": 0.23, "status": 200}, "events": {"elapsed": 0.24, "status": 200}, "health": {"elapsed": 1.23, "status": 200}, "live": {"elapsed": 0.43, "status": 200}, "memory": {"elapsed": 0.23, "status": 200}, "sqlite": {"elapsed": 0.64, "status": 200}, "status": {"elapsed": 1.09, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T12:13:06.267809+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-05T12:11:08.076237+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-05T12:10:38.664956+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "error": ""}, {"at": "2026-06-05T12:08:59.012998+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 09:13:19 -03 - Playwright UI Contract Check

- Profile listed: `True`.
- Viewer login HTTP: `200`; `/api/targets` HTTP: `200`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Primary keys exact: `True`; default-checked exact: `True`.
- Primary keys: `["seguranca_presente", "programa_seguranca_presente", "operacao_seguranca_presente", "seguranca", "inseguranca", "crime", "criminalidade", "violencia", "assalto", "roubo", "furto", "medo", "policiamento", "patrulhamento", "percepcao_de_seguranca", "sensacao_de_seguranca", "reforco_no_policiamento", "ordem_publica"]`.
- Checked primary keys: `["seguranca_presente", "programa_seguranca_presente", "operacao_seguranca_presente", "seguranca", "inseguranca", "crime", "criminalidade", "violencia", "assalto", "roubo", "furto", "medo", "policiamento", "patrulhamento", "percepcao_de_seguranca", "sensacao_de_seguranca", "reforco_no_policiamento", "ordem_publica"]`.
- Secondary keys: `[]`; secondary empty `True`.
- Runner status: `Atualizando`.
- Browser errors/warnings: `[]`.
- Barriers: `[]`.

## 2026-06-05 09:15:21 -03 - Production Recovery Baseline

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `22`, mentions `22`, stories `22`, publishedAt `2026-06-05T12:13:23.246195+00:00`.
- Website asset: generatedAt `05/06/2026 12:15 UTC`, stories `1483`, articles `1961`, targets `27`.
- Live results: latest `2026-06-05T12:15:08.192469+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `242.74` MiB, VmHWM `674.27` MiB, limit `512` MiB.
- Disk: free `54750.7` MiB, DB `256.55` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.1, "status": 200}, "disk": {"elapsed": 0.61, "status": 200}, "events": {"elapsed": 0.25, "status": 200}, "health": {"elapsed": 1.23, "status": 200}, "live": {"elapsed": 0.32, "status": 200}, "memory": {"elapsed": 0.61, "status": 200}, "sqlite": {"elapsed": 0.8, "status": 200}, "status": {"elapsed": 1.84, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.28, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T12:15:15.174201+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "candidatesSeen": 25, "candidatesTotal": 25, "articlesInserted": 6, "mentionsInserted": 6, "storiesTouched": 6, "rssBefore": 237.5, "rssAfter": 240.99, "error": ""}, {"at": "2026-06-05T12:13:35.097276+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 237.5, "rssAfter": null, "error": ""}, {"at": "2026-06-05T12:13:06.267809+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "candidatesSeen": 25, "candidatesTotal": 25, "articlesInserted": 9, "mentionsInserted": 9, "storiesTouched": 9, "rssBefore": 228.77, "rssAfter": 227.09, "error": ""}, {"at": "2026-06-05T12:11:08.076237+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 228.77, "rssAfter": null, "error": ""}, {"at": "2026-06-05T12:10:38.664956+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "pending", "candidatesSeen": 25, "candidatesTotal": 25, "articlesInserted": 7, "mentionsInserted": 7, "storiesTouched": 7, "rssBefore": 194.91, "rssAfter": 218.79, "error": ""}, {"at": "2026-06-05T12:08:59.012998+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Agenda do Poder", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 194.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 239.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "candidatesSeen": 25, "candidatesTotal": 25, "articlesInserted": 4, "mentionsInserted": 4, "storiesTouched": 4, "rssBefore": 239.91, "rssAfter": 239.91, "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 10:03:09 -03 - Production Recovery Baseline

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 838, "pending": 22074}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `117`, mentions `125`, stories `125`, publishedAt `2026-06-05T12:42:06.711882+00:00`.
- Website asset: generatedAt `05/06/2026 12:41 UTC`, stories `1432`, articles `1924`, targets `27`.
- Live results: latest `2026-06-05T12:41:51.021577+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `277.65` MiB, VmHWM `674.27` MiB, limit `512` MiB.
- Disk: free `53626.41` MiB, DB `270.2` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.12, "status": 200}, "disk": {"elapsed": 0.24, "status": 200}, "events": {"elapsed": 0.22, "status": 200}, "health": {"elapsed": 1.39, "status": 200}, "live": {"elapsed": 0.3, "status": 200}, "memory": {"elapsed": 0.23, "status": 200}, "sqlite": {"elapsed": 1.03, "status": 200}, "status": {"elapsed": 1.49, "status": 200}, "targets": {"elapsed": 0.22, "status": 200}, "viewers": {"elapsed": 0.24, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T13:02:53.371129+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 262.96, "rssAfter": 262.96, "error": ""}, {"at": "2026-06-05T13:02:52.430324+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 262.96, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:02:52.312638+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 262.96, "rssAfter": 262.96, "error": ""}, {"at": "2026-06-05T13:02:51.615731+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 262.96, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:02:51.499471+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 262.96, "rssAfter": 262.96, "error": ""}, {"at": "2026-06-05T13:02:50.670692+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 262.96, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:02:50.553012+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 262.96, "rssAfter": 262.96, "error": ""}, {"at": "2026-06-05T13:02:49.809277+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 262.96, "rssAfter": null, "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 10:07:24 -03 - Production Recovery Baseline

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 990, "pending": 21921, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `117`, mentions `125`, stories `125`, publishedAt `2026-06-05T12:42:06.711882+00:00`.
- Website asset: generatedAt `05/06/2026 12:41 UTC`, stories `1432`, articles `1924`, targets `27`.
- Live results: latest `2026-06-05T12:41:51.021577+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `287.46` MiB, VmHWM `674.27` MiB, limit `512` MiB.
- Disk: free `53330.8` MiB, DB `270.48` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.66, "status": 200}, "disk": {"elapsed": 0.33, "status": 200}, "events": {"elapsed": 0.24, "status": 200}, "health": {"elapsed": 1.17, "status": 200}, "live": {"elapsed": 0.29, "status": 200}, "memory": {"elapsed": 0.76, "status": 200}, "sqlite": {"elapsed": 0.64, "status": 200}, "status": {"elapsed": 1.23, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T13:07:22.134282+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 284.49, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:07:22.010376+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 292.37, "rssAfter": 287.46, "error": ""}, {"at": "2026-06-05T13:07:21.163072+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 292.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:07:20.918790+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 286.22, "rssAfter": 289.38, "error": ""}, {"at": "2026-06-05T13:07:19.961569+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 286.22, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:07:19.712578+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 276.57, "rssAfter": 279.5, "error": ""}, {"at": "2026-06-05T13:07:18.849567+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 276.57, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:07:18.622916+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 276.57, "rssAfter": 276.57, "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 10:13:34 -03 - Backend Low-Volume Diagnosis and Local Fix

- Incident finding: the low article/story count is backend scheduling, not delayed saves. Source-run events already proved articles were being inserted within a checkpoint when candidates existed.
- Root cause: `run_durable_update()` scheduled and processed source-runs one `target_key` at a time. Production was still spending source-runs on `seguranca_presente`; the broad terms such as `segurança`, `crime`, `roubo`, `furto`, and `violência` had not received equivalent collection yet.
- Evidence: production source ledger total `22912` matches one target-scale source plan for `2014-01-01` through `2026-06-02` (`4536` days; `22680` sitemap daily rows plus RSS/search/archive rows), not 18 independent target-scale plans.
- Local backend fix prepared in `web_app/jobs.py`: durable multi-target jobs now use grouped source-runs under target key `__all_targets__`; each source-run carries all query variants and ingests against all selected target snapshots.
- Same-job recovery behavior prepared: if a resumable multi-target job has legacy per-target source-run rows, the runner deletes and replaces that ledger with grouped source-run rows for the same job id, then logs `source_run_ledger_migrated`.
- Observability prepared: `/api/update/status` now exposes aggregate `sourceRunTargetCounts` and `sourceRunSourceTypeCounts`, and grouped source-run events include the full `target_keys` list.
- Operator script prepared: source-run event summaries now keep `candidatesSeen`, `candidatesTotal`, `articlesInserted`, `mentionsInserted`, `storiesTouched`, `rssBefore`, and `rssAfter`.
- Tests: `.venv_playwright/bin/python -m pytest tests/test_targets_jobs.py tests/test_voluntarios_backfill_operator.py -q` passed with `81 passed`.
- Next action: deploy the backend fix, allow the deploy to interrupt production cleanly, resume only job `0b36e332911a`, verify the ledger migrates to grouped rows, then monitor article/live-results movement against all 18 primary targets.

## 2026-06-05 10:14:24 -03 - Production Recovery Baseline

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 1235, "pending": 21677}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `117`, mentions `125`, stories `125`, publishedAt `2026-06-05T12:42:06.711882+00:00`.
- Website asset: generatedAt `05/06/2026 12:41 UTC`, stories `1432`, articles `1924`, targets `27`.
- Live results: latest `2026-06-05T12:41:51.021577+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `278.64` MiB, VmHWM `674.27` MiB, limit `512` MiB.
- Disk: free `50935.11` MiB, DB `270.92` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.07, "status": 200}, "disk": {"elapsed": 0.61, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 1.64, "status": 200}, "live": {"elapsed": 0.3, "status": 200}, "memory": {"elapsed": 0.41, "status": 200}, "sqlite": {"elapsed": 0.87, "status": 200}, "status": {"elapsed": 1.84, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.24, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T13:14:21.966165+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 278.64, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:14:21.851219+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 278.64, "rssAfter": 278.64, "error": ""}, {"at": "2026-06-05T13:14:20.970849+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 278.64, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:14:04.662534+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 277.52, "rssAfter": 277.52, "error": ""}, {"at": "2026-06-05T13:14:03.877653+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 277.52, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:14:03.764134+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 277.52, "rssAfter": 277.52, "error": ""}, {"at": "2026-06-05T13:14:02.932922+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 277.52, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:14:02.807636+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "O Globo Sitemap", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 277.52, "rssAfter": 277.52, "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 10:19:00 -03 - Resumed Same Production Job

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `805`, stories `301`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `05/06/2026 12:41 UTC`, stories `1432`, articles `1924`, targets `27`.
- Live results: latest `2026-06-03T16:51:31.525271+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `197.06` MiB, VmHWM `682.38` MiB, limit `512` MiB.
- Disk: free `46838.75` MiB, DB `254.17` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.06, "status": 200}, "disk": {"elapsed": 0.23, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 2.42, "status": 200}, "live": {"elapsed": 0.44, "status": 200}, "memory": {"elapsed": 0.22, "status": 200}, "sqlite": {"elapsed": 0.93, "status": 200}, "status": {"elapsed": 1.64, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 239.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "candidatesSeen": 25, "candidatesTotal": 25, "articlesInserted": 4, "mentionsInserted": 4, "storiesTouched": 4, "rssBefore": 239.91, "rssAfter": 239.91, "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 239.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "candidatesSeen": 25, "candidatesTotal": 25, "articlesInserted": 10, "mentionsInserted": 10, "storiesTouched": 10, "rssBefore": 239.91, "rssAfter": 239.91, "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 239.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "candidatesSeen": 24, "candidatesTotal": 24, "articlesInserted": 8, "mentionsInserted": 8, "storiesTouched": 8, "rssBefore": 239.91, "rssAfter": 239.91, "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 239.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:36:25.606763+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "pending", "candidatesSeen": 25, "candidatesTotal": 25, "articlesInserted": 4, "mentionsInserted": 4, "storiesTouched": 4, "rssBefore": 239.91, "rssAfter": 239.91, "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 10:22:08 -03 - Production Recovery Baseline

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22911`, counts `{"complete": 6, "pending": 22904, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `877`, mentions `1317`, stories `1315`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `05/06/2026 12:41 UTC`, stories `1432`, articles `1924`, targets `27`.
- Live results: latest `2026-06-05T13:21:52.039174+00:00`, count `57`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `277.45` MiB, VmHWM `682.38` MiB, limit `512` MiB.
- Disk: free `57123.84` MiB, DB `269.05` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.52, "status": 200}, "disk": {"elapsed": 0.24, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 2.62, "status": 200}, "live": {"elapsed": 0.45, "status": 200}, "memory": {"elapsed": 0.26, "status": 200}, "sqlite": {"elapsed": 1.04, "status": 200}, "status": {"elapsed": 1.95, "status": 200}, "targets": {"elapsed": 0.22, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T13:19:54.472378+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "G1 Politica", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:54.320429+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "G1", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 229.37, "rssAfter": 229.37, "error": ""}, {"at": "2026-06-05T13:19:53.209167+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "G1", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:53.054730+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "Veja Rio", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 229.37, "rssAfter": 229.37, "error": ""}, {"at": "2026-06-05T13:19:52.904945+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:52.744324+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "VEJA Cidades", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 231.46, "rssAfter": 231.37, "error": ""}, {"at": "2026-06-05T13:19:52.422056+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "VEJA Cidades", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 231.46, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:52.221307+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "VEJA Politica", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 231.46, "rssAfter": 231.46, "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 10:22:40 -03 - Monitor Cycle 1

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22911`, counts `{"complete": 6, "pending": 22904, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `881`, mentions `1323`, stories `1319`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `05/06/2026 12:41 UTC`, stories `1432`, articles `1924`, targets `27`.
- Live results: latest `2026-06-05T13:22:22.513471+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `297.28` MiB, VmHWM `682.38` MiB, limit `512` MiB.
- Disk: free `57107.09` MiB, DB `271.26` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.08, "status": 200}, "disk": {"elapsed": 0.6, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 2.25, "status": 200}, "live": {"elapsed": 0.45, "status": 200}, "memory": {"elapsed": 0.42, "status": 200}, "sqlite": {"elapsed": 0.62, "status": 200}, "status": {"elapsed": 1.85, "status": 200}, "targets": {"elapsed": 0.25, "status": 200}, "viewers": {"elapsed": 0.25, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T13:19:54.472378+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "G1 Politica", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:54.320429+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "G1", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 229.37, "rssAfter": 229.37, "error": ""}, {"at": "2026-06-05T13:19:53.209167+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "G1", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:53.054730+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "Veja Rio", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 229.37, "rssAfter": 229.37, "error": ""}, {"at": "2026-06-05T13:19:52.904945+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:52.744324+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "VEJA Cidades", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 231.46, "rssAfter": 231.37, "error": ""}, {"at": "2026-06-05T13:19:52.422056+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "VEJA Cidades", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 231.46, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:52.221307+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "VEJA Politica", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 231.46, "rssAfter": 231.46, "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 10:23:53 -03 - Monitor Cycle 2

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22911`, counts `{"complete": 7, "pending": 22903, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `886`, mentions `1329`, stories `1324`, publishedAt `2026-06-05T13:23:00.830627+00:00`.
- Website asset: generatedAt `05/06/2026 13:22 UTC`, stories `1432`, articles `1892`, targets `27`.
- Live results: latest `2026-06-05T13:23:49.529306+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `270.54` MiB, VmHWM `682.38` MiB, limit `512` MiB.
- Disk: free `57430.66` MiB, DB `271.8` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.05, "status": 200}, "disk": {"elapsed": 0.29, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 1.33, "status": 200}, "live": {"elapsed": 0.35, "status": 200}, "memory": {"elapsed": 0.61, "status": 200}, "sqlite": {"elapsed": 0.93, "status": 200}, "status": {"elapsed": 2.25, "status": 200}, "targets": {"elapsed": 0.24, "status": 200}, "viewers": {"elapsed": 0.23, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T13:23:13.102574+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "G1 Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 270.23, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:22:43.388937+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "G1 Politica", "status": "complete", "candidatesSeen": 54, "candidatesTotal": 54, "articlesInserted": 21, "mentionsInserted": 26, "storiesTouched": 21, "rssBefore": 229.37, "rssAfter": 299.84, "error": ""}, {"at": "2026-06-05T13:19:54.472378+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "G1 Politica", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:54.320429+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "G1", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 229.37, "rssAfter": 229.37, "error": ""}, {"at": "2026-06-05T13:19:53.209167+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "G1", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:53.054730+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "Veja Rio", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 229.37, "rssAfter": 229.37, "error": ""}, {"at": "2026-06-05T13:19:52.904945+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:52.744324+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "VEJA Cidades", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 231.46, "rssAfter": 231.37, "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 10:25:04 -03 - Monitor Cycle 3

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22911`, counts `{"complete": 7, "pending": 22903, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `898`, mentions `1348`, stories `1336`, publishedAt `2026-06-05T13:23:00.830627+00:00`.
- Website asset: generatedAt `05/06/2026 13:22 UTC`, stories `1432`, articles `1892`, targets `27`.
- Live results: latest `2026-06-05T13:24:56.006535+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `281.38` MiB, VmHWM `682.38` MiB, limit `512` MiB.
- Disk: free `57427.2` MiB, DB `271.8` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.65, "status": 200}, "disk": {"elapsed": 0.23, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 1.07, "status": 200}, "live": {"elapsed": 0.44, "status": 200}, "memory": {"elapsed": 0.24, "status": 200}, "sqlite": {"elapsed": 0.78, "status": 200}, "status": {"elapsed": 1.13, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.22, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T13:23:13.102574+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "G1 Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 270.23, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:22:43.388937+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "G1 Politica", "status": "complete", "candidatesSeen": 54, "candidatesTotal": 54, "articlesInserted": 21, "mentionsInserted": 26, "storiesTouched": 21, "rssBefore": 229.37, "rssAfter": 299.84, "error": ""}, {"at": "2026-06-05T13:19:54.472378+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "G1 Politica", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:54.320429+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "G1", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 229.37, "rssAfter": 229.37, "error": ""}, {"at": "2026-06-05T13:19:53.209167+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "G1", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:53.054730+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "Veja Rio", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 229.37, "rssAfter": 229.37, "error": ""}, {"at": "2026-06-05T13:19:52.904945+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:52.744324+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "VEJA Cidades", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 231.46, "rssAfter": 231.37, "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 10:26:19 -03 - Monitor Cycle 4

- Job `0b36e332911a` status `running`, coverage `running`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22911`, counts `{"complete": 7, "pending": 22903, "running": 1}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `914`, mentions `1374`, stories `1352`, publishedAt `2026-06-05T13:23:00.830627+00:00`.
- Website asset: generatedAt `05/06/2026 13:22 UTC`, stories `1432`, articles `1892`, targets `27`.
- Live results: latest `2026-06-05T13:26:11.149190+00:00`, count `60`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `290.87` MiB, VmHWM `682.38` MiB, limit `512` MiB.
- Disk: free `57148.13` MiB, DB `274.07` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.7, "status": 200}, "disk": {"elapsed": 0.28, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 2.46, "status": 200}, "live": {"elapsed": 0.37, "status": 200}, "memory": {"elapsed": 0.35, "status": 200}, "sqlite": {"elapsed": 0.64, "status": 200}, "status": {"elapsed": 3.91, "status": 200}, "targets": {"elapsed": 0.23, "status": 200}, "viewers": {"elapsed": 0.21, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-05T13:23:13.102574+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "G1 Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 270.23, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:22:43.388937+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "G1 Politica", "status": "complete", "candidatesSeen": 54, "candidatesTotal": 54, "articlesInserted": 21, "mentionsInserted": 26, "storiesTouched": 21, "rssBefore": 229.37, "rssAfter": 299.84, "error": ""}, {"at": "2026-06-05T13:19:54.472378+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "G1 Politica", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:54.320429+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "G1", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 229.37, "rssAfter": 229.37, "error": ""}, {"at": "2026-06-05T13:19:53.209167+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "G1", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:53.054730+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "Veja Rio", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 229.37, "rssAfter": 229.37, "error": ""}, {"at": "2026-06-05T13:19:52.904945+00:00", "event": "source_run_started", "target": "__all_targets__", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 229.37, "rssAfter": null, "error": ""}, {"at": "2026-06-05T13:19:52.744324+00:00", "event": "source_run_complete", "target": "__all_targets__", "source": "VEJA Cidades", "status": "complete", "candidatesSeen": 0, "candidatesTotal": 0, "articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0, "rssBefore": 231.46, "rssAfter": 231.37, "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 10:26:40 -03 - Playwright UI Contract Check

- Profile listed: `True`.
- Viewer login HTTP: `200`; `/api/targets` HTTP: `200`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Primary keys exact: `True`; default-checked exact: `True`.
- Primary keys: `["seguranca_presente", "programa_seguranca_presente", "operacao_seguranca_presente", "seguranca", "inseguranca", "crime", "criminalidade", "violencia", "assalto", "roubo", "furto", "medo", "policiamento", "patrulhamento", "percepcao_de_seguranca", "sensacao_de_seguranca", "reforco_no_policiamento", "ordem_publica"]`.
- Checked primary keys: `["seguranca_presente", "programa_seguranca_presente", "operacao_seguranca_presente", "seguranca", "inseguranca", "crime", "criminalidade", "violencia", "assalto", "roubo", "furto", "medo", "policiamento", "patrulhamento", "percepcao_de_seguranca", "sensacao_de_seguranca", "reforco_no_policiamento", "ordem_publica"]`.
- Secondary keys: `[]`; secondary empty `True`.
- Runner status: `Atualizando`.
- Browser errors/warnings: `[]`.
- Barriers: `[]`.

## 2026-06-05 10:30:10 -03 - Grouped Ledger Post-Deploy Confirmation

- Commit deployed: `80ca09b fix(jobs): group multi-target durable source runs`.
- Resume action: `/api/update/resume` used for job `0b36e332911a`; no duplicate full job started.
- Ledger migration confirmed: `source_run_ledger_migrated` emitted at `2026-06-05T13:19:34Z`.
- Current ledger shape confirmed by raw `/api/update/status`: `sourceRunTargetCounts={"__all_targets__": 22911}` and source type counts `{"rss": 18, "google_news": 1, "wordpress_api": 6, "internal_search": 6, "sitemap_daily": 22680, "vejario_archive": 100, "camara_archive": 100}`.
- Source-run events now include all 18 `target_keys` on grouped runs.
- Post-migration source evidence:
  - `G1 Politica`: `54` candidates, `21` articles, `26` mentions, `21` stories.
  - `G1 Rio`: `100` candidates, `44` articles, `65` mentions, `44` stories.
  - `Extra`: `10` candidates, `2` articles, `2` mentions, `2` stories.
  - `Estadao`: `20` candidates, `5` articles, `7` mentions, `5` stories.
  - `Agencia Brasil`: `3` candidates, `2` articles, `2` mentions, `2` stories.
- Monitor evidence: live results advanced from stale/old timestamps to `2026-06-05T13:26:11Z` and then `2026-06-05T13:28:59Z`; publishedAt advanced to `2026-06-05T13:29:15.876001Z`; website asset generatedAt advanced to `05/06/2026 13:22 UTC`.
- Health: no barriers, no repeated 5xx, SQLite quick_check `ok`, activeJobsCount `1`, viewer login ok, Playwright contract ok, RSS stayed around `270-305` MiB after grouped processing.
- Monitoring note: `/api/update/status` article/mention/story totals can oscillate during active source-runs because progress summaries mix recent `article_saved` events and job totals. For this recovery, source-run events, live-results timestamps, asset timestamps, and ledger counts are the reliable per-cycle evidence.
- Current next action: continue monitoring Google News and later WordPress/internal-search grouped rows; stop blind waiting if a grouped source stalls without article/live/source movement or if memory/5xx/disk barriers appear.

## 2026-06-05 10:35:36 -03 - Google News Stall and Timeout Patch

- Barrier: grouped `Google News` source-run started at `2026-06-05T13:29:33Z` and remained `running` for several minutes with `23` candidates seen/total, no live-results movement, no source-run completion, and memory around `305-308` MiB.
- Impact: queue blocked before WordPress/internal-search/sitemap grouped coverage.
- Local diagnosis: `pipeline/ingest.py` prefetch path waited on `future.result()` without its own timeout. Even though `fetch_url()` has a hard timeout, a stuck or exhausted fetch pool can leave the source-run waiting on a prefetch future.
- Local fix prepared: `future.result(timeout=request_timeout + 5)` with cancellation and `article_prefetch hard timeout` error propagation.
- Tests: `.venv_playwright/bin/python -m pytest tests/test_targets_jobs.py tests/test_voluntarios_backfill_operator.py -q` passed with `82 passed`.
- Next action: deploy the timeout patch, let production interrupt cleanly, resume only job `0b36e332911a`, and verify Google News either completes or fails resumably instead of blocking the full queue.

## 2026-06-05 10:55:46 -03 - Google Redirect Skip Patch

- Post-timeout deploy result: grouped ledger remigrated successfully and RSS source-runs progressed again, but grouped `Google News` stalled again after reaching `3` candidates seen/total.
- Diagnosis refinement: unresolved `news.google.com` redirect candidates are still entering full article fetch during ingestion. The source-run can block even with prefetch future timeouts because the direct Google redirect/full-fetch path remains expensive or stuck.
- Local fix prepared: `process_candidates()` now skips unresolved Google News redirect URLs with reason `google_redirect_unresolved` instead of attempting full fetch. Direct outlet links already resolved by `collect_google_news()` remain eligible.
- Tests: `.venv_playwright/bin/python -m pytest tests/test_targets_jobs.py tests/test_voluntarios_backfill_operator.py -q` passed with `83 passed`.
- Next action: deploy this skip patch, resume only job `0b36e332911a`, verify grouped ledger remigration, and confirm Google News completes quickly or advances to WordPress.

## 2026-06-05 11:16:53 -03 - Backend Review: Google News Preview-Only Patch

- User concern: website/news count remains implausibly low for 18 broad public-security targets over `2014-01-01` to `2026-06-02`.
- Baseline evidence before patch: production job `0b36e332911a` is `running`; grouped ledger is active with `sourceRunTargetCounts={"__all_targets__": 22911}`; source type counts are `{"rss": 18, "google_news": 1, "wordpress_api": 6, "internal_search": 6, "sitemap_daily": 22680, "vejario_archive": 100, "camara_archive": 100}`; only `18` source-runs complete, `1` running, `22892` pending.
- Current barrier: grouped `Google News` is stuck at `3/3` candidates and prevents the job from reaching WordPress, internal search, and the daily sitemap source-runs where the long-range volume should appear.
- Backend diagnosis: for `google_news`, the ingestion layer should not perform full article fetch/archive as part of this grouped backfill. If the Google preview title/snippet already matches a target, save from the preview; if it does not match, skip with an explicit reason. Full fetches here are the blocking behavior, not useful evidence of low volume.
- Local fix prepared: `process_candidates()` now skips non-matching Google News previews with reason `google_news_preview_no_match` and disables archive full-text fetches for `candidate_source_type == "google_news"`.
- Tests: `.venv_playwright/bin/python -m pytest tests/test_targets_jobs.py tests/test_voluntarios_backfill_operator.py -q` passed with `84 passed`.
- Next action: deploy the preview-only Google News patch, wait for production to interrupt cleanly, resume only job `0b36e332911a`, then verify Google News completes and the queue advances beyond the first `19` grouped source-runs.

## 2026-06-05 10:40:45 -03 - Resumed Same Production Job

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `805`, stories `301`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `05/06/2026 13:29 UTC`, stories `1437`, articles `1894`, targets `27`.
- Live results: latest `2026-06-03T16:51:31.525271+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `185.14` MiB, VmHWM `676.89` MiB, limit `512` MiB.
- Disk: free `55076.6` MiB, DB `254.17` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 0.53, "status": 200}, "disk": {"elapsed": 0.23, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 1.4, "status": 200}, "live": {"elapsed": 0.45, "status": 200}, "memory": {"elapsed": 0.23, "status": 200}, "sqlite": {"elapsed": 1.01, "status": 200}, "status": {"elapsed": 1.46, "status": 200}, "targets": {"elapsed": 0.22, "status": 200}, "viewers": {"elapsed": 0.22, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 239.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "candidatesSeen": 25, "candidatesTotal": 25, "articlesInserted": 4, "mentionsInserted": 4, "storiesTouched": 4, "rssBefore": 239.91, "rssAfter": 239.91, "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 239.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "candidatesSeen": 25, "candidatesTotal": 25, "articlesInserted": 10, "mentionsInserted": 10, "storiesTouched": 10, "rssBefore": 239.91, "rssAfter": 239.91, "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 239.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "candidatesSeen": 24, "candidatesTotal": 24, "articlesInserted": 8, "mentionsInserted": 8, "storiesTouched": 8, "rssBefore": 239.91, "rssAfter": 239.91, "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 239.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:36:25.606763+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "pending", "candidatesSeen": 25, "candidatesTotal": 25, "articlesInserted": 4, "mentionsInserted": 4, "storiesTouched": 4, "rssBefore": 239.91, "rssAfter": 239.91, "error": ""}]`.
- Barriers: `[]`.

## 2026-06-05 11:02:05 -03 - Resumed Same Production Job

- Job `0b36e332911a` status `running`, coverage `pending`, resumeAvailable `False`.
- Contract: date `2014-01-01` to `2026-06-02`, collector `all`, preset `custom`, exact 18 keys `True`.
- Source ledger: total `22912`, counts `{"complete": 23, "pending": 22889}`.
- Current target/source: `n/a` / `n/a`.
- Totals/status fields: articles `None`, mentions `805`, stories `301`, publishedAt `2026-06-03T01:40:39.522579+00:00`.
- Website asset: generatedAt `05/06/2026 13:50 UTC`, stories `1437`, articles `1895`, targets `27`.
- Live results: latest `2026-06-03T16:51:31.525271+00:00`, count `51`.
- Viewer profile/login: login ok `True`, profile `{'found': True, 'label': 'Voluntários-Lab-Políticas-Públicas', 'hasPassword': True, 'targetKeysCount': 18, 'defaultTargetsCount': 18, 'missing': [], 'extra': [], 'defaultsMissing': [], 'defaultsExtra': [], 'targetKeys': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica'], 'defaultTargets': ['seguranca_presente', 'programa_seguranca_presente', 'operacao_seguranca_presente', 'seguranca', 'inseguranca', 'crime', 'criminalidade', 'violencia', 'assalto', 'roubo', 'furto', 'medo', 'policiamento', 'patrulhamento', 'percepcao_de_seguranca', 'sensacao_de_seguranca', 'reforco_no_policiamento', 'ordem_publica']}`.
- Target contract: `{'count': 18, 'missing': [], 'extra': [], 'primaryExact': True}`.
- Memory: VmRSS `197.49` MiB, VmHWM `682.95` MiB, limit `512` MiB.
- Disk: free `59091.17` MiB, DB `254.17` MiB.
- Storage diagnostic: enabled `False`, reason `supabase_env_not_available_locally`.
- HTTP timings/status: `{"asset": {"elapsed": 1.18, "status": 200}, "disk": {"elapsed": 0.61, "status": 200}, "events": {"elapsed": 0.23, "status": 200}, "health": {"elapsed": 1.84, "status": 200}, "live": {"elapsed": 0.49, "status": 200}, "memory": {"elapsed": 0.27, "status": 200}, "sqlite": {"elapsed": 2.0, "status": 200}, "status": {"elapsed": 1.99, "status": 200}, "targets": {"elapsed": 0.73, "status": 200}, "viewers": {"elapsed": 0.59, "status": 200}}`.
- Recent source events: `[{"at": "2026-06-03T01:41:53.755590+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 239.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:41:40.247251+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "candidatesSeen": 25, "candidatesTotal": 25, "articlesInserted": 4, "mentionsInserted": 4, "storiesTouched": 4, "rssBefore": 239.91, "rssAfter": 239.91, "error": ""}, {"at": "2026-06-03T01:40:52.964517+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 239.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:40:22.446931+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Veja Rio", "status": "pending", "candidatesSeen": 25, "candidatesTotal": 25, "articlesInserted": 10, "mentionsInserted": 10, "storiesTouched": 10, "rssBefore": 239.91, "rssAfter": 239.91, "error": ""}, {"at": "2026-06-03T01:39:08.444608+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Veja Rio", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 239.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:38:38.069488+00:00", "event": "source_run_complete", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "complete", "candidatesSeen": 24, "candidatesTotal": 24, "articlesInserted": 8, "mentionsInserted": 8, "storiesTouched": 8, "rssBefore": 239.91, "rssAfter": 239.91, "error": ""}, {"at": "2026-06-03T01:36:57.604497+00:00", "event": "source_run_started", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "running", "candidatesSeen": null, "candidatesTotal": null, "articlesInserted": null, "mentionsInserted": null, "storiesTouched": null, "rssBefore": 239.91, "rssAfter": null, "error": ""}, {"at": "2026-06-03T01:36:25.606763+00:00", "event": "source_run_checkpoint", "target": "seguranca_presente", "source": "Tribuna da Serra", "status": "pending", "candidatesSeen": 25, "candidatesTotal": 25, "articlesInserted": 4, "mentionsInserted": 4, "storiesTouched": 4, "rssBefore": 239.91, "rssAfter": 239.91, "error": ""}]`.
- Barriers: `[]`.
