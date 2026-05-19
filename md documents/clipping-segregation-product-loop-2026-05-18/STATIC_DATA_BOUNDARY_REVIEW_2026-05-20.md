# Static Data Boundary Review - 2026-05-20

_Created by Atlas/Codex during the segregation product loop._

## Purpose

Verify that committed repo data files are not accidentally acting as the
private client surface. The sellable product must use scoped FastAPI routes,
not public raw files.

## Live Render Evidence

Checked on:

```text
https://clipping-project.onrender.com/
deploy=dep-d86u9ne7r5hc73cvm37g
commit=ec52781f8c15440a76f4ad719007f6a896cdf4ed
```

Logged-out direct file probes:

```text
GET /data/targets.json -> 404 Not Found
GET /data/viewer_profiles.json -> 404 Not Found
GET /data/reports/rio_economic_topic_report_20260519T142621Z.json -> 404 Not Found
GET /clipping-data.json -> 404 Not Found
```

Logged-out scoped/private surfaces still require viewer login:

```text
GET /assets/clipping-data.json -> 401 viewer_login_required
GET /assets/clipping-raw-texts.json -> 401 viewer_login_required
GET /api/reports/rio-economic-topic -> 401 viewer_login_required
GET /api/categories -> 401 viewer_login_required
```

## Local Static Boundary

The FastAPI app exposes a controlled `/assets/{asset_path:path}` handler, not a
mounted `/data` directory. `clipping-data.json` and `clipping-raw-texts.json`
are special-cased inside that handler and pass through `require_viewer()` plus
server-side scoping before response.

The dashboard HTML points at:

```text
assets/clipping-data.json
assets/clipping-raw-texts.json
```

Those names are scoped FastAPI routes in production, not raw static files.

## Test Coverage

```text
tests/test_static_data_boundary.py
```

The static test asserts:

```text
no app.mount("/data")
no StaticFiles usage in web_app/app.py
no @app.get("/data...") route
dashboard HTML does not point at data/ files
asset handler keeps clipping-data/raw-texts on require_viewer/scoped code paths
```

## Remaining Caveat

This review does not prove authenticated per-profile data correctness. That is
still covered by the authenticated smoke helper and still requires real viewer
passwords outside Git. This review only proves the raw committed `data/` files
are not public Render surfaces.
