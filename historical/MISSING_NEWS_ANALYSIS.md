This document was written during an earlier baseline where many sources were still missing due to discovery gaps.
As of `2026-03-15`, the project status is tracked in:

- `CLIPPING CATALOGUE.md` (per-source benchmark snapshot + next actions)
- `TESTING_SET.md` (testing set definition and how to re-run benchmarks)


## Current Status (2026-03-15)

We now have dedicated recovery/benchmark tooling per source, including:

- `tools/benchmark_sources_vs_excel.py` for per-host benchmarking vs Excel.
- `tools/globo_family_diagnostic.py` to diagnose URL-by-URL fetch/extraction buckets for `oglobo/g1/extra`.

The "missing news" analysis should be re-derived by re-running the benchmarks; the canonical place to read the current numbers is `CLIPPING CATALOGUE.md`.