"""Tests for Wave 2: Clean and restore pipeline core modules."""
import json
import py_compile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# --- F2-T1: settings.py ---

def test_settings_compiles():
    py_compile.compile(str(PROJECT_ROOT / "pipeline" / "settings.py"), doraise=True)


def test_settings_has_all_search_targets():
    from pipeline.settings import FLAVIO_INTERNAL_SEARCH_TARGETS
    # Original uses source_name, not name
    names = {t.source_name for t in FLAVIO_INTERNAL_SEARCH_TARGETS}
    # Original has fewer targets — at minimum O Globo and Veja Rio
    assert len(names) >= 3, f"Expected ≥3 search targets, got {len(names)}: {names}"


def test_settings_has_site_source_configs():
    """Original had per-site source configs like EXTRA_SITE_SOURCE, ODIA_SITE_SOURCE."""
    import pipeline.settings as settings
    assert hasattr(settings, "SITEMAP_CONFIGS"), "Missing SITEMAP_CONFIGS"
    assert hasattr(settings, "WORDPRESS_HOSTS") or hasattr(settings, "WORDPRESS_API_SITES"), (
        "Missing WordPress config"
    )


def test_settings_has_vejario_in_targets():
    """Original had Veja Rio configured for internal search."""
    from pipeline.settings import FLAVIO_INTERNAL_SEARCH_TARGETS
    hosts = {t.host for t in FLAVIO_INTERNAL_SEARCH_TARGETS}
    assert "vejario.abril.com.br" in hosts, f"Missing vejario, got hosts: {hosts}"


# --- F2-T2: http_utils.py ---

def test_http_utils_compiles():
    py_compile.compile(str(PROJECT_ROOT / "pipeline" / "http_utils.py"), doraise=True)


def test_http_utils_has_fetch_url():
    from pipeline.http_utils import fetch_url
    assert callable(fetch_url)


def test_http_utils_has_post_json():
    from pipeline.http_utils import post_json
    assert callable(post_json)


def test_http_utils_has_try_resolve_google_redirect():
    from pipeline.http_utils import try_resolve_google_redirect
    assert callable(try_resolve_google_redirect)


# --- F2-T3: normalization.py ---

def test_normalization_compiles():
    py_compile.compile(str(PROJECT_ROOT / "pipeline" / "normalization.py"), doraise=True)


def test_normalization_has_normalize_url():
    from pipeline.normalization import normalize_url
    assert callable(normalize_url)


def test_normalization_has_clean_title():
    from pipeline.normalization import clean_title
    assert callable(clean_title)


def test_normalization_strips_utm_params():
    from pipeline.normalization import normalize_url
    url = "https://diariodorio.com/article?utm_source=x&utm_medium=y"
    result = normalize_url(url)
    assert "utm_source" not in result
    assert "utm_medium" not in result


# --- F2-T4: matcher.py ---

def test_matcher_compiles():
    py_compile.compile(str(PROJECT_ROOT / "pipeline" / "matcher.py"), doraise=True)


def test_matcher_has_target_dataclass():
    from pipeline.matcher import Target
    t = Target(key="test", label="Test", display_name="Test", keywords=["test"])
    assert t.key == "test"


def test_matcher_has_citation_matcher():
    from pipeline.matcher import CitationMatcher, Target
    targets = [Target(key="fv", label="FV", display_name="FV", keywords=["Flavio Valle"])]
    matcher = CitationMatcher(targets)
    hits = matcher.find_hits("O vereador Flavio Valle participou da sessao")
    assert len(hits) > 0
    assert hits[0].target_key == "fv"


def test_matcher_supports_exact_aliases():
    """Original matcher had exact_aliases support on Target."""
    from pipeline.matcher import Target
    t = Target(
        key="fv", label="FV", display_name="FV",
        keywords=["Flavio Valle"],
        exact_aliases=["Flavio Vale"],
    )
    assert hasattr(t, "exact_aliases")
    assert "Flavio Vale" in t.exact_aliases


# --- F2-T5: database.py ---

def test_database_compiles():
    py_compile.compile(str(PROJECT_ROOT / "pipeline" / "database.py"), doraise=True)


def test_database_creates_all_tables():
    from pipeline.database import ClippingDB
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        with ClippingDB(db_path) as db:
            tables = [row[0] for row in db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
        assert "articles" in tables
        assert "mentions" in tables
        assert "story_articles" in tables
    finally:
        os.unlink(db_path)


def test_database_insert_and_query():
    from pipeline.database import ClippingDB
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        with ClippingDB(db_path) as db:
            aid = db.insert_article(
                url="https://example.com/test",
                title="Test Article",
                source_name="TestSource",
                source_type="test",
                published_at="2026-03-30T12:00:00",
                snippet="Test snippet",
            )
            assert aid is not None
            db.insert_mention(aid, "fv", "Flavio Valle", "Flavio Valle")
            articles = db.list_articles_for_export()
            assert len(articles) >= 1
    finally:
        os.unlink(db_path)


# --- F3-T2: targets.json ---

def test_targets_json_exists():
    targets_path = PROJECT_ROOT / "data" / "targets.json"
    assert targets_path.exists(), f"targets.json not found at {targets_path}"


def test_targets_json_has_flavio_valle():
    """targets.json should have at least flavio_valle. Other targets are in settings.py."""
    targets_path = PROJECT_ROOT / "data" / "targets.json"
    with open(targets_path, "r", encoding="utf-8") as f:
        targets = json.load(f)
    assert len(targets) >= 1, f"Expected ≥1 targets, got {len(targets)}"
    keys = {t["key"] for t in targets}
    assert "flavio_valle" in keys


def test_targets_json_has_keywords():
    targets_path = PROJECT_ROOT / "data" / "targets.json"
    with open(targets_path, "r", encoding="utf-8") as f:
        targets = json.load(f)
    for t in targets:
        assert len(t.get("keywords", [])) >= 1, f"Target {t['key']} has no keywords"
