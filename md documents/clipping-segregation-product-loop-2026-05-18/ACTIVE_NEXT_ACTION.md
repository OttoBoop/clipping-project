# Active Next Action - Segregation Product Loop

_Last updated 2026-05-18 by Atlas/Codex._

Read `LONG_TERM_GOALS.md` first, then this file, then the bottom of
`WORK_LOG.md`.

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

Last non-live verification:

```text
244 passed, 13 deselected
```

Known unrelated live-source failures from full suite:

- Agenda do Poder WordPress returned 0 articles.
- CONIB internal search returned 0 articles.

## Next Product Step

Execute production verification after deploy:

1. confirm `CLIPPING_SESSION_SECRET`;
2. confirm admin password;
3. confirm viewer passwords;
4. confirm `data/viewer_profiles.json` is present;
5. confirm logged-out JSON returns `401` on Render;
6. confirm one real viewer profile returns scoped data.

If production deploy is not available, the next non-blocked task is deciding
whether to make a path-limited local commit for this product loop. Do not commit
until the inherited untracked `tests/test_sprint_regression_harness.py` question
is reviewed.

## Do Not Do Next

- Do not create a new repo or GitHub Pages site.
- Do not turn static exports into the private client surface.
- Do not move Shakira/debug, target-repair, or live-source failure work into
  this loop.
- Do not commit inherited dirty files or use `git add .`.
