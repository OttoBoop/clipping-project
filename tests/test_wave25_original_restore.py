"""Tests for Wave 2.5: Restore pipeline originals from 63MB Codex session log.

F2-T5b: database.py — original 361 lines with story_with_articles()
F2-T1b: settings.py — WORDPRESS_API_SITES, get_active_targets, etc.
F2-T2b: http_utils.py — canonicalize_url
"""
import py_compile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ═══ F2-T5b: database.py original restoration ═══

def test_database_compiles():
    py_compile.compile(str(PROJECT_ROOT / "pipeline" / "database.py"), doraise=True)


def test_database_has_story_with_articles():
    """Original had story_with_articles() — returns stories with their linked articles."""
    from pipeline.database import ClippingDB
    assert hasattr(ClippingDB, "story_with_articles"), "Missing story_with_articles method"


def test_database_line_count():
    """Original was 361 lines. Current rewrite is 114. Should be ≥250 after restoration."""
    content = (PROJECT_ROOT / "pipeline" / "database.py").read_text(encoding="utf-8")
    lines = len(content.strip().splitlines())
    assert lines >= 250, f"database.py is {lines} lines — too short, original was 361"


def test_database_has_original_methods():
    """Original had richer query methods beyond the simplified rewrite."""
    content = (PROJECT_ROOT / "pipeline" / "database.py").read_text(encoding="utf-8")
    # story_with_articles is the key missing method
    assert "story_with_articles" in content, "Missing story_with_articles"
    # Original had article_id in export query results
    assert "article_id" in content, "Missing article_id in queries"


def test_database_story_with_articles_returns_list():
    """story_with_articles() should return a list of story dicts with articles."""
    import tempfile, os
    from pathlib import Path
    from pipeline.database import ClippingDB
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = ClippingDB(db_path)
        result = db.story_with_articles()
        assert isinstance(result, list), "story_with_articles should return a list"


# ═══ F2-T1b: settings.py original restoration ═══

def test_settings_compiles():
    py_compile.compile(str(PROJECT_ROOT / "pipeline" / "settings.py"), doraise=True)


def test_settings_has_wordpress_api_sites():
    """Original had WORDPRESS_API_SITES — list of dicts with base_url, source_name."""
    content = (PROJECT_ROOT / "pipeline" / "settings.py").read_text(encoding="utf-8")
    assert "WORDPRESS_API_SITES" in content, "Missing WORDPRESS_API_SITES"


def test_settings_has_sitemap_daily_sources():
    """Original had SITEMAP_DAILY_SOURCES."""
    content = (PROJECT_ROOT / "pipeline" / "settings.py").read_text(encoding="utf-8")
    assert "SITEMAP_DAILY_SOURCES" in content, "Missing SITEMAP_DAILY_SOURCES"


def test_settings_has_get_active_targets():
    """Original had get_active_targets() function."""
    content = (PROJECT_ROOT / "pipeline" / "settings.py").read_text(encoding="utf-8")
    assert "def get_active_targets" in content, "Missing get_active_targets function"


def test_settings_has_build_wordpress_queries():
    """Original had build_wordpress_queries_for_site()."""
    content = (PROJECT_ROOT / "pipeline" / "settings.py").read_text(encoding="utf-8")
    assert "build_wordpress_queries" in content, "Missing build_wordpress_queries"


def test_settings_has_flavio_search_queries():
    """Original had FLAVIO_INTERNAL_SEARCH_QUERIES."""
    content = (PROJECT_ROOT / "pipeline" / "settings.py").read_text(encoding="utf-8")
    assert "FLAVIO_INTERNAL_SEARCH_QUERIES" in content or "SEARCH_QUERIES" in content, (
        "Missing FLAVIO_INTERNAL_SEARCH_QUERIES"
    )


def test_settings_has_vejario_archive_targets():
    """Original had VEJARIO_ARCHIVE_TARGETS."""
    content = (PROJECT_ROOT / "pipeline" / "settings.py").read_text(encoding="utf-8")
    assert "VEJARIO_ARCHIVE" in content, "Missing VEJARIO_ARCHIVE_TARGETS"


def test_settings_has_camara_archive_target():
    """Original had CAMARA_ARCHIVE_TARGET."""
    content = (PROJECT_ROOT / "pipeline" / "settings.py").read_text(encoding="utf-8")
    assert "CAMARA_ARCHIVE" in content, "Missing CAMARA_ARCHIVE_TARGET"


# ═══ F2-T2b: http_utils.py original restoration ═══

def test_http_utils_compiles():
    py_compile.compile(str(PROJECT_ROOT / "pipeline" / "http_utils.py"), doraise=True)


def test_http_utils_has_canonicalize_url():
    """Original had canonicalize_url — used by benchmark_sources_vs_excel."""
    content = (PROJECT_ROOT / "pipeline" / "http_utils.py").read_text(encoding="utf-8")
    assert "def canonicalize_url" in content, "Missing canonicalize_url function"


def test_http_utils_canonicalize_url_importable():
    """canonicalize_url should be importable from pipeline.http_utils."""
    from pipeline.http_utils import canonicalize_url
    assert callable(canonicalize_url)


def test_http_utils_canonicalize_url_normalizes():
    """canonicalize_url should normalize URLs — strip trailing slashes and query params."""
    from pipeline.http_utils import canonicalize_url
    result = canonicalize_url("https://example.com/path/")
    assert result.endswith("/path"), "Should strip trailing slash"
    assert "?" not in canonicalize_url("https://example.com/path?utm=x"), "Should strip query"
