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
- Political/communications competitor pass.
- Buyer interview guide.
- Demo script and buyer assumptions.
- Dirty worktree / commit-boundary review.
- Product loop operating protocol.
- Static boundary evidence.
- Rio economic isolation decision.
- Sellable package readiness gate.
- Operator cost discipline guardrail.
- System review status snapshot for 2026-05-19.
- Target management no-fake-UI review snapshot for 2026-05-18.
- Render env change safety runbook for password/profile operations.
- Rio economic ingestion architecture decision: do not flatten Rio into a plain
  target row; preserve query families, exclusions, date quality, and clusters.

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
viewerAuthConfigured=true
demoViewerConfigured=false
missingConfig=[]
```

Live authenticated viewer verification:

```text
flavio -> scoped to bernardo_rubiao, flavio_valle, pedro_angelito, pedro_duarte
shakira -> scoped to shakira
rio_economico -> empty isolated profile, no Flavio/Shakira contamination
forbidden live-results target_key checks -> absent
viewer POST /api/targets -> 401
viewer UI fake-action audit -> add/manage/classification/run controls hidden
shakira viewer filter -> direct shakira chip, no secondary-target drawer
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
2. keep real viewer profile proof verified after deploys;
3. keep target-management no-fake-UI review fresh; a 2026-05-18 code/docs
   pass exists, but positive admin CSRF/target-management smoke on Render still
   needs operator credentials;
4. continue the `RIO_ECONOMIC_VALIDATION_PLAN.md` path: offline report artifact
   exists; live Google News smoke now works with redirect resolution skipped;
   a 32-row live sample, 29-row revised sample, and 26-row title-exclusion
   sample exist; title-level labels exist; source/dimension refinement now
   exists; a v2 revised query file/sample now separates `municipal_finance`
   from `economic_development`; v3 query file/sample/review now exists with a
   strong title-level result; body/source review plan now exists; first
   body/source pass now reviewed 21 rows across all six dimensions; v4 query
   file/sample/review now removed the known row 15/27 false positives;
   canonical review helper and first 3-row canonical sample now exist; next Rio
   duplicate cluster review now exists; the dry-run format now has optional
   manual cluster fields; a 10-row canonical source/date pass now exists with
   eight same-day rows, one missing canonical date, and one date mismatch; next
   Rio date-quality policy now exists and the canonical helper now records
   status counts; a cluster-annotated v4 review now exists with 3 clusters and
   9 clustered rows; Rio production gate v0 now blocks target-row creation
   until live scoping proof, date-quality, cluster counting, source/body review,
   and narrow first-run planning are all satisfied; Rio ingestion architecture
   decision now blocks plain target-row implementation and prefers scoped
   topic/query reporting first; first topic-report artifact now collapses 31
   articles into 25 stories and marks only 6 stories as current-period countable
   from the first 10 canonical checks; next Rio step is fresh production scoping
   proof and/or extended canonical review before any production target row;
5. convert the live proof into a sellable demo script without exposing secrets;
   demo/prospect strategy now exists; V1 pilot scope and delivery-format
   decision now exist; demo script is now tied to the V1 offer without exposing
   secrets or promising custom work; political competitor desk-research pass
   now exists; buyer interview guide now exists; next packaging step is live
   buyer/quote validation with a real prospect; dedicated prospect-profile
   setup checklist and buyer quote validation tracker now exist for serious
   hands-on access and pricing evidence capture;
6. review costs, password rotation, and operations;
   first-client onboarding/offboarding checklist now exists; V1 pilot operating
   ledger now exists for measuring update time, weekly summary time, support,
   false positives, missed items, and scope creep before final pricing; Render
   env change safety runbook now exists for password/profile operations without
   full-env replacement or secret leakage;
7. then re-read the docs and choose the next weak axis.

If `viewerAuthConfigured=false` returns, treat it as a regression and re-check
Render env configuration. Do not rotate or publish viewer passwords in docs.

Use `SYSTEM_REVIEW_STATUS_2026-05-19.md` as the current proof/blocker snapshot.

## Do Not Do Next

- Do not create a new repo or GitHub Pages site.
- Do not turn static exports into the private client surface.
- Do not move Shakira/debug, target-repair, or live-source failure work into
  this loop.
- Do not commit inherited dirty files or use `git add .`.
