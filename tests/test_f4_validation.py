"""Tests for F4: Cross-reference validation.

F4-T1: Function cross-reference
F4-T2: Import validation
F4-T3: Source coverage check
"""
import py_compile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ═══ F4-T2: All pipeline imports work ═══

def test_all_pipeline_modules_import():
    from pipeline import collectors, database, ingest, matcher, normalization, settings


def test_all_pipeline_key_exports():
    from pipeline.collectors import CandidateArticle, collect_google_news, collect_rss
    from pipeline.collectors import collect_wordpress_api, collect_internal_site_search
    from pipeline.collectors import collect_direct_scrape, _dedupe_candidates_by_url
    from pipeline.database import ClippingDB
    from pipeline.ingest import IngestionResult, IngestionOptions, process_candidates
    from pipeline.ingest import select_targets, ordered_unique, create_or_update_story
    from pipeline.matcher import Target, MatchHit, CitationMatcher
    from pipeline.normalization import normalize_url, canonicalize_url, clean_title, normalize_text
    from pipeline.settings import get_active_targets, WORDPRESS_API_SITES
    from pipeline.http_utils import fetch_url, post_json, canonicalize_url, html_to_text


# ═══ F4-T1: Key functions exist ═══

def test_database_has_all_key_methods():
    from pipeline.database import ClippingDB
    for method in ["story_with_articles", "insert_article_if_new",
                   "list_articles_for_export", "insert_mentions",
                   "list_articles", "list_story_context"]:
        assert hasattr(ClippingDB, method), f"Missing ClippingDB.{method}"


def test_collectors_has_all_key_functions():
    from pipeline import collectors
    for fn in ["collect_google_news", "collect_rss", "collect_wordpress_api",
               "collect_internal_site_search", "collect_direct_scrape",
               "_dedupe_candidates_by_url", "_parse_pt_br_datetime",
               "fetch_full_article_text", "parse_rss_or_atom"]:
        assert hasattr(collectors, fn), f"Missing collectors.{fn}"


def test_collectors_has_all_key_regexes():
    from pipeline import collectors
    for regex in ["CAMARA_RESULT_RE", "CONIB_ARTICLE_RE", "VEJARIO_DATE_RE", "PT_MONTHS"]:
        assert hasattr(collectors, regex), f"Missing collectors.{regex}"


def test_ingest_has_all_key_functions():
    from pipeline import ingest
    for fn in ["IngestionResult", "IngestionOptions", "process_candidates",
               "create_or_update_story", "select_targets", "ordered_unique",
               "run_ingestion"]:
        assert hasattr(ingest, fn), f"Missing ingest.{fn}"


def test_settings_has_all_key_exports():
    from pipeline import settings
    for name in ["get_active_targets", "WORDPRESS_API_SITES",
                 "FLAVIO_INTERNAL_SEARCH_QUERIES", "FLAVIO_INTERNAL_SEARCH_TARGETS",
                 "build_wordpress_queries_for_site"]:
        assert hasattr(settings, name), f"Missing settings.{name}"


def test_http_utils_has_all_key_functions():
    from pipeline import http_utils
    for fn in ["fetch_url", "post_json", "canonicalize_url",
               "try_resolve_google_redirect", "html_to_text",
               "extract_published_at", "is_likely_article_url"]:
        assert hasattr(http_utils, fn), f"Missing http_utils.{fn}"


# ═══ F4-T3: Source coverage ═══

def test_all_major_sources_have_collector_path():
    """Every major source from the old HTML snapshot should have at least one
    collector path configured in settings."""
    from pipeline import settings

    wp_hosts = set()
    for site in settings.WORDPRESS_API_SITES:
        url = site.get("base_url", "")
        if "//" in url:
            wp_hosts.add(url.split("//")[1].rstrip("/"))

    internal_hosts = {t.host for t in settings.FLAVIO_INTERNAL_SEARCH_TARGETS}

    scrape_hosts = set()
    if hasattr(settings, "DIRECT_SCRAPE_TARGETS"):
        for t in settings.DIRECT_SCRAPE_TARGETS:
            url = t.search_url_template
            if "//" in url:
                scrape_hosts.add(url.split("//")[1].split("/")[0].replace("www.", ""))

    all_hosts = wp_hosts | internal_hosts | scrape_hosts

    # Major sources that MUST be covered
    must_cover = [
        "diariodorio.com", "agendadopoder.com.br", "vejario.abril.com.br",
        "oglobo.globo.com", "odia.ig.com.br", "camara.rio",
        "extra.globo.com",
    ]

    for host in must_cover:
        found = host in all_hosts or any(host in h for h in all_hosts)
        assert found, f"Source {host} has no collector path in settings"


# ═══ F3-T6: No corrupted files in main directories ═══

def test_no_corrupted_files_in_pipeline():
    """All pipeline/*.py files should compile."""
    pipeline_dir = PROJECT_ROOT / "pipeline"
    for f in pipeline_dir.glob("*.py"):
        py_compile.compile(str(f), doraise=True)


def test_no_corrupted_files_in_tools():
    """All tools/*.py files should compile."""
    tools_dir = PROJECT_ROOT / "tools"
    for f in tools_dir.glob("*.py"):
        py_compile.compile(str(f), doraise=True)


def test_corrupted_files_archived():
    """Corrupted files should be in raw_recovery/."""
    raw = PROJECT_ROOT / "raw_recovery"
    assert raw.exists(), "raw_recovery/ directory should exist"
    # At least some archived files
    archived = list(raw.rglob("*.py")) + list(raw.rglob("*.mjs")) + list(raw.rglob("*.html"))
    assert len(archived) >= 3, f"Expected archived files, found {len(archived)}"
