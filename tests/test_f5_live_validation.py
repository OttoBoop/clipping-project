"""Tests for F5: Targeted live validation.

F5-T1: Test oracle extraction from old HTML snapshot
F5-T2..F5-T6: Individual collector validation (added later)
F5-T7: Full E2E pipeline run
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ═══ F5-T1: Test oracle exists and has required structure ═══

def test_oracle_file_exists():
    oracle_path = PROJECT_ROOT / "data" / "test_oracle.json"
    assert oracle_path.exists(), "data/test_oracle.json not found"


def test_oracle_has_at_least_5_sources():
    oracle_path = PROJECT_ROOT / "data" / "test_oracle.json"
    with open(oracle_path, "r", encoding="utf-8") as f:
        oracle = json.load(f)
    assert isinstance(oracle, dict), "Oracle should be a dict of {source: [urls]}"
    assert len(oracle) >= 5, f"Expected ≥5 sources, got {len(oracle)}: {list(oracle.keys())}"


def test_oracle_has_at_least_50_total_urls():
    oracle_path = PROJECT_ROOT / "data" / "test_oracle.json"
    with open(oracle_path, "r", encoding="utf-8") as f:
        oracle = json.load(f)
    total = sum(len(v) for v in oracle.values())
    assert total >= 50, f"Expected ≥50 total URLs, got {total}"


def test_oracle_has_key_sources():
    """The old HTML snapshot had these major sources."""
    oracle_path = PROJECT_ROOT / "data" / "test_oracle.json"
    with open(oracle_path, "r", encoding="utf-8") as f:
        oracle = json.load(f)
    required = ["diariodorio.com", "agendadopoder.com.br", "vejario.abril.com.br",
                "oglobo.globo.com", "odia.ig.com.br"]
    for source in required:
        assert source in oracle, f"Missing required source: {source}"
        assert len(oracle[source]) >= 1, f"Source {source} has no URLs"


def test_oracle_entries_have_url_title_date():
    """Each oracle entry should be a dict with url, title, date keys."""
    oracle_path = PROJECT_ROOT / "data" / "test_oracle.json"
    with open(oracle_path, "r", encoding="utf-8") as f:
        oracle = json.load(f)
    for source, entries in oracle.items():
        assert isinstance(entries, list), f"Source {source} value should be a list"
        for entry in entries[:3]:  # spot check first 3
            assert isinstance(entry, dict), f"Entry in {source} should be dict, got {type(entry)}"
            assert "url" in entry, f"Entry in {source} missing 'url' key"
            assert "title" in entry, f"Entry in {source} missing 'title' key"
            assert "date" in entry, f"Entry in {source} missing 'date' key"
            assert entry["url"].startswith("http"), f"URL doesn't start with http: {entry['url'][:50]}"


def test_oracle_most_entries_have_dates():
    """Most oracle entries should have dates for targeted date-range validation."""
    oracle_path = PROJECT_ROOT / "data" / "test_oracle.json"
    with open(oracle_path, "r", encoding="utf-8") as f:
        oracle = json.load(f)
    total = sum(len(v) for v in oracle.values())
    with_dates = sum(1 for entries in oracle.values() for e in entries if e.get("date"))
    ratio = with_dates / total if total else 0
    assert ratio >= 0.8, f"Only {with_dates}/{total} ({ratio:.0%}) entries have dates, need ≥80%"
