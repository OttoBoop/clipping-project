# First Client Onboarding Checklist

_Created 2026-05-19 by Atlas/Codex._

Use this before giving any external person access to the clipping product.

## Before The Sale Call

```text
choose demo mode from DEMO_PROFILE_STRATEGY.md
confirm static export is not being used as private access
confirm logged-out Render JSON/API checks return 401
confirm no Flavio/Shakira credentials will be shared
prepare short explanation of V1_DELIVERY_SCOPE.md
```

## Before Creating Access

Write down:

- client/prospect name;
- profile key;
- allowed target keys;
- update frequency;
- delivery format;
- pilot start/end date;
- who may receive the password;
- offboarding date or condition.

## Profile Setup

1. Add or review the profile in `data/viewer_profiles.json`.
2. Confirm allowed target keys are exactly the approved target list.
3. Do not use Flavio/Shakira/Rio profiles as a shortcut.
4. If the profile is only a demo, prefer `demo_cliente` with empty scope or a
   dedicated `prospect_<name>` profile.
5. Commit profile changes path-limited if any are needed.

## Password Setup

1. Generate a random password outside Git.
2. Update only the needed Render env var, merging with existing env.
3. Do not print the password in logs.
4. Store/share the password outside the repo.
5. After a one-off demo, rotate or remove access.

## Pre-Share Verification

Before sending a password:

```text
GET /healthz -> viewerAuthConfigured=true
GET /assets/clipping-data.json logged out -> 401
GET /assets/clipping-raw-texts.json logged out -> 401
profile login -> expected profile
profile targets -> only approved keys
profile raw texts -> only scoped article keys
viewer POST /api/targets -> 401/403
operator controls hidden
```

## Pilot Operation

During the pilot, log:

- each update run date;
- target/profile changes;
- time spent on QA;
- time spent on summary/export;
- false positives or missed items;
- support/password issues;
- buyer feedback.

## Offboarding

At the end of the pilot or if access should stop:

1. Rotate/remove the profile password in Render.
2. Remove or empty the prospect profile if it should not remain active.
3. Confirm old password no longer logs in.
4. Keep non-secret notes in `WORK_LOG.md`.
5. Do not leave unused client passwords active.

## Never Do

- `git add .`;
- commit passwords;
- send Flavio/Shakira credentials externally;
- rely on GitHub Pages/Wix/static export as private access;
- promise daily/realtime/custom work unless priced and written separately.
