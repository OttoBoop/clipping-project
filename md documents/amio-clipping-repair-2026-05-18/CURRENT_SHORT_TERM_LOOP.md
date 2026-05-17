# Current Short-Term Loop - Names, Filters, Live Base

_Created 2026-05-18 by Amio/Codex. This loop is derived from
`LONG_TERM_GOALS.md`._

## Purpose

Turn the user-visible failures into a bounded technical sprint only after the
documentation memory is committed.

The failures:

- adding a monitored name can appear to work while the filter does not;
- saved news does not reliably appear in Base atual as soon as it is found;
- error messages do not explain the real failure;
- prior agents left a dirty worktree and unclear responsibility trail.

## Required System Connections To Prove

Use `SYSTEM_CONNECTION_CHECKLIST.md` before and after any patch. A fix is not
accepted until the loop proves:

1. UI target form sends the intended payload.
2. `/api/targets` writes and returns the active target.
3. `data/targets.json` and `pipeline.settings.get_active_targets()` agree.
4. The update spec freezes the intended target set for the job.
5. Collectors build queries for the selected target.
6. Matcher creates real `mentions`.
7. Story records get real `story_targets`.
8. `/api/update/live-results` exposes saved articles.
9. `tools/export_mobile_snapshot.py` includes the target and its counts.
10. Frontend filters use the same target keys as the database/export/live
    payload.

## Initial Technical Sprint

Do not start until the docs-only commit exists.

Planned sprint goals:

- improve target add/edit/archive error responses so the user sees cause and
  correction, not a generic failure;
- remove or narrow unrelated target-management blocking during active updates;
- make target creation synchronize existing matching saved articles when safe;
- make Base atual poll live saved results quickly enough to feel immediate;
- add tests that create a target, save/match an article, and prove the filter
  path is real rather than UI-only.

## Expected Commit Shape

After the docs commit, use small path-limited commits. Probable boundaries:

1. target validation and API error contract;
2. target/backfill/live-results connection;
3. frontend messaging and filter refresh;
4. tests and any small export contract correction.

Do not include inherited pycache, old screenshots, moved docs outside this new
folder, or unrelated dirty files.

## Stop Conditions

Stop only if:

- a product decision from Otavio is required and cannot be inferred from the
  long-term goals;
- another agent's active claim makes the edit unsafe;
- tests reveal a broader architecture break that needs a new short-term loop.

If blocked, write the block in `WORK_LOG.md` and keep all unblocked work moving.
