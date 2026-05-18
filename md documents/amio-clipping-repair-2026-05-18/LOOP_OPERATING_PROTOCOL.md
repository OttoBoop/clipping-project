# Loop Operating Protocol - No Idle Exit

_Created 2026-05-18. This document turns the long-term goals into an operating
rule for multi-hour repair loops._

## Core Rule

**No Idle Exit:** do not stop just because a bug was fixed, tests passed, a
commit was pushed, a deploy completed, or one live smoke passed.

Every apparent success must become the start of the next cycle:

```text
re-read goals -> audit live site -> update log -> choose next failure -> act
```

The loop may stop only when Otavio explicitly asks to pause, the session enters
Plan Mode, or a real blocker is written in `WORK_LOG.md` with the next
unblocked action.

## Otavio Away Protocol

When Otavio says he needs to leave, will be away, or cannot babysit the agent,
the agent must switch into unattended loop behavior.

Unattended loop behavior means:

- do not send a final answer after one short cycle;
- keep the turn open while there is any useful non-blocked work;
- alternate between live audit, document review, focused tests, inconsistency
  search, and `WORK_LOG.md` updates;
- if one front is blocked, record the block and move to the next unblocked
  queue item;
- write "Why the loop continues" in every log entry.

Forbidden endings while Otavio is away:

- "tests passed" as a final stop;
- "commit pushed" as a final stop;
- "deploy verified" as a final stop;
- "live auth blocked me" as a final stop when local contracts, health checks,
  asset checks, docs, or handoff work remain available.

Allowed endings while Otavio is away:

- Otavio explicitly asks for pause, final, or handoff;
- Plan Mode is active and mutation is prohibited;
- every live and local queue item is blocked, and the block plus next required
  human input is written in `WORK_LOG.md`;
- the tool/session itself cannot continue.

If a cycle finishes in less than 30 minutes, immediately start another cycle.
Do not compensate by idling silently; do useful audit, documentation, or
contract verification work.

## Standard Cycle

Use 30-45 minute cycles. If a cycle finishes early, begin the next cycle
immediately.

1. **Re-anchor.**
   Read `LONG_TERM_GOALS.md`, `CURRENT_SHORT_TERM_LOOP.md`, and the tail of
   `WORK_LOG.md`. Write which long-term goal is active before changing code.

2. **Audit the live system.**
   Check `/api/update/status`, `/api/update/live-results`, and
   `/assets/clipping-data.json`. For UI, Base atual, or filter work, run a real
   browser smoke against `https://clipping-project.onrender.com/`.

3. **Pick the next failure.**
   Use this priority order:
   - live error, crash, `failed_needs_fix`, or endpoint 500;
   - broken connection between target, ingestion, SQLite, live-results, filter,
     or export;
   - count/filter/export inconsistency;
   - documentation/audit/helpful handoff work.

4. **Act in a small scope.**
   Make the smallest useful patch. Use path-limited staging. Never use
   `git add .`. If the main worktree is dirty, ahead of origin, or contaminated
   by another workstream, create a clean worktree from `origin/master`.

5. **Verify and continue.**
   Run focused tests first, then live checks when applicable. Push real fixes,
   verify the published site, write the result in `WORK_LOG.md`, and return to
   step 1.

## Fixed Unattended Queue

When no higher-priority defect is already selected, use this queue exactly:

1. Re-read `LONG_TERM_GOALS.md`, this protocol, and the tail of `WORK_LOG.md`.
2. Audit `/api/update/status`, `/api/update/live-results`,
   `/assets/clipping-data.json`, `/api/targets`, `/healthz`, and the hosted
   dashboard.
3. If live endpoints are blocked by auth, run the focused local contracts for
   dashboard polling, viewer scoping, live-results, target backfill, and export
   filters.
4. Search for a new inconsistency in targets, filters, export, Base atual, job
   events, source runs, or frontend runtime errors.
5. Update `WORK_LOG.md` with the log format below.
6. Commit/push the log if it records new evidence or decisions.
7. Return to item 1.

This queue is deliberately repetitive. Repetition is the mechanism that
prevents context loss during multi-hour runs.

## Checkpoint, Blocker, And Exit Meanings

- **Checkpoint:** a test pass, commit, push, deploy, smoke, log entry, or
  partial live verification. A checkpoint requires another cycle.
- **Real blocker:** missing password/auth path, missing product decision,
  permission failure, unsafe cross-agent conflict, or external service outage
  that prevents all related verification paths.
- **Allowed exit:** only an explicit pause/final request, Plan Mode, complete
  exhaustion of unblocked queue items with a written blocker, or a hard
  tool/session limit.

## Watch Queue

Carry these watch items forward until each one is either fixed, proven stable,
or replaced by a higher-priority live failure:

- Live authentication gates that make status/live-results audits return 401.
  Do not guess passwords or alter the auth workstream from this loop; log the
  blocked audit and continue with accessible checks such as `/healthz`, static
  assets, git history, and local contract tests.
- Active durable update jobs with many pending source runs.
- Any `failed_needs_fix` source runs or repeated source-run errors.
- `/api/update/live-results?scope=base` returning empty while new saved
  `article_saved` events exist.
- Hosted dashboard not calling `/api/update/status` or `/api/update/live-results`.
- Target metadata counts not matching article-level `targetKeys`.
- A new target appearing in `/api/targets` but not in filters/export/live data.

## Log Format

Append a short entry to `WORK_LOG.md` for every cycle:

```text
Objective reviewed:
Audit performed:
Result:
Next hypothesis:
Why the loop continues:
```

If an objective seems complete, write what proved it and immediately name the
review that follows. Completion is a checkpoint, not an exit.

## Dirty Worktree Rule

The inherited worktree may contain unrelated docs, pycache, screenshots, or
other agents' changes. Do not clean or revert them unless Otavio explicitly
asks. For loop commits:

- inspect `git status --short --branch`;
- stage only named files in this loop;
- prefer a temporary clean worktree from `origin/master` when touching files
  that are dirty in the main worktree;
- record any use of a clean worktree in `WORK_LOG.md`.

## Plan Mode Rule

If the session enters Plan Mode, stop mutating files. Use Plan Mode to improve
this protocol, ask decision-level questions, and produce a handoff plan. Once
Default Mode returns, restart at step 1.
