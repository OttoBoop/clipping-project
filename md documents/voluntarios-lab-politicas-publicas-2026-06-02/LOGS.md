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
