# Rio Corpus Scale Architecture - 2026-07-14

## Decision

`rio_economico/rio_city_corpus` is no longer an indicator-first SQLite job.
It is a dedicated corpus subsystem behind the same authenticated site. Other
profiles continue on the legacy pipeline during migration.

## Durable Boundaries

- PostgreSQL stores jobs, leased source windows, canonical articles, URL
  aliases, collector observations, fetch attempts, geography evidence,
  dimensions and content-object metadata.
- Supabase Storage stores gzip HTML/text objects at content-addressed keys.
- The web service authenticates, enqueues and displays work.
- A standard background worker claims rows with `FOR UPDATE SKIP LOCKED` and a
  renewable lease. Three source windows may run concurrently; article fetches
  are bounded and rate limited per source.
- A five-minute Render cron calls an authenticated scheduling endpoint. It
  cannot enqueue the same five-minute bucket twice.

## Metric Semantics

- `observation_events`: collector emissions, including repeat observations.
- `unique_candidates`: first observation of a URL/query inside a source-run.
- `fetch_attempted`: a real outlet fetch, Google resolution, or WordPress API
  body retrieval was attempted.
- `fetch_succeeded`: that attempt returned usable content without HTTP error.
- `body_extracted`: body/API content has at least 200 characters. A title or
  snippet never qualifies.
- `final_url_resolved`: URL host is a vehicle, never `news.google.com`.
- `page_date_verified`: date came from page metadata or a source API. Feed and
  sitemap dates remain `feed_only`/`sitemap` evidence.
- `city_confirmed`, `city_probable`, `state_only`, `other_city`: evidence-based
  geography result. Other municipalities reduce confidence but do not delete.
- `duplicate_urls`: an observation mapped to an existing canonical article.

## Coverage Semantics

Only `exhausted` and `empty_verified` are clean source-window outcomes.
`capped`, `retryable`, `blocked` and `failed` remain visible gaps. A Google
window at the 100-result cap is split recursively; a one-day cap remains an
explicit cap. Candidate fetch/storage errors keep a window retryable.

## Source Policy

`data/rio_corpus_sources_v1.json` is the source registry. City-focused archives
are collected without a keyword gate. State sections use editorial paths, then
body-level geography. Google uses Google syntax and monthly windows; WordPress
and sitemaps do not receive Google query strings. RSS is realtime-only.

`data/rio_geography_v1.json` is the evidence registry. Ambiguous terms such as
Flamengo, Campo Grande and Zona Sul require city coevidence. Tourism, events,
hospitality and visit intent are dimensions assigned after collection.

## Online Gates

1. Deploy schema/API with no historical job.
2. Prove login, CSRF, password change, relogin and restoration on Render.
3. Import legacy Rio rows idempotently.
4. Run a recent day, a 2011 day and a 2011 month with authenticated monitoring.
5. Accept 2011 only when every child source window is clean or an explicit gap.
6. Queue 2012-2026 only after the canary funnel is audited.

The current operational target is 200,000 unique `confirmed + probable`
articles, 85% with real body, 90% direct URL resolution, 80% page/API dates and
90% geography precision/recall on a stratified human sample.

## Live Deployment State - 2026-07-14

- Commits `423273e` and `bc35294` are live on the existing Render web service.
- Managed PostgreSQL `clipping-rio-corpus` is available in Virginia, but the
  web service does not yet have `RIO_CORPUS_DATABASE_URL`; `/healthz` therefore
  reports `rioCorpus.configured=false` and database metrics show zero active
  application connections.
- The existing web service predates the Blueprint. Pushing `render.yaml` did
  not create or attach the declared worker and cron automatically. They must be
  created by applying the Blueprint or from the Render dashboard, with the
  database and existing Supabase secrets linked to the worker.
- No new Rio corpus job, source-run, observation or article has been created.
  This is intentional: the infrastructure and password gates remain closed.
- The logged-out production boundary passed all 32 checks, including every new
  Rio API. A public demo session received `403 rio_economic_profile_required`
  from status, source, corpus, coverage and audit endpoints.
- The admin password change/relogin/restoration smoke remains pending because
  no current plaintext admin credential is available in the operator shell.

The next valid action is infrastructure attachment, followed by the password
smoke and the three canaries. Do not infer collection progress from deployed
code alone.
