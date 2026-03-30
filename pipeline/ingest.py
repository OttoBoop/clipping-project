"""Main ingestion orchestrator for the clipping pipeline."""
import json
from dataclasses import dataclass, field
from pathlib import Path

from .collectors import (
    collect_google_news, collect_rss, collect_wordpress_api,
    collect_internal_site_search, collect_sitemap_daily,
    collect_vejario_archive, collect_camara_archive,
    _dedupe_candidates_by_url,
)
from .matcher import CitationMatcher, Target
from .database import ClippingDB
from .http_utils import fetch_url
from .normalization import clean_title
from .settings import (
    FLAVIO_INTERNAL_SEARCH_TARGETS, WORDPRESS_HOSTS,
    SITEMAP_CONFIGS, RSS_FEEDS, get_default_query,
)


@dataclass
class IngestionOptions:
    collector: str = "all"
    target_keys: list = field(default_factory=lambda: ["flavio_valle"])
    custom_query: str = ""
    date_from: str = ""
    date_to: str = ""
    db_path: str = "data/clipping.db"
    request_timeout: int = 8
    skip_direct_scrape: bool = True


def load_targets(target_keys=None):
    """Load targets from data/targets.json."""
    targets_file = Path(__file__).parent.parent / "data" / "targets.json"
    if not targets_file.exists():
        print(f"  Warning: {targets_file} not found, using default target")
        return [Target(
            key="flavio_valle", label="Flávio Valle", display_name="Flávio Valle",
            keywords=["Flavio Valle", "Flávio Valle"], primary=True,
        )]

    with open(targets_file, "r", encoding="utf-8") as f:
        raw = json.load(f)

    targets = []
    for entry in raw:
        t = Target(
            key=entry["key"], label=entry.get("label", ""),
            display_name=entry.get("display_name", entry.get("label", "")),
            keywords=entry.get("keywords", []),
            exact_aliases=entry.get("exact_aliases", []),
            className=entry.get("className", ""),
            primary=entry.get("primary", False),
        )
        targets.append(t)

    if target_keys:
        targets = [t for t in targets if t.key in target_keys]

    return targets


def run_ingestion(options):
    """Main entry point: collect candidates, match, store."""
    print("=" * 60)
    print("CLIPPING PIPELINE — Ingestion Run")
    print(f"  Collector: {options.collector}")
    print(f"  Date range: {options.date_from} to {options.date_to}")
    print(f"  Database: {options.db_path}")
    print("=" * 60)

    # Load targets
    targets = load_targets(options.target_keys)
    if not targets:
        print("ERROR: No targets found. Aborting.")
        return

    print(f"\nTargets: {', '.join(t.display_name or t.label for t in targets)}")

    # Build query
    all_keywords = []
    for t in targets:
        all_keywords.extend(t.keywords or [])
    query = options.custom_query or get_default_query(all_keywords)
    print(f"Query: \"{query}\"")

    # Determine which collectors to run
    collector = options.collector
    all_candidates = []

    collectors_to_run = []
    if collector in ("all", "google_news"):
        collectors_to_run.append("google_news")
    if collector in ("all", "rss"):
        collectors_to_run.append("rss")
    if collector in ("all", "wordpress_api"):
        collectors_to_run.append("wordpress_api")
    if collector in ("all", "internal_search"):
        collectors_to_run.append("internal_search")
    if collector in ("all", "sitemap_daily"):
        collectors_to_run.append("sitemap_daily")
    if collector in ("all", "vejario_archive"):
        collectors_to_run.append("vejario_archive")
    if collector in ("all", "camara_archive"):
        collectors_to_run.append("camara_archive")

    # Run each collector
    for cname in collectors_to_run:
        print(f"\n{'='*40}")
        print(f"=== {cname.upper().replace('_', ' ')} ===")
        print(f"{'='*40}")

        try:
            if cname == "google_news":
                batch = collect_google_news(query, options.date_from, options.date_to, timeout=options.request_timeout)
            elif cname == "rss":
                batch = collect_rss(RSS_FEEDS, options.date_from, options.date_to, timeout=options.request_timeout)
            elif cname == "wordpress_api":
                batch = collect_wordpress_api(WORDPRESS_HOSTS, query, options.date_from, options.date_to, timeout=options.request_timeout)
            elif cname == "internal_search":
                batch = collect_internal_site_search(FLAVIO_INTERNAL_SEARCH_TARGETS, query, options.date_from, options.date_to, timeout=options.request_timeout)
            elif cname == "sitemap_daily":
                batch = collect_sitemap_daily(SITEMAP_CONFIGS, options.date_from, options.date_to, query=query, timeout=options.request_timeout)
            elif cname == "vejario_archive":
                batch = collect_vejario_archive(query, options.date_from, options.date_to, timeout=options.request_timeout)
            elif cname == "camara_archive":
                batch = collect_camara_archive(query, options.date_from, options.date_to, timeout=options.request_timeout)
            else:
                batch = []

            all_candidates.extend(batch)
        except Exception as e:
            print(f"  ERROR in {cname}: {e}")

    # Deduplicate
    print(f"\n{'='*60}")
    before = len(all_candidates)
    all_candidates = _dedupe_candidates_by_url(all_candidates)
    print(f"Candidates: {before} total, {len(all_candidates)} after dedup")

    # Process candidates: match and store
    matcher = CitationMatcher(targets)
    stats = {"accepted": 0, "no_match": 0, "existing": 0, "error": 0}

    with ClippingDB(options.db_path) as db:
        for i, candidate in enumerate(all_candidates, 1):
            try:
                # Skip if already in DB
                if db.article_exists(candidate.url):
                    stats["existing"] += 1
                    continue

                # Always fetch full text — preview matching alone misses too many
                full_text, final_url = fetch_url(candidate.url, timeout=options.request_timeout)
                all_text = f"{candidate.title} {candidate.snippet} {full_text}"
                hits = matcher.find_hits(all_text)

                if hits:
                    # Insert article
                    article_id = db.insert_article(
                        url=candidate.url,
                        title=clean_title(candidate.title),
                        source_name=candidate.source_name,
                        source_type=candidate.source_type,
                        published_at=candidate.published_at,
                        snippet=candidate.snippet[:500],
                        full_text=full_text[:50000] if full_text else None,
                    )
                    if article_id:
                        # Insert mentions
                        seen_targets = set()
                        for hit in hits:
                            if hit.target_key not in seen_targets:
                                db.insert_mention(article_id, hit.target_key, hit.target_name, hit.keyword_matched)
                                seen_targets.add(hit.target_key)

                        stats["accepted"] += 1
                        print(f"  [{i}/{len(all_candidates)}] [ACCEPT] {clean_title(candidate.title)[:80]} ({candidate.source_name})")
                    else:
                        stats["existing"] += 1
                else:
                    stats["no_match"] += 1
                    if i <= 20 or i % 50 == 0:  # Don't spam for large batches
                        print(f"  [{i}/{len(all_candidates)}] [NO_MATCH] {clean_title(candidate.title)[:60]}")

            except Exception as e:
                stats["error"] += 1
                print(f"  [{i}/{len(all_candidates)}] [ERROR] {candidate.url[:60]} — {e}")

        # Summary
        print(f"\n{'='*60}")
        print(f"INGESTION COMPLETE")
        print(f"  Candidates processed: {len(all_candidates)}")
        print(f"  Accepted (matched):   {stats['accepted']}")
        print(f"  No match:             {stats['no_match']}")
        print(f"  Already in DB:        {stats['existing']}")
        print(f"  Errors:               {stats['error']}")
        print(f"  DB total articles:    {db.count_articles()}")
        print(f"  DB total mentions:    {db.count_mentions()}")
        print(f"{'='*60}")
