# Current Short-Term Loop - Corpus Rio Em Escala

_Superseded 2026-07-14. This loop is derived from the Rio corpus decision in
`LONG_TERM_GOALS.md`._

## Purpose

Keep the existing Render/FastAPI site and `rio_economico` profile while moving
`rio_city_corpus` to a durable, high-volume corpus subsystem. Do not start a
full historical backfill until the online funnel reports truthful URL, body,
date and coverage states.

The failures this loop addresses:

- query terms currently gate sitemap ingestion before article bodies are read;
- snippets, feed dates and unresolved URLs inflate success counters;
- collectors can stop early and still appear complete;
- a year-long job runs inside the web service and checkpoints the full SQLite;
- the Rio dashboard depends on a static export capped below the corpus target.

## Required System Connections To Prove

This loop is not accepted until it proves:

1. only admin and `rio_economico` can read Rio corpus APIs;
2. `POST /api/update/start` enqueues source windows in PostgreSQL instead of a
   daemon thread when scope/topic is `rio_economico/rio_city_corpus`;
3. workers claim rows with leases and `FOR UPDATE SKIP LOCKED`, retry safely,
   and never call partial/capped work complete;
4. source observations, fetch attempts, content hashes, dates, geography and
   dimensions are independently auditable;
5. city-focused archives are not keyword-filtered before body extraction;
6. the panel uses paginated Rio APIs and shows throughput, last progress,
   retries, caps and failures;
7. password change is proven live by change, relogin and restoration;
8. a recent day, a 2011 day and a 2011 month are monitored on Render before the
   2011 annual replay is accepted.

## Initial Technical Sprint

Implementation order:

- version the source registry and geographic evidence rules;
- add PostgreSQL schema, queue, worker and authenticated scheduler;
- add content-addressed gzip objects in the existing Supabase Storage;
- intercept only the Rio city topic, preserving the legacy profiles;
- expose paginated corpus, coverage, audit and truthful status endpoints;
- import existing Rio SQLite rows idempotently as `legacy_sqlite`;
- update the Rio panel and add focused contract tests;
- deploy, run the real password smoke and then run monitored canaries.

## Expected Commit Shape

Use path-limited commits that preserve inherited dirty work:

1. docs, source registry and evidence model;
2. PostgreSQL queue/storage/worker;
3. API and profile segregation;
4. panel and tests;
5. Render resources, canaries and work-log evidence.

Do not include inherited pycache, screenshots, moved legacy docs, or unrelated
dirty files.

## Stop Conditions

Do not start broad backfill if:

- PostgreSQL/worker/storage is not configured on Render;
- the password smoke cannot restore the original credential;
- any source window can record partial work as exhausted;
- final URL, body and page/API date cannot be sampled independently;
- no useful checkpoint has appeared for 15 minutes.

If blocked, record the exact source/window/state in `WORK_LOG.md` and preserve
all observations already collected.
