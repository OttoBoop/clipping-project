"""Tests that the forensic audit covers every file in the project and from_patches sources."""
import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
INVENTORY_PATH = PROJECT_ROOT / "docs" / "FORENSIC_INVENTORY.md"

# Every file that MUST appear in the inventory
FROM_PATCHES_ROOT = Path("D:/recovery/CLIPPING_PROJECT/from_patches")
CLIPPING_EXTRACTED_ROOT = Path("D:/recovery/CLIPPING_EXTRACTED")


def _read_inventory():
    """Read the forensic inventory markdown."""
    assert INVENTORY_PATH.exists(), f"Inventory file missing: {INVENTORY_PATH}"
    return INVENTORY_PATH.read_text(encoding="utf-8")


# --- F1-T1: Pipeline files audit ---

def test_inventory_covers_all_from_patches_pipeline_files():
    """Every .py file in from_patches/pipeline/ must appear in the inventory."""
    inventory = _read_inventory()
    expected_files = [
        "collectors.py", "database.py", "http_utils.py",
        "ingest.py", "matcher.py", "settings.py",
    ]
    for f in expected_files:
        assert f in inventory, f"from_patches pipeline file '{f}' not mentioned in inventory"


def test_inventory_has_from_patches_line_counts():
    """Inventory must document the from_patches line counts for pipeline files."""
    inventory = _read_inventory()
    # These are the known line counts from from_patches
    expected_counts = {
        "collectors.py": "696",
        "database.py": "361",
        "ingest.py": "426",
        "matcher.py": "116",
        "settings.py": "34",
        "http_utils.py": "77",
    }
    for filename, count in expected_counts.items():
        assert count in inventory, (
            f"Line count {count} for from_patches/{filename} not in inventory"
        )


def test_inventory_has_extractable_functions_section():
    """Inventory must list extractable functions from corrupted files."""
    inventory = _read_inventory()
    assert "Extractable" in inventory, "No 'Extractable' section in inventory"
    # Key functions that must be documented
    key_functions = [
        "IngestionResult",
        "process_candidates",
        "create_or_update_story",
        "render_filter_buttons",
        "render_story_index",
        "render_article_card",
    ]
    for func in key_functions:
        assert func in inventory, f"Key function '{func}' not documented in inventory"


# --- F1-T2: Tools files audit ---

def test_inventory_covers_all_tool_files():
    """Every tool file must appear in the inventory."""
    inventory = _read_inventory()
    tool_files = [
        "export_mobile_snapshot.py",
        "benchmark_sources_vs_excel.py",
        "benchmark_auto_vs_excel.py",
        "prepare_wix_clipping_snapshot.py",
        "backfill_google.py",
        "cbn_search_diagnostic.py",
        "fix_encoding.py",
        "generate_flavio_valle_print_pdf.py",
    ]
    for f in tool_files:
        assert f in inventory, f"Tool file '{f}' not mentioned in inventory"


# --- F1-T3: Test files audit ---

def test_inventory_covers_all_test_files():
    """Every test file must appear in the inventory."""
    inventory = _read_inventory()
    test_files = [
        "test_flavio_query_expansion.py",
        "test_run_ingestion_dedup.py",
        "test_source_recovery_collectors.py",
        "test_cbn_source_recovery.py",
        "test_internal_site_search_collectors.py",
        "test_http_utils.py",
        "test_odia_r7_site_collectors.py",
        "test_benchmark_sources_vs_excel.py",
        "test_direct_scrape_windows.py",
        "test_export_mobile_snapshot.py",
        "test_globo_family_diagnostic.py",
        "test_google_news_collector.py",
        "test_internal_site_search_ingest.py",
        "test_wordpress_site_collectors.py",
    ]
    for f in test_files:
        assert f in inventory, f"Test file '{f}' not mentioned in inventory"


def test_inventory_documents_html_selectors():
    """Inventory must note recoverable HTML selectors from test files."""
    inventory = _read_inventory()
    # These selectors were found in test_internal_site_search_collectors.py
    selectors = [
        "dl.search-results",     # Camara
        "article.uk-article",    # CONIB
    ]
    for sel in selectors:
        assert sel in inventory, f"HTML selector '{sel}' not documented in inventory"


# --- F1-T4: Non-py files + CLIPPING_EXTRACTED comparison ---

def test_inventory_covers_non_py_files():
    """Inventory must cover non-.py files."""
    inventory = _read_inventory()
    non_py_files = [
        "targets.json",
        "README.md",
        "RECOVERY_NOTES.md",
        "requirements.txt",
    ]
    for f in non_py_files:
        assert f in inventory, f"Non-py file '{f}' not in inventory"


def test_inventory_has_from_patches_vs_current_comparison():
    """Inventory must compare from_patches sizes against current project."""
    inventory = _read_inventory()
    # Must mention both extraction directories
    assert "from_patches" in inventory, "No mention of from_patches directory"
    assert "CLIPPING_EXTRACTED" in inventory or "CLIPPING_PROJECT" in inventory, (
        "No mention of extraction source directories"
    )


def test_inventory_has_classification_categories():
    """Inventory must use the defined classification categories."""
    inventory = _read_inventory()
    categories = [
        "RECONSTRUCTED",
        "RECOVERED_CORRUPTED",
        "STUB",
        "WRONG_CONTENT",
    ]
    for cat in categories:
        assert cat in inventory, f"Classification category '{cat}' not in inventory"


def test_inventory_has_recovery_priority_recommendations():
    """Inventory must have prioritized recovery recommendations."""
    inventory = _read_inventory()
    assert "Priority" in inventory, "No priority recommendations in inventory"


# --- F1-T5: Cross-reference gap list ---

def test_inventory_has_cross_reference_gap_list():
    """Inventory must have a gap list of missing functions."""
    inventory = _read_inventory()
    assert "Missing Original Functions" in inventory or "Gap List" in inventory, (
        "No cross-reference gap list in inventory"
    )


def test_gap_list_covers_key_missing_functions():
    """Gap list must include the most important missing functions."""
    inventory = _read_inventory()
    critical_functions = [
        "IngestionResult",
        "process_candidates",
        "create_or_update_story",
        "render_filter_buttons",
        "render_article_card",
        "select_targets",
        "prepare_snapshot",
    ]
    for func in critical_functions:
        assert func in inventory, f"Critical missing function '{func}' not in gap list"


def test_inventory_documents_cross_file_contamination():
    """Inventory must document the cross-file contamination issue."""
    inventory = _read_inventory()
    assert "contamination" in inventory.lower() or "misnamed" in inventory.lower(), (
        "Cross-file contamination not documented in inventory"
    )


def test_inventory_documents_lost_tools():
    """Inventory must document tools that are completely lost."""
    inventory = _read_inventory()
    lost_tools = [
        "backfill_google.py",
        "cbn_search_diagnostic.py",
        "fix_encoding.py",
        "generate_flavio_valle_print_pdf.py",
    ]
    for tool in lost_tools:
        assert tool in inventory, f"Lost tool '{tool}' not documented"
