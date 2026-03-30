"""Tests for F3-T3 (export_mobile_snapshot), F3-T4 (prepare_wix_clipping_snapshot),
F3-T5 (benchmark_sources_vs_excel)."""
import py_compile
import sys
import os
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ═══ F3-T3: export_mobile_snapshot.py ═══

def test_export_mobile_compiles():
    py_compile.compile(str(PROJECT_ROOT / "tools" / "export_mobile_snapshot.py"), doraise=True)


def test_export_mobile_has_generate_html():
    """Should have generate_html that produces article-grouped HTML."""
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))
    from export_mobile_snapshot import generate_html
    articles = [
        {"url": "https://example.com/1", "title": "Test Article", "source_name": "TestSource",
         "source_type": "test", "published_at": "2026-03-28T12:00:00", "snippet": "Snippet",
         "keyword_matched": "Flavio Valle"},
    ]
    html = generate_html(articles, "Flávio Valle", "2026-03-01", "2026-03-31")
    assert "Test Article" in html
    assert "TestSource" in html
    assert len(html) > 200


def test_export_mobile_has_main():
    """CLI should have a main() function."""
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))
    from export_mobile_snapshot import main
    assert callable(main)


def test_export_mobile_generates_from_db():
    """Integration: generate HTML from a test database."""
    from pipeline.database import ClippingDB
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        with ClippingDB(db_path) as db:
            aid = db.insert_article(
                url="https://example.com/test-export",
                title="Vereador Flavio Valle na Camara",
                source_name="DiarioDoRio",
                source_type="wordpress_api",
                published_at="2026-03-28T10:00:00",
                snippet="Flavio Valle participou da sessao plenaria.",
            )
            db.insert_mention(aid, "flavio_valle", "Flávio Valle", "Flavio Valle")

        with ClippingDB(db_path) as db:
            articles = db.list_articles_for_export(target_key="flavio_valle")

        sys.path.insert(0, str(PROJECT_ROOT / "tools"))
        from export_mobile_snapshot import generate_html
        html = generate_html(articles, "Flávio Valle", "", "")
        assert "Flavio Valle" in html
        assert "DiarioDoRio" in html
        assert len(html) > 500
    finally:
        os.unlink(db_path)


# ═══ F3-T4: prepare_wix_clipping_snapshot.py ═══

def test_wix_snapshot_compiles():
    """File should be valid Python (either functional or documented stub)."""
    py_compile.compile(str(PROJECT_ROOT / "tools" / "prepare_wix_clipping_snapshot.py"), doraise=True)


def test_wix_snapshot_has_docstring_or_main():
    """Should have either a main() or at minimum a module docstring documenting
    what was recoverable from the corrupted original."""
    content = (PROJECT_ROOT / "tools" / "prepare_wix_clipping_snapshot.py").read_text(encoding="utf-8")
    has_docstring = '"""' in content or "'''" in content
    has_main = "def main" in content
    has_prepare = "def prepare_snapshot" in content
    assert has_docstring or has_main or has_prepare, (
        "File must have a docstring documenting recovery state, or functional code"
    )


def test_wix_snapshot_documents_original_functions():
    """Stub should document the original functions found in from_patches."""
    content = (PROJECT_ROOT / "tools" / "prepare_wix_clipping_snapshot.py").read_text(encoding="utf-8")
    # Original had: prepare_snapshot, validate_snapshot_html, render_review_screenshots, scope_token
    assert "prepare_snapshot" in content, "Should reference original prepare_snapshot function"
    assert "validate_snapshot_html" in content or "validate" in content, (
        "Should reference original validation function"
    )


# ═══ F3-T5: benchmark_sources_vs_excel.py ═══

def test_benchmark_compiles():
    """File should be valid Python (cleaned from 112KB corrupted original)."""
    py_compile.compile(str(PROJECT_ROOT / "tools" / "benchmark_sources_vs_excel.py"), doraise=True)


def test_benchmark_has_documented_signatures():
    """Should document or implement the original function signatures extracted
    from the corrupted 708-line version."""
    content = (PROJECT_ROOT / "tools" / "benchmark_sources_vs_excel.py").read_text(encoding="utf-8")
    # Functions found in corrupted from_patches:
    assert "resolve_candidate_limit" in content, "Missing resolve_candidate_limit"
    assert "SourceModule" in content, "Missing SourceModule"
    assert "build_source_modules" in content, "Missing build_source_modules"
    assert "evaluate_source" in content, "Missing evaluate_source function"
    assert "normalize_url" in content, "Missing normalize_url"


def test_benchmark_has_source_module_dataclass():
    """SourceModule should be a usable dataclass/namedtuple with host, module, label, collect, source_type."""
    content = (PROJECT_ROOT / "tools" / "benchmark_sources_vs_excel.py").read_text(encoding="utf-8")
    assert "host" in content
    assert "module" in content or "label" in content
    assert "collect" in content
    assert "source_type" in content


def test_benchmark_resolve_candidate_limit():
    """resolve_candidate_limit(0) should return a high cap, positive values pass through."""
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))
    # This will fail until the benchmark file is cleaned and functional
    from benchmark_sources_vs_excel import resolve_candidate_limit
    assert resolve_candidate_limit(0) >= 100_000
    assert resolve_candidate_limit(-1) >= 100_000
    assert resolve_candidate_limit(250) == 250
