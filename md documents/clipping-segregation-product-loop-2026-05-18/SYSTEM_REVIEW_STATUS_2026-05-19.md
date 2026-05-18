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
viewerAuthConfigured=true
demoViewerConfigured=false
missingConfig=[]
```

Meaning:

- logged-out users no longer receive private Render dashboard data;
- direct private JSON fetches are blocked;
- direct private API reads are blocked;
- `/index.html` does not bypass the FastAPI login surface;
- the deployed JS includes viewer/admin control markers.
- Render now has real viewer-password configuration without committing secrets.

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

## Production Authenticated Segregation - Proven

Checked on the live Render service after `140a1f9` went live:

```text
logged-out private payload/API reads -> 401
flavio login -> role=viewer profile=flavio
flavio scoped targets -> bernardo_rubiao, flavio_valle, pedro_angelito, pedro_duarte
flavio forbidden target shakira in live-results -> absent
shakira login -> role=viewer profile=shakira
shakira scoped targets -> shakira
shakira forbidden target flavio_valle in live-results -> absent
rio_economico login -> role=viewer profile=rio_economico
rio_economico scoped targets/stories/articles/raw -> empty isolated profile
viewer POST /api/targets -> 401
viewer UI -> only Base atual tab visible
viewer UI -> add/manage target controls hidden
viewer UI -> classification editors absent
shakira viewer filter -> direct Shakira chip, no secondary-target drawer
```

Meaning:

- the first real paid-client segregation path is live, not only local;
- direct query params did not widen viewer scope;
- Rio economic exists as a separate profile without polluting Flavio/Shakira;
- raw-text payloads did not expose keys outside the scoped articles checked;
- viewer profiles cannot use target-management writes.
- visible viewer UI does not expose fake/admin-only target or classification
  actions in the checked profiles.
- single-target viewer profiles no longer look like secondary-target clutter.

Remaining production gap:

- positive admin login/CSRF was not tested because the operator admin password
  was not used or rotated during this loop.

## Empty Demo Workaround

The app has a public empty-demo viewer fallback for production verification
only while real viewer passwords are absent:

```text
password=demo-cliente -> role=viewer profile=demo_cliente
```

This path is intentionally limited:

- only enabled when real `CLIPPING_VIEWER_PASSWORDS` are absent;
- only enabled while `demo_cliente` has no target keys;
- returns an empty scoped payload and empty raw texts;
- proves viewer session/readonly/scoped-empty behavior, not real client data.

Current production state:

```text
demoViewerConfigured=false
```

The fallback is disabled because real viewer passwords are configured.

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

Next cycle should not re-litigate the missing viewer secret unless `/healthz`
regresses. Continue from the checklist items that remain weak:

```text
client UI fake-action audit -> target management no-fake-UI review ->
admin positive CSRF check with operator credentials when available ->
Rio economic target/methodology review
```
