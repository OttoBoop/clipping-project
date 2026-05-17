# README For Active AI - Segregation Product Loop

_Created 2026-05-18 by Atlas/Codex._

If you are another AI agent already working in this repository, read this before
touching login, dashboard payloads, target visibility, client views, or product
segregation.

## Current Claim

This loop owns the product-segregation planning and the first password-gated
segregation implementation.

It does **not** own the Shakira/debug loop, Ariadne audit, or old coordination
history. Do not rewrite those docs to make this loop look cleaner.

## Why This Loop Exists

Otavio needs the clipping tool to become a segmented product:

- Flavio should have a clean scoped view;
- Shakira/project-specific data must not pollute political views;
- future paid clients should receive private views;
- Rio economic monitoring should become its own project track;
- the same backend can serve multiple profiles, but data must be scoped
  server-side.

## Non-Negotiable Rule

No fake UI. If a control is visible, it must be connected end to end for the
active profile. If not, hide it or reject it server-side until the loop proves
the connection.

## Coordination Notes

- The shared coordination file is
  `md documents/Who_Is_Doing_What-WRITE_WHAT_YOU'RE_DOING_HERE.md`.
- That file was already dirty when this loop started, so this loop did not
  edit it in the docs-only checkpoint.
- If you need to coordinate with this loop, append here or in `WORK_LOG.md`
  unless you can safely stage only your own hunk in the shared coordination
  file.

## Files This Loop Owns

- `md documents/clipping-segregation-product-loop-2026-05-18/`
- Auth/profile scoping changes made after the docs checkpoint.
- Tests that prove scoped payloads and client login boundaries.

## Files To Treat Carefully

- `web_app/app.py` and `web_app/jobs.py` were already dirty before this loop.
- `assets/clipping-data.json` was already dirty before this loop.
- Shakira screenshots and Shakira docs are inherited from another loop.
- Do not use `git add .`.
