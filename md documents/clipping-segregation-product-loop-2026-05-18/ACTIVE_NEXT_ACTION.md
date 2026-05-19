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
- Viewer profile scope checker now validates `data/viewer_profiles.json`
  against `data/targets.json`, keeping `rio_economico` topic-only and
  `demo_cliente` empty.
- Static export policy: static bundles are not the private paid-client surface.
- Deployment/env memory for Render/local setup.
- Playwright browser smoke for logged-out, Flavio viewer, Shakira viewer, and
  admin.
- First sellable package draft.
- Sellable demo readiness review for what can be shown safely without external
  password sharing or overpromising.
- Buyer quote tracker readiness/no-fabrication rule for the first real
  prospect conversation.
- Rio economic indicator methodology track.
- Render production checklist.
- Authenticated Render smoke runbook/script for repeating viewer/admin proof
  when passwords are available outside Git.
- Authenticated Render smoke script now has an explicit opt-in disposable admin
  mutation path using an auto-archived `Atlas Teste Smoke <timestamp>` target.
- Authenticated Render smoke script now supports a local credentials file
  outside Git and fails partial proof when the expected viewer profile set is
  incomplete.
- Market research plan.
- Initial sourced market research notes.
- Political/communications competitor pass.
- Buyer interview guide.
- Demo script and buyer assumptions.
- Dirty worktree / commit-boundary review.
- Product loop operating protocol.
- Static boundary evidence.
- Static data boundary review now proves Render does not serve raw `data/`
  artifacts or legacy root JSON as the private product surface.
- Rio economic isolation decision.
- Sellable package readiness gate.
- Operator cost discipline guardrail.
- System review status snapshot for 2026-05-19.
- System review status snapshot for 2026-05-20 after Rio panel, operations,
  demo-readiness, buyer-tracker, and Rio manual-review-queue deploys.
- Target management no-fake-UI review snapshot for 2026-05-18.
- Target management live logged-out mutation smoke now proves direct create,
  edit, archive, and restore calls return `admin_login_required`.
- Render env change safety runbook for password/profile operations.
- Render operations review snapshot for service metadata, live health gate, and
  password rotation/offboarding boundaries.
- Rio economic ingestion architecture decision: do not flatten Rio into a plain
  target row; preserve query families, exclusions, date quality, and clusters.
- V1 add-on menu/boundaries for avoiding unlimited low-paid service scope.
- V1 pilot operating ledger now explicitly records zero measured runs and
  blocks final price until real operator-time and buyer evidence exist.
- V1 pilot ledger validation helper now prevents template rows or guessed time
  from counting as pricing evidence.
- Buyer quote tracker validation helper now prevents template rows or guessed
  demo reactions from counting as pricing evidence.
- Scoped Rio economic topic-report endpoint at `/api/reports/rio-economic-topic`
  with Rio/admin-only access and no target-row creation.
- Rio economic manual approval policy v0 for `near_date` and research-only
  stories before any indicator count or chart.
- Rio economic manual approval sidecar and regenerated topic report with
  `manual_approval_status_counts`.
- Rio economic manual approval validation now blocks unknown approval statuses
  and approved-current-period promotions without source/date evidence.
- Rio economic manual approval checker now validates the sidecar, generated
  topic report, and operator queue counts together before any manual promotion
  can be treated as real.
- Rio economic operator template now documents the exact sidecar fields and
  row-11 review shape without approving the row.
- Rio economic manual review queue for the eight `not_reviewed` stories,
  keeping `approved_promotions=0`.
- Rio-only read-only UI decision and first dashboard panel backed by scoped
  `/api/reports/rio-economic-topic`.
- Rio UI no-fake-approval static test now forbids approval/publish/add
  controls and target-write calls in the Rio panel path.

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
   a non-secret authenticated smoke helper now exists, but running it still
   requires viewer/admin passwords outside this shell; it now supports
   `--credentials-file /tmp/clipping-render-smoke.env` and defaults to
   expecting `flavio`, `shakira`, and `rio_economico` so partial runs are not
   mistaken for full proof;
   static data boundary review now also proves raw `data/` files are not the
   public private-client surface;
   a profile-scope checker now also proves the non-secret scope file does not
   reference unknown ordinary targets and does not accidentally add Rio as a
   production target row;
3. keep target-management no-fake-UI review fresh; a 2026-05-18 code/docs
   pass exists and logged-out live mutation calls now reject with
   `admin_login_required`, but positive admin CSRF/target-management smoke on
   Render still needs operator credentials and explicit mutation approval; the
   helper now has a disposable auto-archived target path for that proof;
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
   from the first 10 canonical checks; the extended 20-row canonical pass now
   feeds a cluster-aware topic report with 11 current-period stories, 1 manual
   review story, 4 research-only stories, and 9 still requiring canonical
   checks; the full 31-row canonical topic report now has 17 current-period
   stories, 1 manual-review story, 7 research-only stories, and no remaining
   canonical-check-required stories for the v4 sample; a read-only Rio panel
   now exists behind the scoped report endpoint; next Rio step is fresh
   production scoping proof, live positive proof for
   `/api/reports/rio-economic-topic`, and any real manual approvals recorded in
   the sidecar before promotion; a manual review queue now exists and says row
   11 is the first candidate while all eight non-automatic rows remain
   unpromoted; the Rio UI remains read-only and the static test now blocks
   fake approval/publish/add controls; the report builder now rejects fake
   manual promotions and emits effective `indicator_policy_counts` so future
   approvals cannot be displayed as text without changing the effective count;
   a dedicated checker now proves the manual sidecar rows match the report's
   non-automatic rows and the operator queue's current-decision counts;
5. convert the live proof into a sellable demo script without exposing secrets;
   demo/prospect strategy now exists; V1 pilot scope and delivery-format
   decision now exist; demo script is now tied to the V1 offer without exposing
   secrets or promising custom work; political competitor desk-research pass
   now exists; buyer interview guide now exists; next packaging step is live
   buyer/quote validation with a real prospect; dedicated prospect-profile
   setup checklist and buyer quote validation tracker now exist for serious
   hands-on access and pricing evidence capture; V1 add-on menu now separates
   base pilot from frequency, adversary, custom source, report-format,
   classification, crisis, and Rio methodology add-ons; sellable demo readiness
   review now says operator screen-share is safe, hands-on external password
   needs dedicated profile/setup/offboarding, and Rio is only a read-only
   methodology preview; buyer quote tracker now records zero real
   conversations and the minimum fields required before any quote row counts;
   a validation helper now checks real dated buyer rows, demo-reaction markers,
   and pilot ledger counts before final price can be treated as decided;
6. review costs, password rotation, and operations;
   first-client onboarding/offboarding checklist now exists; V1 pilot operating
   ledger now exists for measuring update time, weekly summary time, support,
   false positives, missed items, and scope creep before final pricing, and now
   explicitly records that no measured pilot run exists yet; a validation
   helper now checks that ledger counts match real rows before pricing; Render
   env change safety runbook now exists for password/profile operations without
   full-env replacement or secret leakage; Render operations review now records
   the live service branch/auto-deploy facts and non-secret rotation checklist;
7. then re-read the docs and choose the next weak axis.

If `viewerAuthConfigured=false` returns, treat it as a regression and re-check
Render env configuration. Do not rotate or publish viewer passwords in docs.

Use `SYSTEM_REVIEW_STATUS_2026-05-20.md` as the current proof/blocker snapshot;
it now reflects live commit `c879432`.

## Do Not Do Next

- Do not create a new repo or GitHub Pages site.
- Do not turn static exports into the private client surface.
- Do not move Shakira/debug, target-repair, or live-source failure work into
  this loop.
- Do not commit inherited dirty files or use `git add .`.
