# Clipping Project

Brazilian political news clipping pipeline for monitoring mentions of selected
Rio de Janeiro candidates — currently centered on Vereador Flávio Valle and
the surrounding circle (Pedro Angelito, Bernardo Rubião, Pedro Duarte).

The tool today is a local CLI ingestion pipeline plus a SQLite store plus a
static GitHub Pages dashboard. The next phase, coordinated by the Atlas
orchestrator, is migrating it into an online coworker-facing application
(likely Render-backed) with human classification as the central new feature.

## What it does today

1. Collects candidate articles from RSS, Google News, WordPress APIs,
   internal site search, daily sitemaps, Câmara archive, and Veja Rio archive.
2. Filters and matches against monitored target names (`data/targets.json`).
3. Fetches full article text when needed, deduplicates by URL, and groups
   related articles into stories.
4. Stores everything in `data/clipping.db`.
5. Exports a static dashboard with `tools/export_mobile_snapshot.py` — served
   at <https://ottoboop.github.io/clipping-project/>.

The published dashboard supports filters by monitored name, recent and grouped
story views, existing AI summaries, and lazy-loaded raw text.

## Quick start

```bash
# Daily ingestion (yesterday → today, all collectors except direct scrape)
python run_ingestion.py all \
  --target flavio_valle \
  --date-from $(date -d yesterday +%Y-%m-%d) \
  --date-to $(date +%Y-%m-%d) \
  --skip-direct-scrape

# Refresh the static dashboard and publish
python tools/export_mobile_snapshot.py --all-stories --merge-from index.html
git add assets/ index.html data/reports/
git commit -m "clipping: update $(date +%Y-%m-%d)"
git push origin master
```

The `--merge-from index.html` flag is **required** to preserve historical data
for all targets across publishes.

For the full operational reference (collectors, multi-target loops, parallel
backfill, performance notes, GitHub Pages contract), see
[`docs/PIPELINE.md`](docs/PIPELINE.md).

## Repository layout

| Path | Purpose |
|------|---------|
| `run_ingestion.py` | CLI entry point for ingestion. |
| `pipeline/` | Collectors, matcher, normalization, HTTP utils, SQLite layer, ingestion orchestrator. |
| `tools/` | Export, snapshot, parallel ingestion, benchmarking, report builders. |
| `data/` | `clipping.db`, `targets.json`, exported reports, visual checklists. |
| `index.html` + `assets/` | Static dashboard published via GitHub Pages. |
| `tests/` | Pytest suite. |
| `docs/PIPELINE.md` | Current operational guide. |
| `md documents/` | Atlas's orchestration framework and project orientation for the next phase. |
| `historical/` | Recovery-era plans and validation artifacts. Kept for context, not part of the active workflow. |
| `.claude/skills/clipping/SKILL.md` | Operational skill the local agent follows when running `/clipping`. |

## Targets

Configured in `data/targets.json`. Currently four monitored figures:

| Target | Key | Notes |
|--------|-----|-------|
| Flávio Valle | `flavio_valle` | Primary monitoring focus. |
| Pedro Angelito | `pedro_angelito` | Inner circle. |
| Bernardo Rubião | `bernardo_rubiao` | Inner circle. |
| Pedro Duarte | `pedro_duarte` | External — appears in "Outros candidatos" on the dashboard. |

## Where things are heading

The current local CLI workflow exists for Otavio. The next phase needs to make
the tool usable by coworkers without Otavio operating it directly. Two
documents drive that next phase:

- [`md documents/GENERAL_UNDERSTANDING_OF_OUR_GOALS_IN_THIS_PROJECT.md`](md%20documents/GENERAL_UNDERSTANDING_OF_OUR_GOALS_IN_THIS_PROJECT.md)
  — current orientation: scope, architecture today, AI-summary policy, the
  human-classification gap, and the Render direction.
- [`md documents/ORCHESTRATORS_FRAMEWORK_FOR_THE_CLIPPING_PROJECT.md`](md%20documents/ORCHESTRATORS_FRAMEWORK_FOR_THE_CLIPPING_PROJECT.md)
  — how Atlas (Codex side) and the future Claude Code orchestrator coordinate
  on shared docs, subagents, dirty workspaces, and disagreements.

A third doc, [`md documents/ATLAS_ORCHESTRATOR_HANDOFF.md`](md%20documents/ATLAS_ORCHESTRATOR_HANDOFF.md),
is Atlas's earlier rough checkpoint — kept as historical context for the
orchestration setup, superseded by the two above.

Live coordination between Atlas (local) and Claude Code (cloud) happens in
[`md documents/ATLAS_CLAUDE_COORDINATION.md`](md%20documents/ATLAS_CLAUDE_COORDINATION.md):
protocol, current status, and append-only log. Both sides should pull, read,
and update it around any session.

Open product decisions still owned by Otavio: v1 scope (review-only vs
run-and-review vs full portal), classification taxonomy and granularity,
coworker roles, production database choice, Render architecture shape, and
AI-summary governance.

## History

The codebase was forensically recovered from Codex session logs after the
original Windows SSD was wiped. That recovery work — discovery questionnaires,
forensic inventories, reconstruction plans, and the validation oracle from the
last public HTML snapshot — lives in [`historical/`](historical/). It is no
longer active guidance; the recovery is complete and the tool is operating.

## Tests

```bash
python -m pytest tests/ -v
```

## Requirements

```
feedparser>=6.0
requests>=2.28
```

Most logic uses the standard library (`urllib`, `xml.etree`, `sqlite3`,
`feedparser`, etc.).
