# Recovery Notes — The Clipping Project

**Date:** 2026-03-29
**Source:** NVMe SSD (WDC PC SN730 256GB) recovered after Linux (EndeavourOS) was installed over Windows NTFS.
**Method:** Disk image forensics → byte-level scanning → Codex session log extraction → patch reconstruction.

## What Happened
The original SSD had Windows NTFS with ~50GB of data including this clipping project. A Linux distro was installed over it, deleting the partition. After ~12 hours of Linux usage, the SSD was removed and imaged for recovery.

## Recovery Results

### Fully Recovered (from Codex apply_patch operations)
These files were reconstructed from Codex session logs that contained the actual code as patches:

| File | Lines | Notes |
|------|-------|-------|
| `pipeline/collectors.py` | 696 | Core: 12+ news source collectors |
| `pipeline/database.py` | 361 | ClippingDB class |
| `pipeline/ingest.py` | 426 | Ingestion pipeline |
| `pipeline/matcher.py` | 116 | Citation matching |
| `server.py` | 313 | Server component |
| `run_ingestion.py` | 15 | Entry point (partial) |
| `app.js` | 23 | Frontend JavaScript |
| `README.md` | 1 | Documentation (partial) |
| `tools/benchmark_sources_vs_excel.py` | 708 | Benchmark tool |
| `tools/export_mobile_snapshot.py` | 151 | Export tool |
| `tests/test_flavio_query_expansion.py` | 361 | Query expansion tests |
| `tests/test_internal_site_search_collectors.py` | 72 | Collector tests |
| `tests/test_source_recovery_collectors.py` | 169 | Source recovery tests |
| `tests/test_direct_scrape_windows.py` | 2 | Direct scrape tests (partial) |

### Known to Exist but Not Yet Extracted
These files were referenced in the session logs but the extractor needs fixing to pull them:

- `pipeline/settings.py` (164+ lines, contains FLAVIO_INTERNAL_SEARCH_TARGETS)
- `pipeline/http_utils.py` (789+ lines)
- `pipeline/normalization.py`
- `data/targets.json` (28 entries)
- `data/runtime.json`
- `tests/test_run_ingestion_dedup.py`
- `tests/test_benchmark_sources_vs_excel.py` (1007+ lines)
- `tests/test_http_utils.py` (254+ lines)
- `tests/test_google_news_collector.py`
- `tests/test_cbn_source_recovery.py`
- `tests/test_odia_r7_site_collectors.py`
- `tests/test_export_mobile_snapshot.py`
- `tests/test_internal_site_search_ingest.py`
- `tests/test_globo_family_diagnostic.py`
- `tests/test_wordpress_site_collectors.py`
- `tools/generate_flavio_valle_print_pdf.py` (8.2KB in shell output)
- `tools/backfill_google.py`
- `tools/cbn_search_diagnostic.py`
- `tools/fix_encoding.py`
- `tools/extract_mock_data.mjs`
- `tools/prepare_wix_clipping_snapshot.py`
- `tools/benchmark_auto_vs_excel.py`
- `EXPORT_HTML_OFFLINE.md`
- `MISSING_NEWS_ANALYSIS.md`
- `FUTURE_IDEAS.md`
- `index.html`
- `progress.html`

### Office Documents (Recovered via signature carving)
77 files including Excel spreadsheets, Word documents, and PowerPoint presentations.
The 70MB pptx is likely a PIBIC presentation.

## Important Notes

1. **Files are reconstructed from diffs** — they contain code that was added across multiple Codex sessions. Some files may have duplicate lines or ordering issues from overlapping patches.

2. **The NTFS MFT was destroyed by TRIM** — we could not do traditional file recovery. Instead, we found the code embedded in Codex session logs stored in AppData.

3. **The original project path was:** `C:\Users\Admin\.vscode\docs\The Clipping project\`

4. **News sources implemented:** Globo internal search, Câmara do Rio, CONIB, Veja Rio archive, CBN (sitemap), WordPress API (agendadopoder.com.br), Google News, direct scrape, RSS, sitemap daily.

5. **The raw recovered files (358 files, 978MB) are preserved on D:\recovery\YOUR_FILES\** for further extraction if needed.

## Technical Details
- Disk image: `D:\ssd recovery\laptop ssd.001` (238GB)
- SHA-256: `F00493F4C9FC2BD086578FD0837DB9C0EA5D56AE3D56C33341A748F6A5F0C1D9`
- TRIM wiped 95% of the disk (1.4M zero windows vs 80K text windows)
- Data survived in the 206-228GB region (Codex session logs in AppData/VSCode)
