# System Review Status - 2026-05-20

_Derived from `SYSTEM_REVIEW_CHECKLIST.md`, recent Render deploys, and
`WORK_LOG.md`. This is a status snapshot, not a replacement for the checklist._

## Latest Live Render Snapshot

Current live commit checked:

```text
6c90470 tools: guard Rio manual approval artifacts
deploy dep-d86ulqrtqb8s73djh4s0 -> live
finishedAt=2026-05-20T17:11:46.323819Z
url https://clipping-project.onrender.com/
```

Logged-out production smoke:

```text
GET /healthz -> 200
loginConfigured=true
viewerAuthConfigured=true
viewerProfilesConfigured=true
demoViewerConfigured=false
missingConfig=[]
GET / -> 200 login page
GET /api/reports/rio-economic-topic -> 401 viewer_login_required
GET /assets/clipping-data.json -> 401 viewer_login_required
GET /assets/clipping-raw-texts.json -> 401 viewer_login_required
GET /api/update/live-results?scope=base&limit=240 -> 401 viewer_login_required
GET /api/targets -> 401 viewer_login_required
GET /api/classifications -> 401 viewer_login_required
GET /api/csrf -> 401 viewer_login_required
GET /api/update/status -> 401 viewer_login_required
GET /api/categories -> 401 viewer_login_required
GET /data/targets.json -> 404 Not Found
GET /data/viewer_profiles.json -> 404 Not Found
GET /data/reports/rio_economic_topic_report_20260519T142621Z.json -> 404 Not Found
GET /clipping-data.json -> 404 Not Found
```

Meaning:

- logged-out users do not receive dashboard data, raw texts, Rio report data,
  targets, classifications, live results, or CSRF tokens;
- `/` serves the login page without exposing private payloads;
- real viewer auth is configured on Render;
- public empty-demo fallback is disabled.

## Latest Deployed Product Changes

Since the previous status snapshot, the loop added and deployed:

```text
457343f tools: add Rio manual approval sidecar
287aa5a web: add scoped Rio economic report panel
e846ee1 docs: add Render operations review
3c20936 docs: add sellable demo readiness review
9906b21 docs: refresh system review status
6c5f10a docs: clarify buyer quote tracker readiness
118cb8e docs: add Rio manual review queue
8203c1a docs: refresh live system status
c0750bc docs: tighten pilot operating ledger
84d6483 docs: refresh target management rejection proof
6ea7ed4 test: guard Rio panel against fake approval UI
e6eef5c docs: refresh status after Rio UI guard
d6104e6 tools: add authenticated Render smoke helper
2ac51e3 docs: log authenticated smoke helper deploy
ef5d8e1 feat: guard Rio manual approval counts
0f23ef6 tools: add admin disposable target smoke
a8d47af tools: add pilot ledger pricing guard
ec52781 docs: refresh status after pilot ledger guard
575041b test: document static data boundary
ceb0179 tools: add buyer quote evidence guard
13489d5 docs: refresh status after buyer guard
6c90470 tools: guard Rio manual approval artifacts
```

Freshly proven after deploy:

- logged-out privacy gate still passes after each deploy;
- static JS/CSS assets published the Rio read-only panel markers after
  `287aa5a`;
- Render service metadata confirms `master` auto-deploys to the live web
  service;
- operations docs now state `CLIPPING_VIEWER_PASSWORDS` changes must use
  `replace=false`;
- demo readiness now separates safe operator screen-share from hands-on
  external password access.
- buyer quote tracking now explicitly records zero real conversations, zero
  hands-on demo reactions, zero measured pilot runs, and no final price;
- Rio manual review now has a queue for the eight `not_reviewed` stories, with
  row 11 as the first review candidate and `approved_promotions=0`.
- target-management logged-out mutation calls return `admin_login_required` for
  direct create/edit/archive/restore attempts;
- the Rio UI static test now blocks fake approval/publish/add controls and
  target write calls in the Rio panel path.
- authenticated Render smoke can now be repeated from an operator shell without
  storing passwords in Git;
- Rio manual approvals now have a guarded status taxonomy and
  `approved_current_period` cannot regenerate a counted report without
  source/date evidence;
- Rio manual approval artifacts now have a checker that validates the sidecar,
  generated report counts, operator queue counts, and `target_row_approved`
  boundary together before any manual promotion is treated as usable;
- the Rio manual approval operator template now gives row 11 a review shape
  without approving it;
- the live JS now prefers `indicator_policy_counts` while falling back to the
  older date-quality counts.
- the authenticated smoke helper now has an explicit opt-in admin mutation path
  that creates only an `Atlas Teste Smoke <timestamp>` target and immediately
  archives it;
- the pilot ledger now has a checker that keeps template rows and guessed time
  from becoming pricing evidence.
- the buyer quote tracker now has a checker that keeps template rows and
  guessed demo reactions from becoming pricing evidence.
- Render static/data boundary probes still return `404` for raw `data/` files
  and the legacy root `clipping-data.json`, while scoped `/assets/*.json`
  still returns `401` when logged out after `6c90470`.

## Authenticated Production Proof

Prior production proof from `SYSTEM_REVIEW_STATUS_2026-05-19.md` remains the
last recorded positive viewer proof:

```text
flavio -> scoped targets only
shakira -> scoped to shakira
rio_economico -> isolated empty profile at that time
direct live-results forbidden target checks -> absent
viewer POST /api/targets -> 401
viewer UI fake-action audit -> add/manage/classification/run controls hidden
```

Current shell limitation:

```text
viewer/admin passwords are not available here
```

Therefore this snapshot does not claim fresh positive viewer/admin browser
proof after `a8d47af`. The fresh proof is logged-out production privacy plus
deployed static/read-only Rio UI markers. Positive authenticated proof must be
repeated by Otavio/operator or a session with the real viewer/admin passwords.

## Rio Economic Track

Current state:

- no production `rio_economico` target row has been added;
- latest topic report has `target_row_approved=false`;
- manual approval sidecar exists and promotes no rows;
- latest topic report with manual-approval guard:

```text
data/reports/rio_economic_topic_report_20260519T142621Z.json
indicator_policy_counts:
  count_current_period=17
  manual_review_before_counting=1
  research_only=7
manual_approval_status_counts:
  not_required=17
  not_reviewed=8
target_row_approved=false
```

- manual review queue exists for rows 1, 5, 11, 15, 19, 22, 25, and 26;
- row 11 is the first candidate for human review because it is `near_date`;
- `approved_promotions=0` and all eight non-automatic rows remain unpromoted;
- `approved_current_period` now requires reviewer, reviewed_at, rationale,
  canonical/source URL, and observed source date or date-trust evidence before
  the report builder will emit a promoted effective indicator count;
- `/api/reports/rio-economic-topic` is scoped to admin or `rio_economico`;
- logged-out access returns `401`;
- the UI panel is hidden by default and fetches the scoped endpoint only for
  admin or `rio_economico`;
- the panel is read-only and has no approval, target creation, update, or
  publish controls.
- the focused static test forbids `Adicionar`, `Aprovar`, `Publicar`,
  `<button`, `<form`, `apiPost(`, `apiPatch(`, and `/api/targets` inside the
  Rio panel path.
- live `/assets/clipping.js` includes `indicator_policy_counts` and
  `story.indicator_policy || story.date_quality_policy`.
- `tools/rio_economic_manual_approval_check.py` currently returns `ok=true`
  for the sidecar/report/queue set:

```text
story_count=25
sidecar_rows=[1, 5, 11, 15, 19, 22, 25, 26]
manual_approval_status_counts:
  not_required=17
  not_reviewed=8
indicator_policy_counts:
  count_current_period=17
  manual_review_before_counting=1
  research_only=7
approved_promotions=0
rows_remaining_not_reviewed=8
target_row_approved=false
```

Remaining Rio blockers:

- fresh positive `rio_economico` viewer proof on Render;
- any real manual approval must be written to the sidecar and the report
  regenerated before promotion;
- approval writes do not exist end to end, so the Rio panel must remain
  read-only;
- no manual approval has been made; the new guard only prevents fake promotion;
- no ordinary target-row ingestion until `RIO_ECONOMIC_PRODUCTION_GATE_V0.md`
  passes.

## Product / Demo State

Current decision:

```text
controlled operator demo: yes
hands-on external password: only after dedicated demo/prospect profile setup
first paid-client onboarding: needs real prospect scope and password rotation plan
Rio economic indicator as finished product: no
```

Safe sales posture:

- use Render/FastAPI as the private surface;
- use operator screen-share for real existing profile content unless a
  dedicated prospect profile exists;
- do not share Flavio/Shakira/Rio/admin credentials;
- do not use static exports as private access;
- do not point clients at raw `data/` artifacts; Render currently returns 404
  for those paths and the dashboard uses scoped `/assets` routes;
- keep V1 bounded to the pilot scope documented in `V1_DELIVERY_SCOPE.md`.
- run `tools/pilot_ledger_check.py` before treating operator-time rows as
  pricing evidence.

Current pilot ledger check:

```text
ok=true
measured_pilot_run_count=0
measured_weekly_summary_count=0
measured_support_issue_count=0
minimum_sustainable_monthly_price_decided=false
```

Current buyer quote tracker check:

```text
ok=true
real_buyer_conversation_count=0
hands_on_demo_reaction_count=0
measured_pilot_run_count=0
final_price_decided=false
```

## Operations State

Render facts:

```text
service=srv-d7p2p5beo5us739f9k40
branch=master
autoDeploy=yes
runtime=python
start=uvicorn web_app.app:app --host 0.0.0.0 --port $PORT
```

Password operations:

- no env var was changed in the latest operations review;
- do not use `replace=true` for routine password updates;
- do not log full `CLIPPING_VIEWER_PASSWORDS`;
- offboarding requires proving the old password no longer logs in, without
  recording the password value.

## Current Gaps

- positive admin CSRF/target-management smoke on Render still needs operator
  credentials and explicit approval before using the disposable mutation flag;
- positive viewer proof after latest deploys still needs viewer credentials;
- no real buyer quote/interview row exists in
  `BUYER_QUOTE_VALIDATION_TRACKER.md`;
- no measured pilot/update run exists in `V1_PILOT_OPERATING_LEDGER.md`;
- no final price has been selected because buyer quote evidence and measured
  operator cost are still empty;
- local toolchain in this shell lacks `pytest`, `fastapi`, `node`, and
  Playwright, so recent code checks used static/direct assertions plus Render
  deploy smoke.
- the current sandbox required escalation for git metadata writes, GitHub push,
  and Render curl checks after DNS/network restriction failures; the barriers
  were logged and worked around.

## Next Review

Continue from the weakest unblocked items:

```text
1. repeat authenticated Render proof when passwords are available;
2. keep logged-out production smoke fresh after every deploy;
3. record real buyer/demo quote data without inventing price;
4. record real pilot operator-time data before final pricing;
5. continue Rio manual-approval/methodology work without target-row pollution.
6. keep approval UI/actions hidden until approval writes are connected end to
   end.
7. re-open the long-term docs and choose the next weak unblocked item after
   this live `6c90470` smoke.
```
