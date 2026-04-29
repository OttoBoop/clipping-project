# Historical Documents

These files are kept for context and traceability. They are **not** active
guidance for the current project.

They were produced during the recovery and reconstruction phase, after the
original Windows SSD was wiped and the codebase had to be rebuilt from Codex
session logs. The recovery is complete: the pipeline is operating, the
dashboard is published, and current work is moving toward an online
coworker-facing tool (see `md documents/` at the repo root).

## Contents

### Recovery and reconstruction
- `RECOVERY_NOTES.md` — what happened, what was recovered, and how.
- `RECONSTRUCTION_PLAN.md` — the rough recovery plan written before pipeline files were rebuilt.
- `PLAN_Clipping_Reconstruction.md` — detailed implementation plan with task IDs (F1-T1…F5-T9), most marked complete.
- `DISCOVERY_Clipping_Reconstruction_Debug.md` — discovery questionnaire driving the reconstruction.
- `FORENSIC_INVENTORY.md` — per-file classification of recovered fragments and gaps.
- `IDEAS_Clipping_Reconstruction.md` — deferred ideas captured during discovery.

### Validation oracle
- `VALIDATION_ORACLE.md` — targeted re-scraping guide derived from the last
  pre-loss public HTML snapshot (1148 articles, 4 targets, 36 provider × site
  combos). Useful as a regression oracle if a collector seems to be missing
  articles it once captured.

### Misc
- `MISSING_NEWS_ANALYSIS.md` — early baseline note. Self-supersedes by
  pointing at the benchmark tooling for current numbers.
- `EXPORT_HTML_OFFLINE.md` — short note about offline export, references
  original Windows paths.
- `FUTURE_IDEAS.md` — Windows volume serial fragment. Kept for completeness;
  has no real content.
