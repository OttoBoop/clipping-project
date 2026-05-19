# Prospect Profile Setup Checklist

_Created 2026-05-18 by Atlas/Codex._

Use this only when a real prospect is serious enough to receive hands-on access.
For casual sales calls, prefer operator screen-share or the empty privacy proof
demo from `DEMO_PROFILE_STRATEGY.md`.

Do not put passwords, private phone numbers, or secrets in this file.

## Before Creating A Prospect Profile

Confirm:

```text
buyer/prospect name is known
demo purpose is written
allowed targets are written
offboarding date/condition is written
static export will not be used as private access
Flavio/Shakira credentials will not be shared
```

## Profile Shape

```text
profile key: prospect_<short_name>
profile label:
allowed target keys:
disallowed target keys:
pilot/demo expiration:
password recipient:
operator owner:
```

Rules:

- keep the target list small;
- do not reuse `flavio`, `shakira`, or `rio_economico`;
- do not add broad topic targets just to make the demo look full;
- prefer screen-share if safe target content is not ready.

## Implementation Steps

1. Add or review `prospect_<short_name>` in `data/viewer_profiles.json`.
2. Confirm each allowed target already works end to end.
3. Generate the password outside Git.
4. Update Render `CLIPPING_VIEWER_PASSWORDS` with merge semantics.
5. Do not print or commit the password.
6. Wait for Render/deploy/env to settle.
7. Run pre-share verification.

## Pre-Share Verification

```text
GET /healthz -> viewerAuthConfigured=true
GET /assets/clipping-data.json logged out -> 401
GET /assets/clipping-raw-texts.json logged out -> 401
prospect login -> role=viewer profile=prospect_<short_name>
prospect /assets/clipping-data.json -> only approved targets
prospect /assets/clipping-raw-texts.json -> only approved article raw keys
prospect /api/update/live-results?target_key=<forbidden> -> no forbidden items
prospect POST /api/targets -> 401/403
viewer UI -> no add/manage/classification/update runner controls
```

## During Demo

Record non-secret notes:

```text
what the prospect opened first
which targets felt useful
which stories felt noisy
whether weekly summary is needed
whether price expectation implies add-ons
support/password friction
```

## Offboarding

Immediately after a one-off demo, unless access should continue:

```text
rotate/remove prospect password in Render
empty or remove prospect profile if no longer needed
confirm old password fails
log non-secret result in WORK_LOG.md
```

## Never Do

- do not use GitHub Pages/Wix/static exports as private access;
- do not share existing client passwords;
- do not include Rio economic material before `RIO_ECONOMIC_PRODUCTION_GATE_V0.md` passes;
- do not expose target-management/admin controls to the prospect;
- do not leave unused prospect passwords active.
