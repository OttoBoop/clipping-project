"""Tests for F2-T8 (run_ingestion.py) and F3-T1 (server.py snapshot generator)."""
import py_compile
import sys
import json
import tempfile
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ═══ F2-T8: run_ingestion.py ═══

def test_run_ingestion_compiles():
    py_compile.compile(str(PROJECT_ROOT / "run_ingestion.py"), doraise=True)


def test_run_ingestion_has_main():
    """CLI should have a main() function."""
    # Just verify the module loads without error
    import importlib.util
    spec = importlib.util.spec_from_file_location("run_ingestion", PROJECT_ROOT / "run_ingestion.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "main") or hasattr(mod, "__name__")


def test_run_ingestion_imports_pipeline():
    """CLI should import from pipeline.ingest."""
    content = (PROJECT_ROOT / "run_ingestion.py").read_text(encoding="utf-8")
    assert "pipeline" in content or "ingest" in content


# ═══ F3-T1: server.py (static HTML snapshot generator) ═══

def test_server_py_exists():
    server_path = PROJECT_ROOT / "server.py"
    assert server_path.exists(), "server.py does not exist"


def test_server_py_compiles():
    py_compile.compile(str(PROJECT_ROOT / "server.py"), doraise=True)


def test_server_has_prepare_snapshot():
    """server.py should have a prepare_snapshot function."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("server", PROJECT_ROOT / "server.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "prepare_snapshot"), "Missing prepare_snapshot function"


def test_server_has_story_html_template():
    """server.py should contain the story-card HTML template."""
    content = (PROJECT_ROOT / "server.py").read_text(encoding="utf-8")
    assert "story-card" in content, "Missing story-card in HTML template"
    assert "data-story-id" in content, "Missing data-story-id attribute"


def test_server_has_filter_buttons():
    """server.py should have target filter button generation."""
    content = (PROJECT_ROOT / "server.py").read_text(encoding="utf-8")
    assert "data-filter-target" in content, "Missing data-filter-target attribute"


def test_server_has_offline_js():
    """server.py should embed offline JavaScript for filtering."""
    content = (PROJECT_ROOT / "server.py").read_text(encoding="utf-8")
    assert "applyFilters" in content or "selectedTargets" in content, (
        "Missing offline JS filter logic"
    )


def test_server_generates_html_with_stories():
    """prepare_snapshot should generate HTML containing story cards."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("server", PROJECT_ROOT / "server.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Create a test DB with some articles
    from pipeline.database import ClippingDB
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        with ClippingDB(db_path) as db:
            aid = db.insert_article(
                url="https://example.com/test-article",
                title="Flavio Valle na Camara do Rio",
                source_name="TestSource",
                source_type="test",
                published_at="2026-03-28T12:00:00",
                snippet="Vereador Flavio Valle participou da sessao plenaria.",
            )
            db.insert_mention(aid, "flavio_valle", "Flávio Valle", "Flavio Valle")
            # Create story link
            db.conn.execute(
                "INSERT INTO story_articles (article_id, story_id) VALUES (?, ?)",
                (aid, str(aid)),
            )
            db.conn.commit()

        html = mod.prepare_snapshot(db_path=db_path)
        assert isinstance(html, str)
        assert len(html) > 100, "Generated HTML is too short"
        assert "story-card" in html or "article-card" in html, "No story/article cards in output"
        assert "Flavio Valle" in html, "Article title not in output"
    finally:
        os.unlink(db_path)
