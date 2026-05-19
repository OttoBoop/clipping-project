# Target Management No-Fake-UI Review - 2026-05-18

This review comes from `SYSTEM_REVIEW_CHECKLIST.md` and the long-term rule that
visible client actions must either be connected end to end or hidden.

## Reviewed Surface

- `web_app/app.py`
- `web_app/segmentation.py`
- `assets/clipping.js`
- `tests/test_admin_ui.py`
- `tests/test_targets_jobs.py`

## Current Contract

Target management is an admin/operator feature, not a viewer feature.

Viewer profiles:

- receive `body.viewer-readonly` before payload load;
- hide run/update tabs except `Base atual`;
- hide add-target controls;
- hide manage-target controls;
- hide classification editors through `editorEnabled=false`;
- can call read APIs only through server-side profile scope;
- get `401 admin_login_required` for target/update/export/category/manual-story
  mutations.

Admin sessions:

- can call `/api/targets` and `/api/targets?include_archived=1`;
- can create secondary targets through `POST /api/targets`;
- can edit through `PATCH /api/targets/{target_key}`;
- can archive and restore through dedicated admin routes;
- must present CSRF for write routes;
- receive target mutation responses that include storage upload metadata and,
  where applicable, target-sync results.

## End-To-End Evidence In Code

Creation:

```text
UI addTargetForm -> POST /api/targets -> db_admin.create_secondary_target ->
record_target_sync(reason=target-created) -> refreshTargets ->
pollBaseLiveResults -> export snapshot test coverage
```

Edit:

```text
manage-target form -> PATCH /api/targets/{key} ->
db_admin.update_secondary_target -> record_target_sync(cleanup=True) ->
reloadTargetsAfterManagement
```

Archive:

```text
manage-target archive button -> POST /api/targets/{key}/archive ->
db_admin.archive_secondary_target -> hidden from active public targets
```

Restore:

```text
archived target restore button -> POST /api/targets/{key}/restore ->
db_admin.restore_secondary_target -> record_target_sync(reason=target-restored)
```

Existing tests prove the important local contracts:

- viewer cannot widen live results or write admin actions;
- targets API requires login;
- admin target create uploads target manifests;
- archived targets are listed only when requested;
- target mutations remain available while an update is active;
- creating a target backfills live base mentions and appears in the export
  filter;
- primary targets cannot be managed as secondary targets.

## Live Production Evidence

Logged-out live checks on Render currently prove:

```text
GET /api/targets -> 401 viewer_login_required
GET /api/csrf -> 401 viewer_login_required
GET /api/classifications -> 401 viewer_login_required
GET /assets/clipping-data.json -> 401 viewer_login_required
GET /assets/clipping-raw-texts.json -> 401 viewer_login_required
```

Additional logged-out mutation checks after deploy `c0750bc`:

```text
POST /api/targets -> 401 admin_login_required
PATCH /api/targets/loop_smoke_should_not_create -> 401 admin_login_required
POST /api/targets/loop_smoke_should_not_create/archive -> 401 admin_login_required
POST /api/targets/loop_smoke_should_not_create/restore -> 401 admin_login_required
```

These calls used a disposable key name but no authenticated session. They prove
that logged-out users cannot create, edit, archive, or restore targets by
calling the API directly. They do not replace the still-needed positive admin
CSRF smoke.

`/healthz` currently proves:

```text
loginConfigured=true
viewerAuthConfigured=true
viewerProfilesConfigured=true
demoViewerConfigured=false
missingConfig=[]
```

## Remaining Gaps

- Positive admin target-management smoke on Render is still blocked in this
  shell because the admin password/CSRF session is not available here.
- Admin-positive smoke must use a real admin session, fetch `/api/csrf`, then
  prove both missing-CSRF rejection and, only with explicit operator approval,
  successful CSRF-protected target mutation against an `Atlas Teste Smoke
  <timestamp>` disposable secondary target that remains archived.
- Positive authenticated viewer UI smoke on Render is also blocked without a
  viewer password, though earlier production proof in
  `SYSTEM_REVIEW_STATUS_2026-05-19.md` recorded viewer segregation when the
  secret was available.
- No production target should be created just to test this loop unless Otavio
  intentionally approves the disposable smoke flag in
  `tools/authenticated_render_smoke.py`.

## Decision

The client-side target-management UI is not fake for admin: the visible actions
have connected API, config, sync, live-results, export, validation, and tests.

For viewer/client profiles, the same UI is intentionally hidden and server
writes are rejected. This satisfies the no-fake-UI rule for the first sellable
segregated product, subject to future positive admin smoke on Render.

As of the latest live logged-out mutation smoke, the server-side rejection path
also blocks direct target-management writes with `admin_login_required`.

## Next Review

Return to `ACTIVE_NEXT_ACTION.md`. The next weak points are:

- positive admin CSRF/target-management verification on Render when credentials
  and explicit mutation approval are available;
- preserve the rule that the disposable production target path creates only an
  `Atlas Teste Smoke <timestamp>` row and immediately archives it;
- continued Rio economic production gate work without creating a target row;
- sellable demo/operations validation with real buyer evidence.
