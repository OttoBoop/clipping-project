# Active Next Action - Segregation Product Loop

_Last updated 2026-05-19 by Atlas/Codex._

Read `LONG_TERM_GOALS.md` first, then `LOOP_OPERATING_PROTOCOL.md`, then this
file, then the bottom of `WORK_LOG.md`.

## Current Phase

Axis 1: functional password-gated segregation on the current FastAPI app.

## Completed In The Current Local Working Tree

- Viewer/admin login model.
- Server-side scoped `clipping-data.json`.
- Server-side scoped `clipping-raw-texts.json`.
- Server-side scoped targets, live results, classifications, and status.
- Admin-only mutations.
- CSRF on admin mutations.
- Viewer readonly shell before payload load.
- Reviewable profile scope file at `data/viewer_profiles.json`.
- Static export policy: static bundles are not the private paid-client surface.
- Deployment/env memory for Render/local setup.
- Playwright browser smoke for logged-out, Flavio viewer, Shakira viewer, and
  admin.
- First sellable package draft.
- Rio economic indicator methodology track.
- Render production checklist.
- Market research plan.
- Initial sourced market research notes.
- Demo script and buyer assumptions.
- Dirty worktree / commit-boundary review.

## Current Verification State

Live production verification:

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

Live `/healthz`:

```text
loginConfigured=true
viewerProfilesConfigured=true
viewerAuthConfigured=false
```

Last non-live verification before deploy:

```text
244 passed, 13 deselected
```

Known unrelated live-source failures from full suite:

- Agenda do Poder WordPress returned 0 articles.
- CONIB internal search returned 0 articles.

## Next Product Step

Continue the production loop. Current priority from the docs:

1. keep the logged-out privacy gate verified on Render;
2. get Render to recognize the required `CLIPPING_VIEWER_PASSWORDS` contract;
3. once the secret is configured, prove one viewer profile returns scoped data;
4. test forbidden target widening and raw-text leakage;
5. then re-read the docs and choose the next weak axis.

If `viewerAuthConfigured=false` remains true after deploy, do not stop. Log the
blocker and continue with the next unblocked review: deployed JS markers,
logged-out API gates, render/env docs, and local authenticated contract tests.

## Do Not Do Next

- Do not create a new repo or GitHub Pages site.
- Do not turn static exports into the private client surface.
- Do not move Shakira/debug, target-repair, or live-source failure work into
  this loop.
- Do not commit inherited dirty files or use `git add .`.
