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
- the session is in Plan Mode, where mutation is prohibited.

If blocked, write the block in `WORK_LOG.md` and keep all unblocked work moving.

## No Idle Exit

This loop does not end when:

- focused tests pass;
- a commit is created;
- a push succeeds;
- Render deploys;
- one live smoke passes;
- a single target/filter/base path looks repaired.

Each of those is a checkpoint. After a checkpoint, follow
`LOOP_OPERATING_PROTOCOL.md`: re-read goals, audit the live site, update
`WORK_LOG.md`, choose the next failure or watch item, and continue.

The durable update job, live-results overlay, published dashboard, target
filters, and export counts remain active watch items until they are stable over
repeated cycles or superseded by a higher-priority live failure.

## User Away Rule

If Otavio says he is leaving, busy, away, eating, or unable to babysit the
agent, the short-term loop enters unattended mode from
`LOOP_OPERATING_PROTOCOL.md`.

In unattended mode:

- do not send a final answer after one short cycle;
- use the fixed unattended queue;
- write `Why the loop continues` in `WORK_LOG.md`;
- treat auth-gated live checks as a blocker for that specific check only, not
  as a reason to stop all work;
- if tests pass, start a new audit instead of ending.

The minimum acceptable unattended behavior is repeated cycles of:

```text
re-read docs -> audit live or auth gate -> run focused contracts -> search next
inconsistency -> update log -> continue
```

## Debug Discipline

Do not use the full test suite as the first debugging tool. It is too slow for
the repair loop and makes Otavio wait without actionable signal.

Use this order:

1. Run the smallest focused tests that cover the changed files.
2. If a failure appears, rerun that exact test with `-q` and then with traceback
   detail only if needed.
3. Use `-x` for discovery when the failure location is unknown.
4. Treat live-network tests as confirmation, not diagnosis; rerun the exact live
   failure once before changing code.
5. Run the full suite only at loop checkpoints or before a larger commit.
6. Log any slow suite run, the reason it was necessary, and whether it found a
   real regression or a transient/live-source issue.
