# Static Export Policy - Segregation Product Loop

_Created 2026-05-18 by Atlas/Codex._

Static exports are not a private-client access layer.

The current export tools write full JSON snapshots beside static HTML files so
the bundle can work offline or in Wix/GitHub Pages contexts. That is useful for
operator review and public/static publishing, but it is not equivalent to
password-gated product access.

## Rule

Private client views must use the FastAPI app with server-side session scoping.

Do not sell or deliver a segmented client product by handing out a static export
unless that export was intentionally generated from an already-scoped dataset
and reviewed as a separate deliverable.

## Why

- Static `clipping-data.json` and `clipping-raw-texts.json` files can expose the
  full exported snapshot to anyone who has the file URL.
- Browser-only filtering is not a security boundary.
- GitHub Pages, Wix, local files, and archived report bundles do not know which
  viewer is logged in.
- A paid client must not be able to inspect another client's raw texts by
  changing a URL or opening a bundled JSON file.

## Current Safe Product Surface

The current private-product surface is:

```text
FastAPI login -> session role/profile -> server-scoped /assets/*.json ->
server-scoped /api/* reads -> admin-only writes
```

## Acceptable Static Uses

- Internal operator review.
- Public/non-private snapshots.
- Historical archives that are not sold as private access.
- A future explicitly scoped export command, after tests prove the exported
  files contain only the intended profile's targets, stories, articles, raw
  texts, and classifications.

## Checklist Before Any Future Client Export

- Name the target profile.
- Generate from a scoped payload, not the full payload.
- Inspect `clipping-data.json` for forbidden target keys.
- Inspect `clipping-raw-texts.json` for forbidden raw text keys.
- Confirm the static bundle has no live `/api/*` dependency unless the API is
  also scoped for that client.
- Record the exact command and checks in `WORK_LOG.md`.
