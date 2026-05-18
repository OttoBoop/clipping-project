# First Sellable Package - Segmented Clipping Product

_Created 2026-05-18 by Atlas/Codex._

This is the first product packaging note after the local password/segregation
loop became testable.

Do not add billing, payment, a new repo, or a new site in this step. The goal is
to define what can be sold once the current FastAPI app is safely configured in
production.

## Product Promise

A political office gets a private clipping dashboard where it sees only its own
people, terms, stories, articles, raw texts, live results, and relevant filters.

The same backend can serve multiple clients, but each client gets a scoped
password and a clean readonly view.

## Current Readiness Status - 2026-05-19

Ready for a controlled live demo by Otavio/operator, not yet for broad public
buyer circulation.

Current live status:

- logged-out users are blocked from private Render dashboard data;
- static GitHub Pages is confirmed unsuitable as private access;
- Render has real `CLIPPING_VIEWER_PASSWORDS` configured without committing
  secrets;
- live Flavio and Shakira viewer profiles return scoped targets/data;
- live Rio economic profile exists as an empty isolated view;
- direct live-results widening checks did not expose forbidden target data;
- viewer UI hides update runner, target management, and classification editor
  controls;
- Shakira's single-target profile now shows a direct clean filter instead of a
  secondary-target drawer.

Allowed now:

- controlled live demo by Otavio/operator using Render viewer credentials;
- technical proof discussion with screenshots or notes;
- continued product/market planning;
- limited buyer discovery conversations that do not share another client's data
  or promise custom methodology.

Not allowed yet:

- sending a live client password broadly without an agreed demo profile and
  rotation plan;
- pitching GitHub Pages/Wix/static exports as private access;
- claiming the Rio economic indicator exists as a finished product;
- promising client self-service target creation;
- claiming admin/operator workflows were fully live-tested with the operator
  admin password in this loop.

## Minimum Paid Offer

Name: `Clipping privado monitorado`

The client receives:

- password-gated dashboard;
- scoped target list;
- grouped stories;
- article links and publication metadata;
- raw/full text only for articles in scope;
- basic sentiment/category chips if Otavio/admin classifies them;
- periodic manual/AI-assisted update run by the operator;
- simple export/screenshot/report prepared by the operator when needed.

## What The Client Does Not Get In V1

- target creation UI;
- update runner controls;
- classification editor;
- billing portal;
- separate GitHub repo;
- separate static site as the private access layer;
- guarantee of custom methodology beyond agreed targets/terms.

## Operator Responsibilities

Otavio/admin must:

- configure viewer password in env;
- review `data/viewer_profiles.json`;
- add/maintain target terms in `data/targets.json`;
- run/update the clipping pipeline;
- verify the profile view after changes;
- handle exports manually when necessary.

## Cost Discipline

The paid package should fund AI/tooling without creating a bespoke research job
for every client.

Avoid in V1:

- custom dashboards per client;
- custom frontend branches;
- unlimited new terms without review;
- live alerts requiring constant monitoring;
- high-frequency AI summaries for every article unless pricing covers it.

## First Demo Shape

Use the existing app, not a landing page:

1. show login;
2. enter the demo/client password;
3. show only that profile's targets;
4. open a story and raw text;
5. show that operator controls are absent;
6. explain that Otavio/admin controls updates behind the scenes.

## Pricing Questions For Later Market Research

Do not answer these from vibes. They need market research:

- What do small political offices already pay for clipping?
- Is the buyer the politician, chief of staff, campaign consultant, or press
  advisor?
- Which is more valuable: not missing mentions, having organized stories, or
  seeing topic movement?
- What update frequency is enough to charge while staying sustainable?

## V1 Acceptance Criteria

Before selling the first real client:

- production Render login is configured; **done for viewer profiles**
- client profile returns scoped data on Render; **done for Flavio/Shakira**
- logged-out JSON returns `401` on Render; **done**
- direct API widening returns no forbidden data; **done for checked targets**
- static exports are not presented as private access; **documented**
- client UI hides fake/admin-only actions; **done for checked viewer shells**
- Otavio can update the client's target terms without code surgery;
- WORK_LOG records the profile, tests, and known limitations.

Remaining before first paid client:

- create a dedicated demo/client profile that does not reuse Flavio/Shakira;
- define update frequency and included targets in writing;
- test the admin/operator target-update path with operator credentials;
- write password rotation and offboarding instructions;
- decide whether the first delivery is dashboard-only or dashboard plus manual
  WhatsApp/PDF summary.
