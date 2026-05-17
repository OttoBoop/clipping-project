# Dependency Map - Segregation, Product, Rio Indicator

_Created 2026-05-18 by Atlas/Codex._

This map keeps the axes separate so future agents do not confuse market
research, economic methodology, product packaging, and access control.

## Axis 1 - Segregation And Login

This is the first dependency. Nothing sellable or methodologically clean exists
until the current app can show different scoped views without leaking data.

Required before anything else:

- logged-out users cannot access dashboard data or raw payloads;
- login creates a viewer profile;
- profile scope controls targets, stories, articles, raw texts, live results,
  classifications, and visible controls;
- operator/admin workflows remain available to Otavio;
- client profiles do not see operator-only target management unless the action
  is fully connected end to end.

## Axis 2 - Product Packaging For Clients

This depends on Axis 1. Once scoped views work, the product can be described and
sold.

Later questions for the loop to answer:

- What does a paid client receive: daily clipping, private dashboard, alerts,
  weekly summary, export, human classification, or all of these?
- What is the minimum operator burden Otavio can afford?
- What proof/demo should be shown to a politician or advisor?
- What pricing covers AI tooling, hosting, and maintenance?

## Axis 3 - Rio Economic Indicator

This depends on Axis 1 for clean project isolation, but it does not need to
block login.

Later methodology work:

- define economic dimensions for Rio;
- design search terms and exclusions carefully;
- separate person/entity monitoring from topic monitoring;
- validate sources and false positives;
- decide whether the indicator is a dashboard, score, narrative report, or
  internal research feed.

## Axis 4 - Market Research

This depends on having a credible product story from Axes 1 and 2. It can begin
as desk research, but it should not distract the first technical loop.

Research questions:

- Who already sells clipping/monitoring to municipal politicians?
- What do small political offices pay for media monitoring?
- Which pain is stronger: "do not miss mentions" or "understand agenda/topic
  movement"?
- Which demo best sells the tool without exposing another client's data?

## Axis 5 - Repos, Sites, Deploys

This is intentionally last. A new repo or GitHub Pages site is not the first
solution. The current Render/FastAPI app must prove scoped data first.

Only revisit separate repos/sites when one of these is true:

- a client needs a custom public brand page;
- deployment blast radius becomes unsafe;
- performance or storage requires separate services;
- contractual data isolation requires separate infrastructure.
