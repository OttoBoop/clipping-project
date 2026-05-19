# Render Operations Review - 2026-05-18

_Created by Atlas/Codex as an operations snapshot for the segregation product
loop._

This file records non-secret production facts and the next operational checks
for password-gated client access. It does not contain passwords, full env var
values, buyer contacts, or private credentials.

## Current Render Service Facts

Observed through Render service metadata:

```text
service id: srv-d7p2p5beo5us739f9k40
service name: clipping-project
url: https://clipping-project.onrender.com
repo: https://github.com/OttoBoop/clipping-project
branch: master
autoDeploy: yes
autoDeployTrigger: commit
runtime: python
buildCommand: pip install -r requirements.txt
startCommand: uvicorn web_app.app:app --host 0.0.0.0 --port $PORT
region: virginia
instances: 1
previews: off
maintenanceMode: false
```

Current implication: pushing to `master` is a live-production operation. Every
path-limited commit that affects the app must be followed by Render deploy
polling and live smoke.

## Current Live Health Gate

Most recent logged-out smoke after `287aa5a`:

```text
GET /healthz -> 200
loginConfigured=true
viewerAuthConfigured=true
viewerProfilesConfigured=true
demoViewerConfigured=false
missingConfig=[]
GET /assets/clipping-data.json -> 401 viewer_login_required
GET /assets/clipping-raw-texts.json -> 401 viewer_login_required
GET /api/reports/rio-economic-topic -> 401 viewer_login_required
GET /api/targets -> 401 viewer_login_required
GET /api/classifications -> 401 viewer_login_required
GET /api/csrf -> 401 viewer_login_required
```

Current implication: the public empty-demo fallback is not active because real
viewer auth is configured. Do not document or share `demo-cliente` as a live
private password.

## Env Change Capability

Render MCP exposes a safe environment update path:

```text
update_environment_variables(serviceId, envVars, replace=false)
```

Use this only when Otavio/operator supplies the intended new secret value. The
loop must not invent, rotate, remove, or print production passwords on its own.

Required pattern:

```text
replace=false
envVars contains only the intended key(s)
never fetch/paste/log full CLIPPING_VIEWER_PASSWORDS
never log the new password value
```

For first-client or demo access, the expected key is usually:

```text
CLIPPING_VIEWER_PASSWORDS
```

The scope should remain in Git only if it is non-secret:

```text
data/viewer_profiles.json
```

## Rotation / Offboarding Checklist

Before changing access:

```text
profile_key written
change_type written: add / rotate / remove
scope impact reviewed in data/viewer_profiles.json
logged-out Render smoke passes
secret value available outside chat/log/git
```

After changing access:

```text
GET /healthz -> viewerAuthConfigured=true and missingConfig=[]
target profile login -> expected profile
target profile payload -> only approved targets/stories/raw texts
forbidden target_key live-results check -> empty
viewer write attempt -> 401 or 403
old password fails if rotating/offboarding
WORK_LOG.md records only non-secret evidence
```

## Hard Boundaries

- Do not use `replace=true` for routine password changes.
- Do not rotate Flavio/Shakira/Rio credentials just to create a sales demo.
- Do not share Flavio/Shakira/Rio credentials with prospects.
- Do not point prospects to GitHub Pages, Wix, archived static bundles, or raw
  report files as private access.
- Do not create a `rio_economico` production target row as an operational
  shortcut.
- Do not leave unused prospect passwords active after a one-off demo.

## Current Blockers

Authenticated production proof remains blocked in this shell because viewer and
admin passwords are not present and should not be guessed.

That blocker does not invalidate logged-out production proof. It means the next
operator-assisted checklist must include a real password session and record
only:

```text
profile key
expected scope
pass/fail
forbidden target checked
no secret values
```

## Next Operations Step

When Otavio has a real prospect or wants a demo credential:

1. Pick `demo_cliente` empty scope for privacy proof or
   `prospect_<short_name>` for a serious scoped demo.
2. Add/review non-secret profile scope in `data/viewer_profiles.json`.
3. Generate password outside Git/chat.
4. Update Render with `replace=false`.
5. Run the pre-share verification from `FIRST_CLIENT_ONBOARDING_CHECKLIST.md`.
6. Log non-secret evidence and an offboarding date in `WORK_LOG.md`.
