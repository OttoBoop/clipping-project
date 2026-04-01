#!/usr/bin/env python3
"""CLI entry point for the Clipping Project news ingestion pipeline."""
import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pipeline.ingest import IngestionOptions, run_ingestion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)


def _progress_callback(event: str, data: dict):
    ts = datetime.now().strftime("%H:%M:%S")
    if event == "run_started":
        print(f"[{ts}] === RUN STARTED: {data.get('sources_total', 0)} sources, {data.get('candidates_total', 0)} total candidates ===")
    elif event == "source_collected":
        print(f"[{ts}]   Collected {data.get('candidates_total', 0):>4d} candidates from {data.get('source_name', '?')} ({data.get('source_type', '?')})")
    elif event == "source_started":
        print(f"[{ts}] >> Processing {data.get('source_name', '?')} ({data.get('source_type', '?')}): {data.get('candidates_total', 0)} candidates")
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
    elif event == "run_complete":
        print(
            f"[{ts}] === RUN COMPLETE: "
            f"sources={data.get('sources_total', 0)} "
            f"articles={data.get('articles_inserted', 0)} "
            f"mentions={data.get('mentions_inserted', 0)} "
            f"stories={data.get('stories_touched', 0)} ==="
        )
    elif event == "candidate_evaluated":
        status = data.get("status", "")
        if status == "selected":
            print(
                f"[{ts}]    + SAVED: {data.get('candidate_title', '')[:80]} "
                f"| {data.get('candidate_url', '')[:60]} "
                f"| targets={data.get('matched_targets', [])}"
            )
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(
        description="Clipping Project — News Ingestion Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_ingestion.py all --target flavio_valle --date-from 2026-03-27 --date-to 2026-03-30
  python run_ingestion.py google_news --query "Flavio Valle vereador"
  python run_ingestion.py sitemap_daily --date-from 2026-03-28
  python run_ingestion.py internal_search --target flavio_valle
        """,
    )
    parser.add_argument(
        "collector", nargs="?", default="all",
        choices=["all", "rss", "google_news", "wordpress_api",
                 "internal_search", "sitemap_daily",
                 "vejario_archive", "camara_archive"],
        help="Which collector(s) to run (default: all)",
    )
    parser.add_argument("--target", default="flavio_valle", help="Target key to match (default: flavio_valle)")
    parser.add_argument("--query", default="", help="Custom search query (overrides target keywords)")
    parser.add_argument("--date-from", default="", help="Start date YYYY-MM-DD (default: 7 days ago)")
    parser.add_argument("--date-to", default="", help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--request-timeout", type=int, default=15, help="HTTP timeout in seconds")
    parser.add_argument("--skip-direct-scrape", action="store_true", default=True,
                        help="Skip direct_scrape collector (default: True)")
    parser.add_argument("--max-candidates", type=int, default=90000,
                        help="Max candidates per source (default: 90000)")
    parser.add_argument("--max-process-seconds", type=int, default=90000,
                        help="Max seconds per source processing (default: 90000)")

    args = parser.parse_args()

    # Default date range
    if not args.date_from:
        args.date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not args.date_to:
        args.date_to = datetime.now().strftime("%Y-%m-%d")

    options = IngestionOptions(
        target_keys=[args.target] if args.target else None,
        custom_query=args.query,
        date_from=args.date_from,
        date_to=args.date_to,
        request_timeout_seconds=args.request_timeout,
        skip_direct_scrape=args.skip_direct_scrape,
        max_candidates_per_source=args.max_candidates,
        max_process_seconds=args.max_process_seconds,
    )

    run_ingestion(args.collector, options, progress_callback=_progress_callback)


if __name__ == "__main__":
    main()
