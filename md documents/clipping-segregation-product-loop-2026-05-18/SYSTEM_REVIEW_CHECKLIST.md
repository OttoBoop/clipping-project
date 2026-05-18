# System Review Checklist - Segregation And Login

_Created 2026-05-18 by Atlas/Codex._

Use this checklist before implementation and before closing any sprint touching
login, profile scope, target management, dashboard data, raw texts, live
results, classifications, or exports.

## Auth And Session Loop

- Logged-out users get a login surface, not dashboard data.
- Session cookies identify role and viewer profile.
- Admin sessions can operate the app.
- Viewer sessions cannot pass admin-only checks.
- Login failure does not reveal configured passwords or profiles.
- Health/status metadata does not expose secrets.
- Admin mutation routes require CSRF, not just a session cookie.

## Profile Scope Loop

- Each profile has explicit allowed target keys.
- Profile scopes are reviewable without storing passwords in Git.
- Unknown or empty scopes do not fall back to "show everything".
- Admin scope is intentionally full.
- A profile can exist before its target has matching articles.
- Direct query params cannot add targets outside the session scope.

## Dashboard Payload Loop

- `clipping-data.json` is served through an authenticated scoped route.
- `clipping-raw-texts.json` is served through an authenticated scoped route.
- `targets` and `defaultTargets` contain only allowed keys.
- Stories with no allowed article are removed.
- Articles have `targetKeys` reduced to allowed keys.
- Story stats and payload meta counts are recomputed after filtering.
- Raw text contains only keys referenced by allowed articles.

## API Loop

- `/api/targets` returns only allowed target metadata for viewer profiles.
- `/api/update/live-results` returns only allowed target items.
- `/api/classifications` returns only allowed target classifications.
- `/api/categories` is currently shared taxonomy; if future categories become
  client-specific, this endpoint must be scoped before exposing it to viewers.
- Mutating endpoints reject non-admin viewers.
- Mutating endpoints reject admin sessions without CSRF.
- Admin/operator workflows continue to work.

## Frontend Loop

- Viewer sessions receive a readonly shell before the JSON payload finishes
  loading.
- Viewer profiles do not see update runner controls unless those workflows are
  intentionally offered to clients.
- Viewer profiles do not see add/manage target controls unless target creation
  is fully scoped and connected.
- Viewer profiles do not see classification editors unless classification is a
  paid/product feature with permissions.
- Filter chips remain small and relevant to the active profile.
- Empty project profiles show a clean empty state, not another project's data.

## Verification Rule

For any segregation fix, close the loop with at least one test or smoke proving:

```text
login/profile -> fetch scoped data -> forbidden target absent from payload ->
raw text absent -> direct API cannot widen scope -> viewer write rejected ->
admin CSRF write still works
```

If a step cannot be verified, log why in `WORK_LOG.md` before moving on.

## Static Export Rule

- Static exports are not the private paid-client surface.
- FastAPI/Render client access must use server-side scoped payloads.
- Any future scoped static export must prove that its bundled
  `clipping-data.json` and `clipping-raw-texts.json` contain only that profile's
  allowed data.
