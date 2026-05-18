# System Connection Checklist

_Created 2026-05-18 by Amio/Codex._

Use this checklist before implementing and before closing any sprint touching
targets, filters, saved news, base display, or updates.

## Target Management Loop

- UI form fields map to the backend payload names.
- `/api/targets` create/update/archive/restore returns structured success or
  structured error.
- Error response includes what failed, why it matters, and how the user can fix
  it.
- `data/targets.json` has the expected key, label, keywords, aliases, primary
  flag, and archived flag.
- `/api/targets` returns the same active target set the frontend will render.
- Archived names do not appear in ordinary filters or future runs.
- Restored names reappear without requiring a deploy.

## Update And Ingestion Loop

- `build_update_spec` receives exactly the target keys selected in the UI.
- The job stores enough target information to avoid being corrupted by later
  target edits.
- `pipeline.settings.get_active_targets()` can construct `Target` objects for
  newly added secondary targets.
- Collector query builders use the selected target's display name and keywords,
  not hardcoded Flavio-only variants for every target.
- `process_candidates` runs the matcher for the selected target and emits
  `article_saved` only after durable save or confirmed existing-article retag.
- Duplicate articles can still receive a new target mention.

## SQLite Truth Loop

- `articles` contains the saved article.
- `mentions` contains the selected target key.
- `story_articles` links the article to a story.
- `story_targets` contains the selected target key.
- Cleanup/backfill must not create target tags based only on boilerplate or
  related-links noise.

## Live Base Loop

- `/api/update/live-results?scope=base` returns recent saved articles for active
  targets.
- `/api/update/live-results?job_id=...` returns saved articles during a running
  job.
- Manual story confirmation emits `article_saved` and appears in the same Base
  atual live-results path as ingestion and target backfill.
- A saved-but-not-exported item remains marked `saved`; only export or real
  artifact publication should make it `published`.
- The frontend merges live results into the in-memory payload without requiring
  a full export.
- Base atual stats and filters update after live results merge.
- A user can select the new target filter and see the saved article if a real
  match exists.

## Export And Published Snapshot Loop

- `tools/export_mobile_snapshot.py` loads active targets from `data/targets.json`.
- Exported `assets/clipping-data.json` includes target metadata and counts.
- Secondary target safe-surface filtering does not remove real matches.
- Frontend filters read the same target keys used by the backend.
- Published snapshot remains usable if live overlay is temporarily unavailable.

## Verification Rule

For any target/filter/base fix, close the loop with at least one test or smoke
that proves:

```text
create target -> run or simulate match -> save article/mention/story_target ->
live-results/export exposes it -> frontend-visible filter can select it
```

If a step cannot be verified, log why in `WORK_LOG.md` before moving on.
