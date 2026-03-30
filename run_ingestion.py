#!/usr/bin/env python3
"""CLI entry point for the Clipping Project news ingestion pipeline."""
import argparse
import sys
from datetime import datetime, timedelta
from pipeline.ingest import IngestionOptions, run_ingestion


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
    parser.add_argument("--db", default="data/clipping.db", help="SQLite database path")
    parser.add_argument("--request-timeout", type=int, default=8, help="HTTP timeout in seconds")
    parser.add_argument("--skip-direct-scrape", action="store_true", default=True,
                        help="Skip direct_scrape collector (default: True)")

    args = parser.parse_args()

    # Default date range
    if not args.date_from:
        args.date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not args.date_to:
        args.date_to = datetime.now().strftime("%Y-%m-%d")

    options = IngestionOptions(
        collector=args.collector,
        target_keys=[args.target] if args.target else None,
        custom_query=args.query,
        date_from=args.date_from,
        date_to=args.date_to,
        db_path=args.db,
        request_timeout=args.request_timeout,
        skip_direct_scrape=args.skip_direct_scrape,
    )

    run_ingestion(options)


if __name__ == "__main__":
    main()
