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
```

## What It Proves

The script checks the non-secret production boundary:

```text
/healthz -> configured login/viewer/profile state
/ -> login page markers
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
```

This avoids treating a browser-visible login page as sufficient proof while
still keeping the check runnable without passwords.

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
