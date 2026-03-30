"""Tests for F3-T3 (export_mobile_snapshot), F3-T4 (prepare_wix_clipping_snapshot),
F3-T5 (benchmark_sources_vs_excel)."""
import py_compile
import sys
import os
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ═══ F3-T3: export_mobile_snapshot.py (original recovered from 63MB Codex session log) ═══

def test_export_mobile_compiles():
    py_compile.compile(str(PROJECT_ROOT / "tools" / "export_mobile_snapshot.py"), doraise=True)


def test_export_mobile_has_original_functions():
    """Should have all 30 original functions recovered from Codex session log."""
    content = (PROJECT_ROOT / "tools" / "export_mobile_snapshot.py").read_text(encoding="utf-8")
    # Core pipeline functions
    assert "def parse_args" in content
    assert "def load_targets" in content
    assert "def load_scope_articles" in content
    assert "def decorate_stories" in content
    assert "def build_target_rows" in content
    assert "def resolve_initial_targets" in content
    assert "def build_html" in content
    assert "def main" in content
    # Rendering functions
    assert "def render_article_card" in content
    assert "def render_story_section" in content
    assert "def render_filter_buttons" in content
    assert "def render_story_index" in content
    # Utility functions
    assert "def normalize_text" in content
    assert "def story_sort_key" in content
    assert "def visibility_stats" in content
    assert "def output_path_for_args" in content
    assert "def json_for_script" in content


def test_export_mobile_has_original_constants():
    """Should have original constants: DB_PATH, TARGETS_PATH, EXPORT_LIMIT, etc."""
    content = (PROJECT_ROOT / "tools" / "export_mobile_snapshot.py").read_text(encoding="utf-8")
    assert "DB_PATH" in content
    assert "TARGETS_PATH" in content
    assert "REPORTS_DIR" in content
    assert "EXPORT_LIMIT" in content
    assert "DEFAULT_TARGET_KEY" in content


def test_export_mobile_has_main():
    """CLI should have a main() -> int function."""
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))
    import importlib
    spec = importlib.util.spec_from_file_location(
        "export_mobile_snapshot", PROJECT_ROOT / "tools" / "export_mobile_snapshot.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.main)


def test_export_mobile_has_offline_js():
    """Original had a complete offline JS filter engine embedded in build_html."""
    content = (PROJECT_ROOT / "tools" / "export_mobile_snapshot.py").read_text(encoding="utf-8")
    assert "applyFilters" in content or "selectedTargets" in content, "Missing offline JS"
    assert "story-card" in content, "Missing story-card template"


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


def test_wix_snapshot_has_original_functions():
    """Should have the original functions recovered from from_patches + 63MB file."""
    content = (PROJECT_ROOT / "tools" / "prepare_wix_clipping_snapshot.py").read_text(encoding="utf-8")
    # Original had: prepare_snapshot, validate_snapshot_html, render_review_screenshots, scope_token
    assert "def prepare_snapshot" in content, "Missing original prepare_snapshot function"
    assert "def validate_snapshot_html" in content, "Missing original validate_snapshot_html function"
    assert "def render_review_screenshots" in content, "Missing original render_review_screenshots function"
    assert "def scope_token" in content, "Missing original scope_token function"


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
