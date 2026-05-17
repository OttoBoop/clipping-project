# Current Short-Term Loop - Functional Password-Gated Segregation

_Created 2026-05-18 by Atlas/Codex. This loop is derived from
`LONG_TERM_GOALS.md`._

## Purpose

Create the first real segregation layer on the existing Render/FastAPI app.
Do not create a new repo or new site in this loop.

The user-visible failures this loop addresses:

- the public dashboard and JSON payloads can mix unrelated projects;
- growing target/filter lists create visual pollution;
- a sellable product cannot expose one client's data to another;
- UI controls for targets and updates must not pretend to be connected if they
  are not safe for a scoped client profile.

## Required System Connections To Prove

Use `SYSTEM_REVIEW_CHECKLIST.md` before and after any patch. A fix is not
accepted until the loop proves:

1. logged-out users cannot fetch private dashboard data or raw texts;
2. login creates a viewer profile with explicit scope;
3. the server filters target metadata, stories, articles, raw texts, live
   results, and classifications by that scope;
4. direct API calls cannot widen scope by changing query params;
5. client profiles see only relevant filters and a reduced visual surface;
6. operator/admin workflows remain available for Otavio;
7. unsupported client actions are hidden or rejected server-side;
8. tests cover at least Flavio, Shakira, and Rio economic profile boundaries.

## Initial Technical Sprint

Implement the simplest functional version:

- keep the existing FastAPI app as the entrypoint;
- add viewer-profile sessions alongside the existing admin session;
- serve `assets/clipping-data.json` and `assets/clipping-raw-texts.json`
  through authenticated, scoped handlers instead of open static JSON;
- gate read APIs behind a logged-in session and filter them by profile;
- gate update, export, target mutation, category creation, and classification
  writes to admin/operator sessions;
- hide runner, target management, and classification editor controls for
  non-admin viewer profiles;
- add focused regression tests for auth and scoping.

## Expected Commit Shape

Use small, path-limited commits:

1. docs-only loop memory;
2. auth/profile and scoped payload implementation;
3. frontend hide/relabel for viewer profiles;
4. tests and work-log update.

Do not include inherited pycache, screenshots, moved legacy docs, or unrelated
dirty files.

## Stop Conditions

Stop only if:

- a dirty file required for the loop contains conflicting uncommitted work that
  cannot be safely merged;
- another active agent owns the exact file and a coordination note is required;
- tests reveal that scoped payloads cannot be produced without a broader data
  model migration.

If blocked, write the block in `WORK_LOG.md` and preserve all unblocked work.
