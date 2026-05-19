# Logged-Out Render Smoke Runbook

_Created 2026-05-19 by Atlas/Codex during the segregation product loop._

Use this helper after every deploy that could affect auth, routes, static
assets, docs/status, or the Render release state.

## Command

```bash
python3 -B tools/logged_out_render_smoke.py
```

Optional:

```bash
python3 -B tools/logged_out_render_smoke.py --base-url https://clipping-project.onrender.com
python3 -B tools/logged_out_render_smoke.py --preflight-retries 3 --retry-delay-seconds 5
```

## What It Proves

The script checks the non-secret production boundary:

```text
/healthz -> configured login/viewer/profile state
/ -> login page markers
POST /api/login with a wrong password -> 401 invalid_password and no profile markers
/assets/clipping-data.json -> 401 viewer_login_required
/assets/clipping-raw-texts.json -> 401 viewer_login_required
/api/reports/rio-economic-topic -> 401 viewer_login_required
/api/update/status -> 401 viewer_login_required
/api/update/live-results?scope=base&limit=240 -> 401 viewer_login_required
/api/targets -> 401 viewer_login_required
/api/categories -> 401 viewer_login_required
/api/classifications -> 401 viewer_login_required
/api/csrf -> 401 viewer_login_required
/data/targets.json -> 404 Not Found
/data/viewer_profiles.json -> 404 Not Found
/data/reports/rio_economic_topic_report_20260519T142621Z.json -> 404 Not Found
/clipping-data.json -> 404 Not Found
POST /api/update/start -> 401 admin_login_required
POST /api/update/cancel -> 401 admin_login_required
POST /api/update/resume -> 401 admin_login_required
POST /api/export -> 401 admin_login_required
POST /api/targets -> 401 admin_login_required
PATCH /api/targets/shakira -> 401 admin_login_required
POST /api/targets/shakira/archive -> 401 admin_login_required
POST /api/targets/shakira/restore -> 401 admin_login_required
POST /api/categories -> 401 admin_login_required
POST /api/classifications -> 401 admin_login_required
```

This avoids treating a browser-visible login page as sufficient proof while
still keeping the check runnable without passwords. The mutation checks are
deliberately no-op rejections; they must not create, edit, archive, restore,
export, update, or classify anything while logged out.

## What It Does Not Prove

It does not replace `tools/authenticated_render_smoke.py`.

It cannot prove:

- Flavio/Shakira/Rio scoped positive payloads;
- viewer direct-query bypass resistance after login;
- admin CSRF positive flow;
- disposable target mutation cleanup;
- external prospect/demo profile behavior.

Use the authenticated helper when the required passwords are present outside
Git. Never paste passwords, cookies, or CSRF tokens into this file or
`WORK_LOG.md`.

## Known Environment Barrier

In sandboxed Codex shells, the first run may fail with DNS/network restriction.
If that happens, rerun with the approved escaped command rather than falling
back to unlogged manual curl-only evidence.

## Post-Deploy 503 Window

The helper runs a `/healthz` preflight before the full endpoint sweep. If
Render is still serving transient `502`, `503`, or `504` responses immediately
after deploy, the helper waits and retries before declaring the smoke failed.
If `/healthz` stays transient after the configured retries, the helper fails
fast with `preflight /healthz` instead of printing a misleading wall of
endpoint failures.
