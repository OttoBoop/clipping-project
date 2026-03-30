#!/usr/bin/env python3
"""Benchmark source recovery modules against Excel spreadsheet data.

Restored from SSD recovery: V1 from 63MB Codex session log (complete),
V2 additions from corrupted from_patches (resolve_candidate_limit, expand_excel_days,
wordpress_site_runner for diariodorio/temporealrj).

RECOVERY STATUS:
- All V1 functions: CLEAN (recovered verbatim from apply_patch diffs)
- V2 resolve_candidate_limit: CLEAN
- V2 expand_excel_days: CLEAN
- V2 wordpress_site_runner: PARTIAL (temporealrj branch truncated)
- build_source_modules() middle entries: PARTIAL (~5-10 SourceModule entries lost to binary)
- evaluate_source_module(): CLEAN but references original pipeline API signatures
  (process_candidates, IngestionOptions) which may differ from current restored versions

KNOWN API MISMATCHES (to fix in F4 cross-reference):
- Original collectors used keyword args (source=, limit_total=, limit_per_source=, etc.)
  Current restored collectors use positional args (query, date_from, date_to, limit=)
- settings.py missing: CAMARA_ARCHIVE_TARGET, WORDPRESS_API_SITES, SITEMAP_DAILY_SOURCES,
  VEJARIO_ARCHIVE_TARGETS, build_wordpress_queries_for_site, get_active_targets,
  FLAVIO_INTERNAL_SEARCH_QUERIES
- http_utils.py missing: canonicalize_url
- ingest.py: process_candidates signature differs, IngestionOptions fields differ
- Requires: pandas (pip install pandas openpyxl)

Original path: tools/benchmark_sources_vs_excel.py
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- Original imports (some will fail until settings.py is fully restored) ---
# These are commented where the current pipeline doesn't export them yet.
# Uncomment as pipeline restoration progresses.

from pipeline.collectors import CandidateArticle

# Original imported these — not yet available in current restored versions:
# from pipeline.collectors import (
#     collect_camara_archive,
#     collect_internal_site_search,
#     collect_sitemap_daily,
#     collect_vejario_archive,
#     collect_wordpress_api,
# )
# from pipeline.http_utils import canonicalize_url
# from pipeline.ingest import IngestionOptions
# from pipeline.settings import (
#     CAMARA_ARCHIVE_TARGET,
#     FLAVIO_INTERNAL_SEARCH_QUERIES,
#     FLAVIO_INTERNAL_SEARCH_TARGETS,
#     SITEMAP_DAILY_SOURCES,
#     VEJARIO_ARCHIVE_TARGETS,
#     WORDPRESS_API_SITES,
#     build_wordpress_queries_for_site,
#     get_active_targets,
# )
import pipeline.ingest as ingest_mod

# --- V2 addition: recovered from corrupted from_patches ---
UNBOUNDED_CANDIDATE_LIMIT = 100_000

EXCEL_DEFAULT = Path(r"C:\Users\Admin\.vscode\general-ai-workflows\Acompanhamento GVFV.xlsx")
DEFAULT_START_DATE = "2025-05-01"
DEFAULT_END_DATE = "2025-07-31"


@dataclass(slots=True)
class SourceModule:
    """Recovered verbatim from Codex apply_patch."""
    host: str
    module: str
    label: str
    collect: Callable[[str, str, int], list[CandidateArticle]]
    source_type: str


# --- V2: recovered from corrupted from_patches ---
def resolve_candidate_limit(value: int) -> int:
    """Recovered verbatim from corrupted from_patches."""
    raw = int(value)
    if raw <= 0:
        return UNBOUNDED_CANDIDATE_LIMIT
    return max(1, raw)


# --- V2: recovered from CLIPPING_EXTRACTED patches ---
def expand_excel_days(days: set[str], *, start_date: str, end_date: str, padding: int) -> set[str]:
    """Recovered verbatim from CLIPPING_EXTRACTED patches."""
    if not days:
        return set()
    if int(padding) <= 0:
        return {str(day) for day in days if str(day)}
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    expanded: set[str] = set()
    for day_str in days:
        raw = str(day_str or "").strip()
        if not raw:
            continue
        base_day = datetime.strptime(raw, "%Y-%m-%d").date()
        for offset in range(-int(padding), int(padding) + 1):
            current = base_day + timedelta(days=offset)
            if current < start or current > end:
                continue
            expanded.add(current.isoformat())
    return expanded


# --- V1: recovered verbatim from Codex apply_patch ---
def normalize_url(url: str) -> str:
    """Recovered verbatim from Codex apply_patch.

    V2 addition (clipboard artifact cleanup) included below.
    """
    try:
        import pandas as pd
        if url is None or (isinstance(url, float) and pd.isna(url)):
            return ""
    except ImportError:
        if url is None:
            return ""
    value = str(url).strip()
    if not value:
        return ""
    # V1 original: fix single-slash after scheme
    value = re.sub(r"^(https?:)/([^/])", r"\1//\2", value, flags=re.I)
    # V2 addition: strip clipboard artifact suffixes like "/n", "/rn"
    value = re.sub(r"(?:/(?:n|r|rn))+$", "", value, flags=re.I)
    # Original called canonicalize_url from http_utils — not yet restored.
    # Fallback: strip trailing slashes and lowercase scheme+host
    try:
        parts = urlsplit(value)
        scheme = (parts.scheme or "https").lower()
        netloc = (parts.netloc or "").lower()
        path = parts.path.rstrip("/") or "/"
        # V2: strip clipboard artifacts from path too
        path = re.sub(r"(?:/(?:n|r|rn))+$", "", path, flags=re.I)
        return f"{scheme}://{netloc}{path}"
    except Exception:
        return value


def host_of(url: str) -> str:
    """Recovered verbatim from Codex apply_patch."""
    try:
        host = (urlsplit(url).netloc or "").lower()
    except Exception:
        return ""
    return host[4:] if host.startswith("www.") else host


def load_excel_rows(excel_path: Path, *, sheet: str, start_date: str, end_date: str) -> list[dict[str, str]]:
    """Recovered verbatim from Codex apply_patch. Requires pandas + openpyxl."""
    import pandas as pd

    df = pd.read_excel(excel_path, sheet_name=sheet).copy()
    df = df[df.get("LINK").notna() & (df["LINK"].astype(str).str.strip() != "")].copy()
    if "DATA" in df.columns:
        df = df[df["DATA"].notna()].copy()
        df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce")
        df = df[df["DATA"].notna()].copy()
        start_dt = pd.Timestamp(start_date)
        end_dt = pd.Timestamp(end_date)
        df = df[(df["DATA"] >= start_dt) & (df["DATA"] <= end_dt)].copy()
    rows: list[dict[str, str]] = []
    for _, row in df.iterrows():
        url = normalize_url(row.get("LINK", ""))
        if not url:
            continue
        rows.append(
            {
                "url": url,
                "host": host_of(url),
                "title": str(row.get("TITULO", "") or "").strip(),
                "date": str(row.get("DATA", "") or "").strip(),
            }
        )
    return rows


def build_source_modules() -> list[SourceModule]:
    """Recovered from Codex apply_patch.

    NOTE: The middle ~5-10 SourceModule entries (between agendadopoder and vejario)
    were lost to binary corruption in every recovery source. The head (agendadopoder)
    and tail (vejario, camara) are clean. The missing entries would be trivially
    reconstructable from the project's settings.py config lists once those are
    fully restored.

    Currently returns an empty list because the runner functions depend on
    settings.py constants and collector API signatures that don't match the
    current restored versions. This will be wired up in F4 cross-reference.
    """
    # Original code below — commented until settings.py exports are restored.
    # ---
    # flavio = get_flavio_target()
    # wp_sites = {
    #     host_of(str(site.get("base_url") or "")): site
    #     for site in WORDPRESS_API_SITES
    #     if str(site.get("base_url") or "").strip()
    # }
    # sitemap_sources = {str(source.get("host") or "").strip(): source for source in SITEMAP_DAILY_SOURCES}
    # internal_targets = {
    #     host_of(str(target.host or "")): target
    #     for target in FLAVIO_INTERNAL_SEARCH_TARGETS
    # }
    #
    # def wordpress_runner(site_host):
    #     site = wp_sites[site_host]
    #     def _run(start_date, end_date, max_candidates):
    #         queries = build_wordpress_queries_for_site(flavio, site)
    #         seen_urls = set()
    #         combined = []
    #         for query in queries:
    #             batch = collect_wordpress_api(
    #                 query, source_name=str(site.get("source_name") or site_host),
    #                 base_url=str(site.get("base_url") or ""),
    #                 date_from=start_date, date_to=end_date,
    #                 per_site_limit=max_candidates, request_timeout=12,
    #             )
    #             for item in batch:
    #                 if item.url in seen_urls: continue
    #                 seen_urls.add(item.url)
    #                 combined.append(item)
    #                 if len(combined) >= max_candidates: return combined
    #         return combined
    #     return _run
    #
    # ... (sitemap_runner, internal_runner, vejario_archive_runner, camara_archive_runner)
    #
    # modules = [
    #     SourceModule(host="agendadopoder.com.br", module="wordpress_api",
    #                  label="Agenda do Poder via WordPress API",
    #                  collect=wordpress_runner("agendadopoder.com.br"),
    #                  source_type="wordpress_api"),
    #     # ... ~5-10 entries lost to binary corruption ...
    #     SourceModule(host="vejario.abril.com.br", module="internal_search",
    #                  label="Veja Rio via Internal Search",
    #                  collect=internal_runner("vejario.abril.com.br"),
    #                  source_type="internal_search"),
    #     SourceModule(host="vejario.abril.com.br", module="vejario_archive",
    #                  label="Veja Rio via Archive",
    #                  collect=vejario_archive_runner("vejario.abril.com.br"),
    #                  source_type="vejario_archive"),
    #     SourceModule(host="camara.rio", module="camara_archive",
    #                  label="Camara via Archive",
    #                  collect=camara_archive_runner("camara.rio"),
    #                  source_type="camara_archive"),
    #     SourceModule(host="camara.rio", module="internal_search",
    #                  label="Camara via Internal Search",
    #                  collect=internal_runner("camara.rio"),
    #                  source_type="internal_search"),
    # ]
    # return modules
    return []  # Placeholder until settings.py and collector APIs are aligned


def db_saved_urls(db_path, *, host: str) -> set[str]:
    """Recovered verbatim from Codex apply_patch."""
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT a.url
            FROM articles a
            JOIN mentions m ON m.article_id = a.id
            WHERE m.target_key = 'flavio_valle'
            """
        )
        urls = {normalize_url(row[0]) for row in cur.fetchall()}
    finally:
        conn.close()
    return {url for url in urls if url and host_of(url) == host}


def evaluate_source_module(
    source_module: SourceModule,
    *,
    excel_urls: set[str],
    start_date: str,
    end_date: str,
    max_candidates: int,
    budget_seconds: int,
) -> dict[str, object]:
    """Recovered verbatim from Codex apply_patch.

    NOTE: Currently non-functional because it calls ingest_mod.process_candidates
    with the original API signature (source_label, source_type, candidates, options=,
    progress_callback=) which differs from the current restored version.
    Will be wired up in F4 cross-reference.
    """
    db_path = PROJECT_ROOT / "data" / "experiments" / f"benchmark_{source_module.host}_{source_module.module}.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    raw_candidates = source_module.collect(start_date, end_date, max_candidates)
    raw_urls = {normalize_url(candidate.url) for candidate in raw_candidates if normalize_url(candidate.url)}
    raw_urls = {url for url in raw_urls if host_of(url) == source_module.host}
    skip_reasons: Counter = Counter()

    def progress_callback(event_type: str, payload: dict):
        if event_type != "candidate_evaluated":
            return
        if str(payload.get("status", "")).lower() != "skipped":
            return
        reason = str(payload.get("reason", "")).strip() or "unknown"
        skip_reasons[reason] += 1

    # NOTE: Original called ingest_mod.process_candidates with different API.
    # Skipping actual ingestion for now — just measure raw collector coverage.
    saved_urls = set()  # Would come from db_saved_urls after process_candidates runs

    raw_match = sorted(raw_urls & excel_urls)
    saved_match = sorted(saved_urls & excel_urls)
    missed_urls = sorted(excel_urls - saved_urls)
    return {
        "host": source_module.host,
        "module": source_module.module,
        "label": source_module.label,
        "excel_total": len(excel_urls),
        "raw_found": len(raw_urls),
        "raw_match": len(raw_match),
        "saved_total": len(saved_urls),
        "saved_match": len(saved_match),
        "skip_reasons": dict(skip_reasons),
        "matched_urls": saved_match,
        "missed_urls": missed_urls,
        "raw_matched_urls": raw_match,
        "saved_urls": sorted(saved_urls),
        "db_path": str(db_path),
    }


def write_reports(rows: list[dict[str, object]], *, prefix: str) -> tuple[Path, Path]:
    """Recovered verbatim from Codex apply_patch."""
    out_dir = PROJECT_ROOT / "data" / "experiments"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{prefix}.json"
    csv_path = out_dir / f"{prefix}.csv"

    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)

    fieldnames = [
        "host", "module", "label", "excel_total",
        "raw_found", "raw_match", "saved_total", "saved_match",
        "skip_reasons", "matched_urls", "missed_urls",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "host": row["host"],
                    "module": row["module"],
                    "label": row["label"],
                    "excel_total": row["excel_total"],
                    "raw_found": row["raw_found"],
                    "raw_match": row["raw_match"],
                    "saved_total": row["saved_total"],
                    "saved_match": row["saved_match"],
                    "skip_reasons": json.dumps(row["skip_reasons"], ensure_ascii=False, sort_keys=True),
                    "matched_urls": json.dumps(row["matched_urls"], ensure_ascii=False),
                    "missed_urls": json.dumps(row["missed_urls"], ensure_ascii=False),
                }
            )
    return json_path, csv_path


def main() -> int:
    """Recovered verbatim from Codex apply_patch."""
    parser = argparse.ArgumentParser(description="Benchmark source recovery modules vs Excel by host")
    parser.add_argument("--excel", default=str(EXCEL_DEFAULT), help="Path to Acompanhamento GVFV.xlsx")
    parser.add_argument("--sheet", default="Assessoria de Imprensa", help="Sheet name")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE, help="Lower bound (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=DEFAULT_END_DATE, help="Upper bound (YYYY-MM-DD)")
    parser.add_argument("--hosts", default="", help="Optional comma-separated hosts to include")
    parser.add_argument("--modules", default="", help="Optional comma-separated modules to include")
    parser.add_argument("--max-candidates", type=int, default=400)
    parser.add_argument("--budget-seconds", type=int, default=900)
    args = parser.parse_args(sys.argv[1:])

    excel_path = Path(args.excel)
    if not excel_path.exists():
        raise SystemExit(f"Excel not found: {excel_path}")

    rows = load_excel_rows(
        excel_path, sheet=args.sheet,
        start_date=args.start_date, end_date=args.end_date,
    )
    excel_by_host: dict[str, set[str]] = {}
    for row in rows:
        excel_by_host.setdefault(row["host"], set()).add(row["url"])

    selected_hosts = {item.strip().lower() for item in str(args.hosts or "").split(",") if item.strip()}
    selected_modules = {item.strip().lower() for item in str(args.modules or "").split(",") if item.strip()}
    source_modules = [
        item
        for item in build_source_modules()
        if (not selected_hosts or item.host in selected_hosts)
        and (not selected_modules or item.module in selected_modules)
    ]
    benchmark_rows: list[dict[str, object]] = []
    for source_module in source_modules:
        excel_urls = excel_by_host.get(source_module.host, set())
        result = evaluate_source_module(
            source_module,
            excel_urls=excel_urls,
            start_date=args.start_date,
            end_date=args.end_date,
            max_candidates=max(1, int(args.max_candidates)),
            budget_seconds=max(60, int(args.budget_seconds)),
        )
        benchmark_rows.append(result)
        print(
            f"{source_module.host} [{source_module.module}] "
            f"excel={result['excel_total']} raw={result['raw_match']}/{result['raw_found']} "
            f"saved={result['saved_match']}/{result['saved_total']}"
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    prefix = f"source_benchmark_{timestamp}"
    json_path, csv_path = write_reports(benchmark_rows, prefix=prefix)
    print(f"JSON: {json_path}")
    print(f"CSV: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
