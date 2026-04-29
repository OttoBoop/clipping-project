#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.collectors import (
    CandidateArticle,
    collect_camara_archive,
    collect_google_news,
    collect_internal_site_search,
    collect_rss,
    collect_sitemap_daily,
    collect_vejario_archive,
    collect_wordpress_api,
)
from pipeline.database import ClippingDB
from pipeline.ingest import (
    IngestionOptions,
    dedupe_candidates,
    ordered_unique,
    process_candidates,
    select_targets,
)
from pipeline.settings import (
    FLAVIO_INTERNAL_SEARCH_TARGETS,
    WORDPRESS_API_SITES,
    build_google_queries_for_target,
    build_internal_search_queries,
    build_wordpress_queries_for_target,
    get_active_targets,
)


logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)


@dataclass(slots=True)
class SourceTask:
    order: int
    source_name: str
    source_type: str
    kind: str
    site: dict | None = None


@dataclass(slots=True)
class CollectedBatch:
    order: int
    source_name: str
    source_type: str
    candidates: list[CandidateArticle]
    duration_seconds: float
    error: str = ""


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _safe_name(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")


def _parse_target_args(values: list[str] | None) -> list[str]:
    parsed: list[str] = []
    for raw in values or []:
        for item in str(raw or "").split(","):
            target = item.strip()
            if target:
                parsed.append(target)
    return ordered_unique(parsed)


def _targets_slug(target_keys: list[str]) -> str:
    values = [_safe_name(item) for item in target_keys if _safe_name(item)]
    return "_plus_".join(values) if values else "all_targets"


def _progress_callback(event: str, data: dict) -> None:
    ts = _timestamp()
    if event == "source_started":
        print(
            f"[{ts}] >> Processing {data.get('source_name', '?')} "
            f"({data.get('source_type', '?')}): {data.get('candidates_total', 0)} candidates"
        )
    elif event == "source_progress":
        print(
            f"[{ts}]    ... {data.get('source_name', '?')}: "
            f"seen={data.get('candidates_seen', 0)} "
            f"inserted={data.get('articles_inserted', 0)} "
            f"mentions={data.get('mentions_inserted', 0)} "
            f"stories={data.get('stories_touched', 0)}"
            + (f" [{data.get('status', '')}]" if data.get("status") else "")
        )
    elif event == "source_complete":
        errs = data.get("errors", [])
        err_text = f" ERRORS: {errs}" if errs else ""
        print(
            f"[{ts}] << Done {data.get('source_name', '?')}: "
            f"seen={data.get('candidates_seen', 0)} "
            f"inserted={data.get('articles_inserted', 0)} "
            f"mentions={data.get('mentions_inserted', 0)} "
            f"stories={data.get('stories_touched', 0)}"
            f"{err_text}"
        )
    elif event == "candidate_evaluated" and data.get("status") == "selected":
        print(
            f"[{ts}]    + SAVED: {data.get('candidate_title', '')[:80]} "
            f"| {data.get('candidate_url', '')[:70]} "
            f"| targets={data.get('matched_targets', [])}"
        )


def _compute_limits(options: IngestionOptions) -> dict[str, int]:
    max_candidates = max(1, int(options.max_candidates_per_source))
    if options.custom_query.strip():
        per_feed_limit = max_candidates
        per_query_limit = max_candidates
        per_target_limit = max_candidates
        per_wp_limit = max_candidates
    else:
        per_feed_limit = max(10, min(500, max_candidates // 2))
        per_query_limit = max(10, min(500, max_candidates // 2))
        per_target_limit = max(10, min(300, max_candidates // 3))
        per_wp_limit = max(10, min(500, max_candidates // 2))
    return {
        "max_candidates": max_candidates,
        "per_feed_limit": per_feed_limit,
        "per_query_limit": per_query_limit,
        "per_target_limit": per_target_limit,
        "per_wp_limit": per_wp_limit,
    }


def _build_tasks(options: IngestionOptions) -> list[SourceTask]:
    targets = select_targets(get_active_targets(), options.target_keys)
    tasks: list[SourceTask] = [
        SourceTask(order=0, source_name="RSS", source_type="rss", kind="rss"),
        SourceTask(order=1, source_name="Google News", source_type="google_news", kind="google_news"),
    ]
    order = 2
    for site in WORDPRESS_API_SITES:
        site_name = str(site.get("source_name") or "WordPress").strip() or "WordPress"
        tasks.append(
            SourceTask(
                order=order,
                source_name=site_name,
                source_type="wordpress_api",
                kind="wordpress_site",
                site=site,
            )
        )
        order += 1
    if not options.custom_query.strip() and targets:
        tasks.append(
            SourceTask(
                order=order,
                source_name="Internal Site Search",
                source_type="internal_search",
                kind="internal_search",
            )
        )
        order += 1
    tasks.append(
        SourceTask(
            order=order,
            source_name="Sitemap Daily",
            source_type="sitemap_daily",
            kind="sitemap_daily",
        )
    )
    order += 1
    tasks.append(
        SourceTask(
            order=order,
            source_name="Veja Rio Archive",
            source_type="vejario_archive",
            kind="vejario_archive",
        )
    )
    order += 1
    tasks.append(
        SourceTask(
            order=order,
            source_name="Camara Rio Archive",
            source_type="camara_archive",
            kind="camara_archive",
        )
    )
    return tasks


def _build_queries(options: IngestionOptions) -> dict[str, list[str]]:
    targets = select_targets(get_active_targets(), options.target_keys)
    if options.custom_query.strip():
        google_queries = [options.custom_query.strip()]
        wordpress_queries = [options.custom_query.strip()]
        internal_search_queries = [options.custom_query.strip()]
        sitemap_queries = [options.custom_query.strip()]
    else:
        google_queries = ordered_unique(
            [
                query
                for target in targets
                for query in build_google_queries_for_target(target)
            ]
        )
        wordpress_queries = ordered_unique(
            [
                query
                for target in targets
                for query in build_wordpress_queries_for_target(target)
            ]
        )
        internal_search_queries = build_internal_search_queries(targets)
        sitemap_queries = list(internal_search_queries)
    return {
        "google_queries": google_queries,
        "internal_search_queries": internal_search_queries,
        "wordpress_queries": wordpress_queries,
        "sitemap_queries": sitemap_queries,
    }


def _collect_task(task: SourceTask, options: IngestionOptions, query_config: dict[str, list[str]]) -> CollectedBatch:
    started = time.monotonic()
    request_timeout = max(3, int(options.request_timeout_seconds))
    limits = _compute_limits(options)
    try:
        if task.kind == "rss":
            candidates = collect_rss(
                limit_per_feed=limits["per_feed_limit"],
                request_timeout=request_timeout,
                date_from=options.date_from,
                date_to=options.date_to,
            )
        elif task.kind == "google_news":
            candidates = collect_google_news(
                queries=query_config["google_queries"],
                date_from=options.date_from,
                date_to=options.date_to,
                limit_per_query=limits["per_query_limit"],
                request_timeout=request_timeout,
                resolve_timeout=max(2, request_timeout - 2),
            )
        elif task.kind == "wordpress_site":
            site = task.site or {}
            site_name = str(site.get("source_name") or task.source_name).strip() or task.source_name
            base_url = str(site.get("base_url") or "").strip()
            combined: list[CandidateArticle] = []
            seen_urls: set[str] = set()
            for query in query_config["wordpress_queries"]:
                if len(combined) >= max(1, limits["per_wp_limit"]):
                    break
                batch = collect_wordpress_api(
                    query,
                    source_name=site_name,
                    base_url=base_url,
                    date_from=options.date_from,
                    date_to=options.date_to,
                    per_site_limit=limits["per_wp_limit"],
                    request_timeout=request_timeout,
                )
                for item in batch:
                    if item.url in seen_urls:
                        continue
                    seen_urls.add(item.url)
                    combined.append(item)
                    if len(combined) >= max(1, limits["per_wp_limit"]):
                        break
            candidates = combined
        elif task.kind == "internal_search":
            per_internal_adapter_limit = max(
                6,
                min(200, limits["max_candidates"] // max(1, len(FLAVIO_INTERNAL_SEARCH_TARGETS))),
            )
            candidates = collect_internal_site_search(
                queries=query_config["internal_search_queries"],
                date_from=options.date_from,
                date_to=options.date_to,
                limit_per_adapter=per_internal_adapter_limit,
                max_pages_per_adapter=20,
                request_timeout=request_timeout,
            )
        elif task.kind == "sitemap_daily":
            candidates = collect_sitemap_daily(
                queries=query_config["sitemap_queries"],
                date_from=options.date_from,
                date_to=options.date_to,
                limit_per_source=limits["max_candidates"],
                request_timeout=request_timeout,
            )
        elif task.kind == "vejario_archive":
            candidates = collect_vejario_archive(
                date_from=options.date_from,
                date_to=options.date_to,
                limit_per_target=max(10, limits["max_candidates"] // 2),
                max_pages_per_target=50,
                request_timeout=request_timeout,
            )
        elif task.kind == "camara_archive":
            candidates = collect_camara_archive(
                date_from=options.date_from,
                date_to=options.date_to,
                limit_total=max(10, limits["max_candidates"] // 2),
                max_pages=100,
                request_timeout=request_timeout,
            )
        else:
            raise ValueError(f"unknown_task_kind:{task.kind}")
        candidates = dedupe_candidates(candidates)
        return CollectedBatch(
            order=task.order,
            source_name=task.source_name,
            source_type=task.source_type,
            candidates=candidates,
            duration_seconds=time.monotonic() - started,
            error="",
        )
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()
        return CollectedBatch(
            order=task.order,
            source_name=task.source_name,
            source_type=task.source_type,
            candidates=[],
            duration_seconds=time.monotonic() - started,
            error=error,
        )


def _serialize_batch(batch: CollectedBatch) -> dict:
    return {
        "source_name": batch.source_name,
        "source_type": batch.source_type,
        "candidates_total": len(batch.candidates),
        "duration_seconds": round(batch.duration_seconds, 3),
        "error": batch.error,
    }


def _run_processing(
    batches: list[CollectedBatch],
    options: IngestionOptions,
) -> list[dict]:
    results: list[dict] = []
    for batch in sorted(batches, key=lambda item: item.order):
        source_options = options
        if batch.source_type == "internal_search":
            source_options = replace(options, archive_full_text=True)
        result = process_candidates(
            batch.source_name,
            batch.source_type,
            batch.candidates,
            options=source_options,
            progress_callback=_progress_callback,
        )
        results.append(
            {
                "source_name": result.source_name,
                "source_type": result.source_type,
                "candidates_seen": result.candidates_seen,
                "articles_inserted": result.articles_inserted,
                "mentions_inserted": result.mentions_inserted,
                "stories_touched": result.stories_touched,
                "errors": list(result.errors),
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the clipping pipeline with non-direct collectors collected in parallel.",
    )
    parser.add_argument(
        "--target",
        dest="targets",
        action="append",
        default=None,
        help="Target key to include. Repeat the flag or pass a comma-separated list.",
    )
    parser.add_argument("--date-from", required=True)
    parser.add_argument("--date-to", required=True)
    parser.add_argument("--request-timeout", type=int, default=15)
    parser.add_argument("--max-candidates", type=int, default=90000)
    parser.add_argument("--max-process-seconds", type=int, default=90000)
    parser.add_argument("--max-workers", type=int, default=12)
    parser.add_argument("--db", default="")
    parser.add_argument("--run-dir", default="")
    args = parser.parse_args()
    target_keys = _parse_target_args(args.targets) or ["flavio_valle"]

    run_token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    default_run_dir = (
        PROJECT_ROOT
        / "data"
        / "parallel_runs"
        / f"{_targets_slug(target_keys)}_{args.date_from}_{args.date_to}_{run_token}"
    )
    run_dir = Path(args.run_dir).expanduser() if args.run_dir else default_run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    db_path = Path(args.db).expanduser() if args.db else (run_dir / "clipping.db")

    options = IngestionOptions(
        target_keys=target_keys,
        date_from=args.date_from,
        date_to=args.date_to,
        request_timeout_seconds=args.request_timeout,
        max_candidates_per_source=args.max_candidates,
        max_process_seconds=args.max_process_seconds,
        skip_direct_scrape=True,
        db_path=str(db_path),
    )

    tasks = _build_tasks(options)
    query_config = _build_queries(options)
    max_workers = max(1, min(int(args.max_workers), len(tasks)))

    print(
        f"[{_timestamp()}] Parallel collection starting for {len(tasks)} source units "
        f"with max_workers={max_workers}"
    )
    print(f"[{_timestamp()}] Output DB: {db_path}")
    print(f"[{_timestamp()}] Run dir: {run_dir}")

    batches: list[CollectedBatch] = []
    collection_started = time.monotonic()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_collect_task, task, options, query_config): task
            for task in tasks
        }
        for future in as_completed(future_map):
            batch = future.result()
            batches.append(batch)
            status = "ERROR" if batch.error else "OK"
            print(
                f"[{_timestamp()}] [{status}] Collected {len(batch.candidates):>4d} candidates from "
                f"{batch.source_name} ({batch.source_type}) in {batch.duration_seconds:.1f}s"
                + (f" | {batch.error}" if batch.error else "")
            )

    collection_seconds = time.monotonic() - collection_started
    print(
        f"[{_timestamp()}] Parallel collection complete: "
        f"{sum(len(batch.candidates) for batch in batches)} total candidates in {collection_seconds:.1f}s"
    )

    processing_started = time.monotonic()
    process_results = _run_processing(batches, options)
    processing_seconds = time.monotonic() - processing_started

    with ClippingDB(db_path) as db:
        article_count = db.count_articles()
        mention_count = db.count_mentions()

    summary = {
        "run_token": run_token,
        "target": target_keys[0] if len(target_keys) == 1 else "",
        "target_keys": target_keys,
        "date_from": args.date_from,
        "date_to": args.date_to,
        "db_path": str(db_path),
        "run_dir": str(run_dir),
        "collector_units": len(tasks),
        "collection_seconds": round(collection_seconds, 3),
        "processing_seconds": round(processing_seconds, 3),
        "collection_results": [_serialize_batch(batch) for batch in sorted(batches, key=lambda item: item.order)],
        "processing_results": process_results,
        "db_counts": {
            "articles": article_count,
            "mentions": mention_count,
        },
    }
    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{_timestamp()}] Summary written to {summary_path}")
    print(
        f"[{_timestamp()}] Final DB counts: articles={article_count} mentions={mention_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
