# Commit And Dirty Worktree Rules

_Created 2026-05-18 by Amio/Codex._

The repository is already dirty. Treat existing changes as inherited work unless
you can prove you made them in the current loop.

## Entry Rule

Before touching files:

1. Run `git status --short --branch`.
2. Read `WORK_LOG.md`.
3. Check whether the intended files are already dirty.
4. If a dirty file is required for the loop, inspect the diff first and work
   with the existing changes instead of reverting them.

## Commit Rule

- Never use `git add .`.
- Stage explicit paths only.
- One logical unit per commit.
- Do not include pycache, virtualenvs, screenshots, generated probes, or old
  unrelated docs unless the loop explicitly owns them.
- Record the commit hash in `WORK_LOG.md` after committing.

## Documentation-First Commit

The first commit for this loop must include only:

```text
md documents/amio-clipping-repair-2026-05-18/
```

Commit message:

```text
docs: create clipping repair loop memory
```

## Technical Commit Boundaries

After the docs commit, probable boundaries are:

- API/validation contract;
- backend target/live-results connection;
- frontend messaging/filter refresh;
- tests/export contract.

If a patch touches more than one boundary, write why in `WORK_LOG.md` before
committing.

## Push Rule

Do not push blindly from a dirty shared repo. Before pushing:

1. Recheck `git status --short --branch`.
2. Confirm staged paths are only intended paths.
3. Confirm no inherited dirty file entered the commit.
4. If remote changed, fetch and inspect before pushing.
