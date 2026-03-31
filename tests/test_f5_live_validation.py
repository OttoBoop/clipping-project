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


def test_oracle_urls_are_strings():
    oracle_path = PROJECT_ROOT / "data" / "test_oracle.json"
    with open(oracle_path, "r", encoding="utf-8") as f:
        oracle = json.load(f)
    for source, urls in oracle.items():
        assert isinstance(urls, list), f"Source {source} value should be a list"
        for url in urls[:3]:  # spot check first 3
            assert isinstance(url, str), f"URL in {source} should be string, got {type(url)}"
            assert url.startswith("http"), f"URL in {source} doesn't start with http: {url[:50]}"
