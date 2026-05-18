# Deployment Environment - Password Segregation

_Created 2026-05-18 by Atlas/Codex._

This file records how the current FastAPI app should be configured for the
first password-gated product loop.

## Do Not Put Passwords In Git

Profile scopes can live in Git. Passwords must stay in environment variables.

## Required Environment Variables

```text
CLIPPING_SESSION_SECRET=<long random secret>
CLIPPING_ADMIN_PASSWORD=<operator password>
CLIPPING_VIEWER_PASSWORDS={"flavio":"...","shakira":"...","rio_economico":"...","demo_cliente":"..."}
```

`CLIPPING_VIEWER_PASSWORDS` may also use semicolon form:

```text
flavio=...;shakira=...;rio_economico=...;demo_cliente=...
```

## Optional Environment Variables

```text
CLIPPING_VIEWER_PROFILES=<json profile override>
CLIPPING_VIEWER_PROFILES_PATH=/absolute/path/to/viewer_profiles.json
CLIPPING_EMPTY_DEMO_PASSWORD=<public empty-demo password override>
CLIPPING_DISABLE_PUBLIC_EMPTY_DEMO=1
CLIPPING_ENABLE_PUBLIC_EMPTY_DEMO_WITH_REAL_VIEWERS=1
```

Use these only when Render/local operations need to override
`data/viewer_profiles.json`.

## Public Empty Demo Workaround

When `CLIPPING_VIEWER_PASSWORDS` is not configured, the app allows a limited
viewer login for `demo_cliente` with password:

```text
demo-cliente
```

This is not a private client password. It is a live-production workaround for
proving the viewer login/session/readonly/scoped-empty path without exposing
Flavio, Shakira, Rio, or client data.

Safety rules:

- it only works while real viewer passwords are missing;
- it only works if `demo_cliente` has no target keys;
- it can be disabled with `CLIPPING_DISABLE_PUBLIC_EMPTY_DEMO=1`;
- it can be re-enabled alongside real viewers only with
  `CLIPPING_ENABLE_PUBLIC_EMPTY_DEMO_WITH_REAL_VIEWERS=1`;
- it does not satisfy the production requirement for real
  `CLIPPING_VIEWER_PASSWORDS`.

## Profile Scope File

The default reviewable scope file is:

```text
data/viewer_profiles.json
```

This file contains no passwords. It controls which target keys each viewer
profile may see.

## Current Product Surface

Private client access should go through:

```text
FastAPI / -> /api/login -> session cookie -> scoped /assets/*.json -> scoped /api/* reads
```

Do not treat static exports, GitHub Pages, Wix bundles, or archived report HTML
as private client access.

## Local Smoke Command

```bash
CLIPPING_ADMIN_PASSWORD='test-password' \
CLIPPING_SESSION_SECRET='local-segmentation-secret' \
CLIPPING_VIEWER_PASSWORDS='{"flavio":"viewer-flavio","shakira":"viewer-shakira","rio_economico":"viewer-rio","demo_cliente":"viewer-demo"}' \
.venv_playwright/bin/python -m uvicorn web_app.app:app --host 127.0.0.1 --port 8765
```

Expected local smoke:

- logged-out `/assets/clipping-data.json` returns `401`;
- viewer login returns role `viewer` and the expected profile;
- viewer payload contains only allowed targets;
- direct API widening attempts return empty scoped results;
- admin writes require CSRF.
