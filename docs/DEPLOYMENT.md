# Deployment

The clipping project deploys to Render as **two services**, declared in
`render.yaml` at the repo root.

## Services

### 1. `clipping-dashboard` (static site)

The read-only HTML/CSS/JS dashboard. Serves `index.html` and `assets/` from
the repo root. At build time it runs
`tools/export_mobile_snapshot.py --all-stories` to bake a snapshot of the
SQLite DB into static JSON. The build is pointed at the live API
(`https://clipping-api.onrender.com`) so the dashboard can fetch fresh
classifications at runtime via the `data-clipping-api-url` attribute.

### 2. `clipping-api` (Python web service)

A Flask app (`api_server.py`) running under gunicorn. It accepts coworker
classification writes and serves live reads from a SQLite DB on a
**persistent Render Disk** named `clipping-data`, mounted at `/data`. The
`CLIPPING_DB` env var points the app at `/data/clipping.db`.

## Persistence model

- **Source of truth at runtime:** `/data/clipping.db` on the API service's
  Render Disk. Survives deploys and restarts.
- **Build-time DB:** `data/clipping.db` checked into the repo. Used only
  to (a) bake the static snapshot into the dashboard build and (b)
  bootstrap `/data/clipping.db` on first deploy via the API's
  `preDeployCommand`.
- The static site has no write access and no disk; it is read-only at the
  file level. All writes go through the API.
- Because the static snapshot is frozen at build time, classifications
  made between deploys will only show up via the live API fetch — not in
  the baked JSON.

## Running locally

```bash
# Terminal 1: start the write API on http://localhost:5000
python api_server.py

# Terminal 2: open the dashboard in a browser
open index.html   # or: python -m http.server 8000
```

In `index.html`, set `data-clipping-api-url="http://localhost:5000"` (or
edit it temporarily) so the dashboard talks to your local API instead of
the deployed one.

## First-time deploy

The existing Render service was configured manually through the dashboard
UI. Before applying `render.yaml`:

1. Confirm the manually-configured service's name does not collide with
   `clipping-dashboard` or `clipping-api`, **or** delete the old service.
2. Push to `master` and let Render pick up `render.yaml` (Blueprints).
3. Verify the API's `preDeployCommand` populated `/data/clipping.db` from
   the build-time DB on first run. Subsequent deploys will leave the disk
   copy untouched.
