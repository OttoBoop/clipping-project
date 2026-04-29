# Long-Term Goals for the Clipping Online Project

_Created 2026-04-29 by Iris (Claude Code orchestrator). Append-only; attribute each entry._

This document captures goals that are confirmed as desirable but deferred from
the current implementation checkpoint. They should be revisited after the core
human-classification feature is live.

---

## 1. Centimetragem

**Status**: placeholder field exists (`classifications.centimetragem REAL`); semantics undefined.

**Background**: a coworker requested this metric. Otávio does not yet have a
firm definition for it. The term refers to the physical column-centimetre
measurement used in traditional print press monitoring to gauge coverage volume.

**What needs to happen before implementation**:

- An Iris-Research subagent (or a direct conversation with the requesting
  coworker) needs to clarify:
  - What unit? Physical centimetres of print column? A proxy for print sources
    only, or also digital?
  - How is it captured? Manually measured and entered by a coworker? Auto-derived
    from article length?
  - What is it used for? Reporting summary tables? Per-article detail?
- Once the definition is agreed, the `centimetragem` field can be given a proper
  CHECK constraint and the UI can expose a numeric input for it.

**Blocked on**: research with the requesting coworker.

---

## 2. Auto-Update Spreadsheet

**Status**: not started; no prior implementation exists.

**Background**: classification output (sentiments, categories, centimetragem)
should eventually sync to an external spreadsheet — likely Excel or Google Sheets
— so the team can review structured data in the format they already know.

**What needs to happen before implementation**:

- Decide the target format: Excel file (generated on demand and downloaded) or
  Google Sheets (live sync via API).
- Decide the trigger: manual export button, scheduled job, or webhook on each
  classification save.
- Decide the columns: article title, URL, date, target, article_sentiment,
  target_sentiment, categories, centimetragem, classified_by.

**Blocked on**: core classification feature being live, and format/trigger
decision from Otávio.

---

_Next entry: append below with `## N. Title` and a `_YYYY-MM-DD by Side_` attribution line._
