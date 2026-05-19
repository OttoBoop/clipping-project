# Render Production Checklist - Segregation

_Created 2026-05-18 by Atlas/Codex._

Use this after the password/segregation changes are deployed to Render.

Do not mark production segregation complete from local tests alone.

## Env Vars

Confirm in Render:

- `CLIPPING_SESSION_SECRET` exists and is long/random.
- `CLIPPING_ADMIN_PASSWORD` exists.
- `CLIPPING_VIEWER_PASSWORDS` exists.
- `CLIPPING_VIEWER_PASSWORDS` has at least one non-admin viewer profile.
- No password is committed to Git.

Optional:

- `CLIPPING_VIEWER_PROFILES`
- `CLIPPING_VIEWER_PROFILES_PATH`

Use optional profile env only if it intentionally overrides
`data/viewer_profiles.json`.

## Files

Confirm the deployed app includes:

- `data/viewer_profiles.json`
- `web_app/segmentation.py`
- current `assets/clipping.js`
- current `assets/clipping.css`

## Logged-Out Checks

Expected:

```text
GET / -> login page
GET /assets/clipping-data.json -> 401
GET /assets/clipping-raw-texts.json -> 401
GET /api/update/status -> 401
GET /api/reports/rio-economic-topic -> 401
GET /api/targets -> 401
GET /api/classifications -> 401
```

## Viewer Checks

For each configured viewer:

- login returns role `viewer` and the expected profile;
- `/` has `data-clipping-session-role="viewer"`;
- `/assets/clipping-data.json` returns only allowed targets;
- `/assets/clipping-raw-texts.json` returns only raw keys for allowed articles;
- `/api/update/live-results?target_key=<forbidden>` returns no forbidden items;
- `/api/reports/rio-economic-topic` returns `403` for non-Rio viewers and `200`
  only for `rio_economico` or admin;
- `/api/targets` returns only allowed target metadata;
- mutation attempts return `401` or `403`.

## Empty Demo Workaround Checks

If Render still reports `viewerAuthConfigured=false`, verify the public empty
demo workaround instead of stopping:

- `/healthz` reports `demoViewerConfigured=true`;
- login with `demo-cliente` returns role `viewer` and profile `demo_cliente`;
- `/` has `data-clipping-session-role="viewer"`;
- `/assets/clipping-data.json` returns no targets and no stories;
- `/assets/clipping-raw-texts.json` returns no raw texts;
- `/api/targets` returns no targets;
- mutation attempts return `401` or `403`.

This proves the viewer/session/readonly/scoped-empty path only. It does not
replace real Flavio/Shakira/Rio viewer verification.

## Admin Checks

- admin login returns role `admin`;
- `/` does not have `viewer-readonly`;
- operator controls are visible;
- `/api/csrf` returns a token;
- admin mutation without CSRF returns `403`;
- admin mutation with CSRF reaches the real operation.

## Static Export Boundary

Confirm the private client demo does not point to:

- GitHub Pages;
- Wix static bundle;
- `data/reports/...`;
- archived static HTML;
- raw static JSON files outside the FastAPI scoped `/assets` route.

## Log Requirement

After production smoke, append to `WORK_LOG.md`:

- Render URL checked;
- exact viewer profile checked;
- forbidden target tested;
- result of logged-out JSON checks;
- result of admin CSRF check;
- any profile with intentionally empty data.
