# System Review Status - 2026-05-19

_Derived from `SYSTEM_REVIEW_CHECKLIST.md`. This is a status snapshot, not a
replacement for the checklist._

## Live Render - Proven

Checked on `https://clipping-project.onrender.com/`:

```text
GET / -> 200 login page
GET /index.html -> 404
GET /assets/clipping-data.json -> 401 viewer_login_required
GET /assets/clipping-raw-texts.json -> 401 viewer_login_required
GET /api/update/status -> 401 viewer_login_required
GET /api/update/live-results?scope=base&limit=240 -> 401 viewer_login_required
GET /api/targets -> 401 viewer_login_required
GET /api/classifications -> 401 viewer_login_required
GET /api/csrf -> 401 viewer_login_required
```

Health:

```text
loginConfigured=true
viewerProfilesConfigured=true
viewerAuthConfigured=false
```

Meaning:

- logged-out users no longer receive private Render dashboard data;
- direct private JSON fetches are blocked;
- direct private API reads are blocked;
- `/index.html` does not bypass the FastAPI login surface;
- the deployed JS includes viewer/admin control markers.

## Local Authenticated Contracts - Proven

Focused tests:

```text
7 passed
```

Covered:

- scoped dashboard payload;
- scoped raw texts;
- reviewable viewer-profile config;
- viewer readonly shell before payload load;
- direct API widening blocked for viewers;
- viewer write/admin actions rejected;
- admin CSRF still required;
- targets API scoped by login;
- hosted dashboard same-origin API polling after login.

Local browser smoke:

```text
viewer shakira -> body.viewer-readonly
run/progress tabs hidden
base tab visible
add-target hidden
manage-targets hidden
only scoped/empty profile data shown
```

## Production Blocked

Not yet proven on Render:

- viewer login returns role/profile;
- Flavio viewer returns only Flavio-approved targets;
- Shakira viewer excludes Flavio/Rio/client data;
- Rio economic profile exists as a separate live view;
- live raw texts are scoped for a viewer;
- viewer cannot widen live-results by query param in production;
- admin login/CSRF behavior in production.

Current blocker:

```text
Render missing CLIPPING_VIEWER_PASSWORDS
```

The code, docs, and `render.yaml` now declare the variable, but `/healthz`
still reports `viewerAuthConfigured=false`.

## Static Boundary

GitHub Pages still serves static files:

```text
https://ottoboop.github.io/clipping-project/                              200
https://ottoboop.github.io/clipping-project/assets/clipping-data.json      200
https://ottoboop.github.io/clipping-project/assets/clipping-raw-texts.json 200
```

Meaning: GitHub Pages/Wix/static exports must not be used as private client
access.

## Next Review

After `CLIPPING_VIEWER_PASSWORDS` exists on Render, run the full production
viewer checklist before calling Axis 1 complete:

```text
login/profile -> scoped data -> forbidden target absent -> raw text absent ->
direct API cannot widen -> viewer write rejected -> admin CSRF works
```
