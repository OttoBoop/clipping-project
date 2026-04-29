# Discovery: Clipping Project Reconstruction Debug

**Status:** Complete
**Date Started:** 2026-03-30
**Categories Completed:** 9/9

---

## 1. Core Requirements ✅ (Approved)

**Summary:** Full reconstruction prioritizing recovery of original code over fresh rewrites. Multiple tools contributed to the original rich HTML output (703 grouped stories with AI summaries). The previous reconstruction produced tools too far from originals. Success = all collectors return real results matching original, rich HTML export, corrupted files properly recovered or carefully rebuilt with documented decisions. Testing via targeted validation against known articles from old HTML snapshot. Direct scraper was WIP pre-loss, low priority.

### Q&A Exchange

**Q1: What is the primary goal of this debug/reconstruction effort?**
> **Full reconstruction** — Fix collectors + rebuild the rich HTML export + clean up corrupted files — bring it all back to working state.

**Tags:** [Core], [Functional]

**Q2: Which tools generated the rich HTML report?**
> **Multiple tools contributed** — different tools generated different parts (e.g., export did basic HTML, server.py added stories, another script did AI summaries).

**Tags:** [Core], [Functional], [Constraints]

**Q3: What does 'success' look like?**
> **Reconstruct, don't rebuild.** Every corrupted tool needs a comprehensive checklist: what state is it in, what can be recovered from the fragments, what needs manual reconstruction. Prefer recovering original logic over writing new code. Document every decision (recovered vs rebuilt vs skipped). Running the full pipeline end-to-end is the ultimate test. The direct scraper was a legitimate WIP (was being skipped before the loss) — document its state but don't prioritize it.
>
> Key principle: **The new rebuilt tools were "complete crap" because they ignored the original implementations.** We need to extract as much original code as possible from the corrupted files, then fill gaps carefully and document what was changed.

**Tags:** [Core], [Functional], [Constraints], [Testing]

**Q4: What quality issues have you noticed with the reconstructed pipeline's output?**
> The messy frontend output is a symptom of deeper pipeline problems. If the export is that far off, the collectors/filters likely aren't working as intended either. The original gathered ~700 news items successfully.
>
> **Testing approach:** Don't do a full run right now. Instead, do **targeted validation** — pick specific articles from the old HTML snapshot (clipping_mobile_snapshot_all_stories.html), match them with the collector that originally picked them up + their dates, and verify the reconstructed pipeline can find those same articles. This is resource-efficient and proves correctness.

**Tags:** [Core], [Testing], [Functional]

---

## 2. Functional Requirements ✅ (Approved)

**Summary:** The original pipeline had a richer architecture than reconstructed. Key missing pieces: (1) `IngestionResult` dataclass with `stories_touched`, (2) `create_or_update_story`, (3) `process_candidates`, (4) `normalize_url`/`host_of`, (5) `FLAVIO_QUERY_VARIANTS`, (6) `prepare_snapshot`/`extract_embedded_article_text`, (7) story-based HTML template with offline filters. Multi-target system (4 targets). `server.py` was a static snapshot generator. Multiple export tools existed. **The discovery/plan must define a systematic workflow: for each tool, analyze corrupted fragments → extract original code → reconstruct → TDD verify.**

### Q&A Exchange

**Q1: Should we restore all 4 targets?**
> The tool supports multiple targets via filters — user can add/remove targets at will. Flavio Valle is the main use case but that's usage, not architecture. The tool was designed to be target-agnostic. **Focus should be on understanding how the original tool worked, not on my specific usage.**
>
> Evidence from old HTML: 4 targets active (Flavio Valle 1061, Pedro Duarte 914, Bernardo Rubiao 93, Pedro Angelito 46). Top sources: diariodorio.com (549), agendadopoder.com.br (382), vejario (189), oglobo (165), odia (54), conib (48), cbn (24), extra (21), r7 (3).

**Tags:** [Functional], [Core]

**Q2: Are there other artifacts beyond the HTML + recovered files?**
> There might be more on D:\ — specifically discovery/plan docs directly related to the project. A haiku agent is indexing D:\recovery\ docs in background. The old HTML snapshot (2.5M tokens, 703 stories) is the primary evidence of how the original worked.

**Tags:** [Functional], [Constraints]

**Q3: Did the DB have a stories table? (Investigated code rather than asking user)**
> **FOUND IN CODE:** Yes. The current `database.py` already has `story_articles` table (article_id, story_id). The corrupted `server.py` contains ~250+ lines of the original HTML template with:
> - Story cards with `data-story-id`, expandable details
> - Filter buttons by target (`data-filter-target`) with JS toggle logic
> - Stats: visible stories/articles/AI summaries/raw text counts
> - Story index navigation
> - `__PAYLOAD__` JSON embedded in a script tag with `storyTargets` mapping
> - CSS for story-card, story-stats, story-summary, article-card, summary-ai, summary-raw
> - JS: `applyFilters()`, `storyTargets()`, `storyVisible()`, `activeLabel()`
> - References to functions: `create_or_update_story`, `process_candidates`, `run_ingestion`, `IngestionResult`, `clean_title`
>
> **Key insight:** The `server.py` or `prepare_wix_clipping_snapshot.py` generated the rich HTML, NOT `export_mobile_snapshot.py`. The current reconstructed export is a completely different (simpler) tool.

**Tags:** [Functional], [Core], [Constraints]

**Q4: Architecture investigation from corrupted code (self-answered)**
> Findings from corrupted files:
> - `server.py` is NOT a web server — it's a **static HTML snapshot generator** ("Sem chamadas para /api depois da geracao"). Contains 250+ lines of the story-based HTML template with JS filters.
> - `prepare_wix_clipping_snapshot.py` references `"story-card"` and `has_story_cards` — it was related to preparing snapshots for Wix embedding.
> - `benchmark_sources_vs_excel.py` (708 lines) contains ORIGINAL function definitions: `prepare_snapshot`, `extract_embedded_article_text`, `_clean_embedded_text`, `_json_string_to_text`, `source_uses_sitemap_fast_path`, `build_cbn_run_dir`, `expand_excel_days`, `main` — this file has tons of recoverable code.
> - `IngestionResult` dataclass had a `stories_touched` field (not in current reconstruction).
> - Functions like `normalize_url`, `host_of`, `FLAVIO_QUERY_VARIANTS`, `process_candidates`, `create_or_update_story` were part of the original architecture but are missing from reconstruction.
> - `fix_encoding.py` (14,711 tokens) also references `stories_touched`.
>
> **Key gap:** The reconstruction is missing: `IngestionResult`, `create_or_update_story`, `process_candidates`, `normalize_url`, `host_of`, `FLAVIO_QUERY_VARIANTS`, `prepare_snapshot`, `extract_embedded_article_text`.

**Tags:** [Functional], [Core], [Constraints], [Edge Cases]

---

## 3. Non-Functional Requirements ✅ (Approved)

**Summary:** Match original behavior + improve error handling so broken collectors don't crash the whole pipeline. No new performance/scale requirements beyond what the original had.

### Q&A Exchange

**Q1: Non-functional concerns?**
> Same as original + more robust error handling. Broken collectors should fail gracefully, not crash the pipeline.

**Tags:** [Non-Functional], [Edge Cases]

---

## 4. Constraints & Boundaries ✅ (Approved)

**Summary:** Only `direct_scrape` collector is out of scope (was WIP pre-loss). Everything else should be reconstructed: all collectors, ingest, database, matcher, the rich Wix snapshot tool, server.py (static HTML generator), benchmarks. The Wix snapshot tool is in scope because it generated the rich reports.

### Q&A Exchange

**Q1: What's out of scope?**
> Only direct scraper is out. Wix snapshot tool should be reconstructed since it generated the rich reports.

**Tags:** [Constraints], [Functional]

---

## 5. Edge Cases & Error Handling ✅ (Approved)

**Summary:** When files are too corrupted to extract code from, go back to the disk image (`D:\ssd recovery\laptop ssd.001`) and search for more fragments. Don't give up on recovery — the disk image is the last resort. Document the extraction method for each file.

### Q&A Exchange

**Q1: What to do with unrecoverable files?**
> Try harder with the disk image. Don't give up easily.

**Tags:** [Edge Cases], [Constraints]

---

## 6. Testing & Acceptance ✅ (Approved)

**Summary:** Targeted validation per collector: pick specific articles from old HTML snapshot that came from each source, run that collector for those dates, verify it finds them. This is the primary acceptance test. The old HTML with 703 stories is the test oracle.

### Q&A Exchange

**Q1: Testing approach?**
> Targeted run matching old articles. For each collector: pick articles from old HTML that came from that source, run the collector for those dates, verify it finds them.

**Tags:** [Testing], [Functional]

### Acceptance Criteria Table

| Feature | Test Type | Human Needed? | Done When |
|---------|-----------|---------------|-----------|
| Each collector (7+) | Targeted live run | Yes — verify found articles match old HTML | Collector finds known articles from old snapshot |
| Ingest pipeline | Integration | Yes — check DB after run | Articles + mentions stored correctly |
| Rich HTML export | Visual comparison | Yes — compare to old HTML snapshot | Report has story groupings, filters, stats |
| Story grouping | Integration | Yes — verify stories in DB | `story_articles` table populated correctly |
| Full pipeline E2E | Integration + visual | Yes — final verification | Run → DB → Export matches old snapshot quality |

---

## 7. Other / Notes ✅ (Approved)

**Summary:** Quality over speed. Take the time to properly recover and reconstruct each tool rather than rushing a broken pipeline.

### Q&A Exchange

**Q1: Additional concerns?**
> Quality over speed. Do it right.

**Tags:** [Other], [Core]

---

## 8. Future Plans ✅ (Approved)

**Summary:** No future plans right now. Focus entirely on reconstruction. Ideas will come after the pipeline is working again.

### Q&A Exchange

**Q1: Future improvements?**
> None right now. Focus on getting it working first.

**Tags:** [Future]

---

## 9. Parallelism Analysis ✅ (Approved)

**Summary:** 6-wave plan starting from `from_patches` originals (not current reconstructed files). Wave 1: audit all from_patches files. Wave 2: clean and restore pipeline core. Wave 3: clean and restore tools. Wave 4: cross-reference validation. Wave 5: targeted live validation. Wave 6: full E2E run + push. Two merge checkpoints (MC-1 after audit, MC-2 after restoration). Sequential dependency chain.

### Q&A Exchange

**Systematic Reconstruction Workflow:**

For EVERY component in the pipeline (17 files + tests + data), perform this 7-step audit:

| Step | Action | Output |
|------|--------|--------|
| 1. Role | What does this file do in the original architecture? | 1-line role description |
| 2. State | recovered-valid / corrupted / reconstructed / stub / missing | Classification |
| 3. Extract | If corrupted: extract all original functions, classes, constants | Cleaned code fragments |
| 4. Diff | If reconstructed: compare against original fragments — what's different/missing? | Gap list |
| 5. Bugs | What specific issues exist? (wrong behavior, missing filtering, wrong output) | Bug list |
| 6. Fix | What changes are needed? (recover, rewrite, merge, delete) | Action items |
| 7. Verify | How do we prove this component works correctly? | Test plan |

**Detection mechanism for skipped items:**
- Cross-reference ALL function names found in corrupted files against reconstructed code
- Check all imports — if a file imports a function that doesn't exist, it's a gap
- Search old HTML snapshot for source types/collector names not in current code
- Search corrupted files for class/function definitions not in any reconstructed file
- Compare DB schema references across all files

**Components to audit (complete list):**

**Pipeline Core (7):**
1. `pipeline/collectors.py`
2. `pipeline/database.py`
3. `pipeline/http_utils.py`
4. `pipeline/ingest.py`
5. `pipeline/matcher.py`
6. `pipeline/normalization.py`
7. `pipeline/settings.py`

**Entry Points (2):**
8. `run_ingestion.py`
9. `server.py`

**Tools (7):**
10. `tools/export_mobile_snapshot.py`
11. `tools/prepare_wix_clipping_snapshot.py`
12. `tools/benchmark_sources_vs_excel.py`
13. `tools/backfill_google.py`
14. `tools/cbn_search_diagnostic.py`
15. `tools/fix_encoding.py`
16. `tools/generate_flavio_valle_print_pdf.py`

**Data (1):**
17. `data/targets.json`

**Tests (14):** — all test files in tests/

**Total: 31 files to audit**

### REVISED Wave Structure (after discovering from_patches originals)

**Key decision:** Start fresh from `D:\recovery\CLIPPING_PROJECT\from_patches\` originals. Discard current reconstructed files.

**Source directories:**
- `D:\recovery\CLIPPING_PROJECT\from_patches\` — primary (patch-extracted originals)
- `D:\recovery\CLIPPING_EXTRACTED\patches\` — secondary extraction pass
- `D:\recovery\CLIPPING_EXTRACTED\shell\` — shell output versions (may be cleaner)
- `D:\recovery\clipping-project\` — current project (keep repo/git, discard reconstructed .py)

```
Wave 1: SYSTEMATIC AUDIT OF ALL from_patches ORIGINALS
  For each file in from_patches/:
  ├── 1. Read full content
  ├── 2. Classify: clean Python / escaped quotes / mixed binary / stub
  ├── 3. List all functions, classes, imports
  ├── 4. Document what's recoverable vs corrupted
  ├── 5. Check if CLIPPING_EXTRACTED has a cleaner version
  └── 6. Record decision: use as-is / clean up / needs disk image

  Files (from_patches):
  ├── pipeline/collectors.py (696 lines)
  ├── pipeline/database.py (361 lines)
  ├── pipeline/http_utils.py (77 lines)
  ├── pipeline/ingest.py (426 lines)
  ├── pipeline/matcher.py (116 lines)
  ├── pipeline/settings.py (34 lines)
  ├── server.py (313 lines)
  ├── run_ingestion.py (15 lines)
  ├── tools/export_mobile_snapshot.py (117 lines)
  ├── tools/benchmark_sources_vs_excel.py (49 lines)
  ├── tools/benchmark_auto_vs_excel.py (2 lines)
  ├── tools/prepare_wix_clipping_snapshot.py (10 lines)
  ├── data/targets.json
  ├── All test files (11 files)
  └── app.js (4300 bytes)

MC-1: MERGE CHECKPOINT — Audit complete, per-file decisions reviewed

Wave 2: CLEAN AND RESTORE PIPELINE CORE
  For each audited file:
  ├── Un-escape quotes (\" → ")
  ├── Remove binary/Codex log fragments
  ├── Reconstruct missing parts (imports, structure)
  ├── Add genuinely missing files (normalization.py, __init__.py)
  └── Syntax check each restored file

  Priority: settings → http_utils → normalization → matcher → database → collectors → ingest → run_ingestion

Wave 3: CLEAN AND RESTORE TOOLS
  ├── server.py (static HTML snapshot generator)
  ├── tools/export_mobile_snapshot.py
  ├── tools/prepare_wix_clipping_snapshot.py
  ├── tools/benchmark_sources_vs_excel.py
  └── data/targets.json (all 4 targets)

Wave 4: CROSS-REFERENCE VALIDATION
  ├── All function names from originals → verify in cleaned files
  ├── All imports → verify targets exist
  ├── Old HTML sources → verify collectors exist
  ├── DB schema → verify tables/columns
  └── Output: Gap list

MC-2: MERGE CHECKPOINT — All files restored, gaps reviewed

Wave 5: TARGETED VALIDATION (live)
  ├── Pick known articles from old HTML per source
  ├── Run each collector for those dates
  ├── Verify found articles match
  └── Fix collector bugs

Wave 6: FULL E2E RUN
  ├── Full pipeline, all collectors
  ├── Rich HTML export via restored server.py
  ├── Compare to old snapshot
  └── Push to GitHub
```

### Dependency Graph
```
Wave 1 (Audit) --> MC-1 (Review)
                      |
                Wave 2 (Pipeline) --> Wave 3 (Tools)
                                          |
                                    Wave 4 (Cross-ref)
                                          |
                                       MC-2 (Review)
                                          |
                                    Wave 5 (Validation)
                                          |
                                    Wave 6 (E2E + Push)
```

**OLD GRAPH REPLACED:**
```
OLD Wave 1 ──→ Wave 2 ──→ Wave 3 ──→ MC-1
                                    │
                              ┌─────┴─────┐
                              │           │
                           Wave 4      Wave 5
                              │           │
                              └─���───┬─────┘
                                    │
                                  MC-2
                                    │
                                 Wave 6
                                    │
                                 Wave 7
```

---

## Reliability Evidence

### Gap Matrix
| Capability | Intended | Current | Evidence | Verdict |
|------------|----------|---------|----------|---------|
| Globo collectors (O Globo, Extra) | Return articles via busca.globo.com API | Return 0 results | Pipeline run log: 0 candidates | BROKEN |
| CBN collector | Fetch via daily sitemaps | Returns 0 or errors | Pipeline run log | BROKEN |
| O Dia, R7, CONIB collectors | HTML scraping of search pages | Return 0 results | Pipeline run log | BROKEN |
| Story grouping | Articles grouped into narratives via create_or_update_story | No story logic exists | story_articles table empty | MISSING |
| Rich HTML export | 703 stories, filters, AI summaries, offline JS | Flat list, simple cards | Compare old vs new HTML | WRONG |
| IngestionResult dataclass | stories_touched, errors, progress_callback | Not implemented | from_patches/ingest.py has it | MISSING |
| Anthropic AI summaries | sentiment_reason='anthropic_batch', summary per article | Not implemented | from_patches/database.py has has_ai_summary | MISSING |
| Multi-target support | 4 targets (Flavio, Pedro Duarte, Bernardo, Pedro Angelito) | Only 1 target | targets.json has 1 entry | INCOMPLETE |
| normalize_url, host_of | URL dedup and host extraction | Not implemented | from_patches has references | MISSING |
| FLAVIO_QUERY_VARIANTS | Query expansion for search | Not implemented | benchmark file has it | MISSING |
| Camara filtering | Filter non-news content | No filtering | Camara returned non-news junk | BROKEN |
| process_candidates | Separate candidate processing step | Inline in ingest.py | from_patches has it as separate function | MISSING |

### Live-Proof Status
- **Pipeline runs but produces poor results:** 41 Camara articles (many non-news), 0 from Globo/CBN/O Dia/R7/CONIB
- **HTML export produces output but wrong format:** Simple flat list vs original's grouped story cards
- **No live proof of:** story grouping, AI summaries, multi-target, Wix snapshot, benchmarks

### Tool Inventory
- **Required and proven:** http_utils.py (requests works), basic database CRUD, basic matcher, normalization.py
- **Required but missing/unproven:** IngestionResult, create_or_update_story, process_candidates, normalize_url, host_of, FLAVIO_QUERY_VARIANTS, rich HTML template, Wix snapshot, AI summary integration
- **Deferred:** direct_scrape collector (WIP pre-loss)

### Unresolved Evidence Risks
- from_patches files are corrupted (escaped quotes, binary fragments) — unknown how much is recoverable until Wave 1 audit
- No disk image search done yet for files not in any extraction directory
- Original tests in from_patches are also corrupted — unknown test coverage
- Anthropic API key needed for AI summaries — unknown if user has one set up

---

## Connection Map

| Answer | Affects Categories | Notes |
|--------|-------------------|-------|
| Full reconstruction is the goal | Core, Functional, Constraints | Scope includes collectors, export, cleanup — no shortcuts |
| Multiple tools contributed to HTML | Core, Functional, Constraints | Must reverse-engineer which tool did what from corrupted fragments |
| Reconstruct don't rebuild | Core, Functional, Constraints, Testing | Original code fragments are the source of truth, not fresh rewrites |
| Targeted validation from old HTML | Core, Testing, Functional | Use known articles from old snapshot to verify each collector works |
| server.py has rich HTML template | Functional, Core, Constraints | 250+ lines of original story-based HTML template recovered from corrupted server.py |
| Disk image is last resort for recovery | Edge Cases, Constraints | Don't give up on corrupted files — search disk image for more fragments |
| CLIPPING_PROJECT/from_patches/ has bigger originals | ALL CATEGORIES | database.py 361 vs 114, ingest.py 426 vs 202, collectors.py 696 vs 521 — reconstruction lost half the code |
| Original used Anthropic AI for article summaries | Functional, Future | `sentiment_reason = 'anthropic_batch'` in original database.py |
| Multiple extraction dirs not fully merged | Constraints, Edge Cases | CLIPPING_EXTRACTED/ and CLIPPING_PROJECT/ have files not in current project |

---

## Completeness Score

```
Completeness Score: 6/6 gates passed
- G1: ✅ All categories covered (9/9)
- G2: ✅ All summaries approved (9/9)
- G3: ✅ Testing questions complete (acceptance criteria table in Cat 6)
- G4: ✅ Connection map entries (9 >= 3)
- G5: ✅ No pending re-approvals
- G6: ✅ Reliability evidence complete (gap matrix, live-proof, tool inventory, risks)
```

### Pre-Exit Cross-Category Review (Layer 3)
- No contradictions found
- All categories align: recover from originals, quality over speed
- One dependency: Wave 1 audit will determine which files need disk image search (Cat 5)
