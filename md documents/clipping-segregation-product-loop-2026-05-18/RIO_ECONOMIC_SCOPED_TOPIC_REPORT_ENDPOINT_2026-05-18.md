# Rio Economic Scoped Topic Report Endpoint - 2026-05-18

_Created 2026-05-18 by Atlas/Codex._

This is the first app surface for the Rio economic topic report. It is not a
normal clipping target and does not add a `rio_economico` row to
`data/targets.json`.

## Endpoint

```text
GET /api/reports/rio-economic-topic
```

## Access Rule

```text
logged out -> 401 viewer_login_required
viewer profile != rio_economico -> 403 rio_economic_profile_required
viewer profile == rio_economico -> 200 latest topic report
admin -> 200 latest topic report
```

The endpoint reads the newest committed:

```text
data/reports/rio_economic_topic_report_*.json
```

and annotates the response meta with:

```text
viewerRole
viewerProfile
reportSurface=scoped_rio_economic_topic
reportFile
```

## Product Boundary

This endpoint keeps Rio as a scoped topic report:

- it does not write production DB;
- it does not write assets payloads;
- it does not write `data/targets.json`;
- it does not expose the report through static `/assets`;
- it does not add dashboard filter clutter to Flavio/Shakira.

## Verification State

Local Python can parse the changed files:

```text
ast parse passed for app and admin ui test
```

Local FastAPI/TestClient smoke is blocked in this shell because `fastapi` is not
installed in the active Python environment. The route still has a test in
`tests/test_admin_ui.py`; Render deployment and logged-out live smoke are the
next available production proof.

## Remaining Proof Needed

- live logged-out `/api/reports/rio-economic-topic` returns 401;
- Shakira/Flavio viewer cannot access it when credentials are available;
- Rio viewer can access it when credentials are available;
- UI decision: whether to expose the report as a Rio-only tab or keep it as API
  backing for an operator demo.
