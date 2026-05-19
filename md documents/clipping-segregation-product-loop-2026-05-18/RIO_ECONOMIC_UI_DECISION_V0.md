# Rio Economic UI Decision V0

_Created 2026-05-18 by Atlas/Codex._

## Decision

Expose the Rio economic topic report as a read-only panel inside the existing
FastAPI dashboard, visible only to:

- admin/operator sessions;
- the `rio_economico` viewer profile.

Do not expose it to Flavio, Shakira, `demo_cliente`, logged-out users, static
exports, or future client profiles by default.

## Why

The Rio economic track is a separate topic product, not a normal person target.
Flattening it into the ordinary target list would pollute the political/person
filters and make the dashboard look less sellable.

The report is already served by a scoped backend endpoint:

```text
GET /api/reports/rio-economic-topic
```

That endpoint is the source of truth for the UI. The panel must not bundle the
report as public static JSON and must not ask the browser to hide forbidden data
after download.

## Boundaries

- The panel is read-only.
- No buttons for creating targets, approving rows, running searches, or
  publishing indicators are visible in the Rio panel.
- Manual approvals remain in the sidecar/report workflow until a real admin
  review UI exists.
- `target_row_approved=false` remains visible as a production gate, not as a
  call to action.
- If the scoped endpoint returns `401` or `403`, the panel is hidden or shows a
  non-data error; it must not fall back to static files.

## First Implementation

Add a hidden-by-default `rioEconomicReportPanel` in `index.html`.

In `assets/clipping.js`, read:

```text
data-clipping-session-profile
```

Fetch `/api/reports/rio-economic-topic` only when the session is admin or the
profile is `rio_economico`.

Render only aggregate counts and the first report stories:

- total stories;
- total articles;
- current-period count;
- manual-review count;
- manual approval status counts;
- production target gate;
- story title, date-quality policy, manual status, dimensions, and source link.

## Verification

Required checks:

- static code check proves the panel is hidden by default;
- JavaScript syntax check passes;
- logged-out Render smoke still returns `401 viewer_login_required` for the
  report endpoint and private payloads;
- positive Rio/admin Render view remains blocked until credentials are
  available in the shell, but the backend endpoint already rejects non-Rio
  viewers server-side.

## Future Work

Only add manual approval controls after the approval write path exists end to
end:

```text
UI -> API -> sidecar/report update -> validation artifact -> scoped report
```

Until then, the UI stays read-only.
