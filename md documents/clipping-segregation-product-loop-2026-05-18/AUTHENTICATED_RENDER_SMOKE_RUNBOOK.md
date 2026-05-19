# Authenticated Render Smoke Runbook

_Created 2026-05-19 by Atlas/Codex._

This runbook turns the recurring "missing viewer/admin passwords in this shell"
blocker into a repeatable operator action. It must not store passwords in Git,
logs, screenshots, or commit messages.

## Script

```text
tools/authenticated_render_smoke.py
```

The script uses only Python standard library modules. It reads credentials from
environment variables and prints pass/fail evidence without printing password
values.

## Inputs

Set these outside Git:

```text
CLIPPING_SMOKE_BASE_URL=https://clipping-project.onrender.com
CLIPPING_SMOKE_VIEWER_PASSWORDS='flavio=...;shakira=...;rio_economico=...'
CLIPPING_SMOKE_ADMIN_PASSWORD='...'
```

`CLIPPING_SMOKE_VIEWER_PASSWORDS` may also be a JSON object:

```text
{"flavio":"...","shakira":"...","rio_economico":"..."}
```

Optional forbidden-target override:

```text
CLIPPING_SMOKE_FORBIDDEN_TARGETS='{"shakira":["flavio_valle","rio_economico"]}'
```

## Default Checks

For each viewer profile provided:

```text
POST /api/login returns role=viewer and expected profile
GET /assets/clipping-data.json returns no forbidden target keys
GET /assets/clipping-raw-texts.json contains no forbidden target markers
GET /api/targets returns no forbidden target keys
GET /api/update/live-results?target_key=<forbidden> returns no forbidden marker
GET /api/reports/rio-economic-topic returns 200 only for rio_economico, 403 for other viewers
POST /api/targets returns 401 or 403 for viewers
```

For admin, when `CLIPPING_SMOKE_ADMIN_PASSWORD` is provided:

```text
POST /api/login returns role=admin
GET /api/csrf returns a token
POST /api/targets without CSRF returns 403
```

By default the script does **not** create a target in production. A successful
CSRF-protected admin mutation still needs an explicit disposable-target cleanup
plan and operator approval before running.

## Run

```text
python3 tools/authenticated_render_smoke.py
```

Optional:

```text
python3 tools/authenticated_render_smoke.py --base-url https://clipping-project.onrender.com
```

## Evidence To Record

After running, copy only non-secret evidence into `WORK_LOG.md`:

```text
profiles checked
forbidden targets checked
status for clipping-data/raw-texts/targets/live-results/Rio endpoint
admin CSRF token present=true, but not the token value
viewer write rejection status
any failure or blocker
```

Never paste passwords, cookies, CSRF token values, or full private payloads into
the repo.

## Remaining Manual Gate

The script proves authenticated profile boundaries when credentials are
available. It does not replace:

```text
human review of visual cleanliness
operator approval before production target mutation
Rio manual approval source/date review
buyer/pilot evidence collection
```
