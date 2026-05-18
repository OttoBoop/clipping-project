# Commit And Dirty Worktree Rules

_Created 2026-05-18 by Atlas/Codex._

The repository is already dirty. Treat existing changes as inherited work
unless you can prove you made them in the current loop.

## Entry Rule

Before touching files:

1. Run `git status --short --branch`.
2. Read `WORK_LOG.md`.
3. Check whether intended files are already dirty.
4. If a dirty file is required, inspect the diff first and work with existing
   changes instead of reverting them.

## Commit Rule

- Never use `git add .`.
- Stage explicit paths only.
- One logical unit per commit.
- Do not include pycache, virtualenvs, screenshots, generated probes, or old
  unrelated docs unless this loop explicitly owns them.
- Record commit hashes in `WORK_LOG.md` after committing when practical.

## Documentation-First Commit

The first commit for this loop should include only:

```text
md documents/clipping-segregation-product-loop-2026-05-18/
```

Recommended commit message:

```text
docs: create clipping segregation product loop
```

## Technical Commit Boundaries

After the docs commit, probable boundaries are:

- auth/profile session contract;
- scoped payload and API filtering;
- frontend role-based visibility;
- tests and work-log updates.

After the resumed 2026-05-18 loop, product-loop paths may also include:

- `data/viewer_profiles.json`;
- `web_app/segmentation.py`;
- `assets/clipping.css`;
- `assets/clipping.js`;
- `tools/pages_assets/clipping.css`;
- `tools/pages_assets/clipping.js`;
- `tests/test_admin_ui.py`;
- files inside `md documents/clipping-segregation-product-loop-2026-05-18/`.

If a patch touches more than one boundary, write why in `WORK_LOG.md` before
committing.

Treat untracked inherited files, especially
`tests/test_sprint_regression_harness.py`, as separate ownership questions. Do
not add them just because this loop's tests touched one line there.

## Push Rule

Do not push blindly from a dirty shared repo. Before pushing:

1. Recheck `git status --short --branch`.
2. Confirm staged paths are only intended paths.
3. Confirm no inherited dirty file entered the commit.
4. If remote changed, fetch and inspect before pushing.
