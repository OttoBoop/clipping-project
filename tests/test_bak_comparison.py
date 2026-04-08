"""Compare regenerated Pages data against the .bak historical reference.

Ensures no data loss during migration from monolithic HTML to Pages bundle.

Run with:
    pytest tests/test_bak_comparison.py -v
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BAK_PATH = ROOT / "data" / "reports" / "clipping_historias_completo.html.bak"
DATA_PATH = ROOT / "assets" / "clipping-data.json"
RAW_PATH = ROOT / "assets" / "clipping-raw-texts.json"


@pytest.fixture(scope="module")
def bak_data():
    """Parse the .bak HTML to extract story/article data."""
    if not BAK_PATH.exists():
        pytest.skip(".bak reference file not found")
    html = BAK_PATH.read_text(encoding="utf-8")

    # Extract payload
    m = re.search(
        r'<script id="snapshot-payload"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    payload = json.loads(m.group(1)) if m else {}

    # Count stories and articles from DOM
    story_ids = set(re.findall(r'data-story-id="(\d+)"', html))
    article_count = len(re.findall(r'class="article-card"', html))

    # Extract target info from storyTargets
    story_targets = payload.get("storyTargets", {})
    target_story_counts = {}
    for sid, keys in story_targets.items():
        for k in keys:
            target_story_counts[k] = target_story_counts.get(k, 0) + 1

    # Extract story titles from DOM
    titles = {}
    for m_title in re.finditer(
        r'data-story-id="(\d+)".*?<h2>(.*?)</h2>', html, re.DOTALL
    ):
        sid = m_title.group(1)
        title = re.sub(r"<[^>]+>", "", m_title.group(2)).strip()
        titles[sid] = title

    return {
        "story_ids": story_ids,
        "article_count": article_count,
        "target_story_counts": target_story_counts,
        "payload_targets": payload.get("targets", []),
        "titles": titles,
    }


@pytest.fixture(scope="module")
def pages_data():
    """Load the regenerated Pages data.json."""
    if not DATA_PATH.exists():
        pytest.skip("Pages data.json not found")
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def raw_texts():
    """Load the raw texts JSON."""
    if not RAW_PATH.exists():
        pytest.skip("Raw texts JSON not found")
    return json.loads(RAW_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDataCompleteness:
    def test_story_count_gte_bak(self, bak_data, pages_data):
        """Pages data should have at least as many stories as .bak."""
        bak_count = len(bak_data["story_ids"])
        pages_count = len(pages_data.get("stories", []))
        assert pages_count >= bak_count, (
            f"Pages has {pages_count} stories, .bak had {bak_count}"
        )

    def test_article_count_gte_bak(self, bak_data, pages_data):
        """Pages data should have at least as many articles as .bak."""
        bak_count = bak_data["article_count"]
        pages_count = sum(
            len(s.get("articles", [])) for s in pages_data.get("stories", [])
        )
        assert pages_count >= bak_count, (
            f"Pages has {pages_count} articles, .bak had {bak_count}"
        )


class TestTargets:
    def test_all_bak_targets_present(self, bak_data, pages_data):
        """All target keys from .bak storyTargets should exist in Pages targets."""
        bak_keys = set(bak_data["target_story_counts"].keys())
        pages_keys = {t["key"] for t in pages_data.get("targets", [])}
        missing = bak_keys - pages_keys
        assert not missing, f"Missing targets in Pages: {missing}"

    def test_four_targets(self, pages_data):
        """Pages should have exactly 4 targets."""
        targets = pages_data.get("targets", [])
        keys = {t["key"] for t in targets}
        expected = {"flavio_valle", "pedro_duarte", "pedro_angelito", "bernardo_rubiao"}
        assert keys == expected, f"Expected {expected}, got {keys}"

    def test_pedro_duarte_not_primary(self, pages_data):
        """Pedro Duarte should be primary=false."""
        for t in pages_data.get("targets", []):
            if t["key"] == "pedro_duarte":
                assert not t.get("primary"), "pedro_duarte should not be primary"
                return
        pytest.fail("pedro_duarte not found in targets")

    def test_target_story_counts_gte_bak(self, bak_data, pages_data):
        """Each target's story count should be >= .bak's count."""
        pages_counts = {}
        for t in pages_data.get("targets", []):
            pages_counts[t["key"]] = t.get("storyCount", 0)
        for key, bak_count in bak_data["target_story_counts"].items():
            pages_count = pages_counts.get(key, 0)
            assert pages_count >= bak_count, (
                f"Target {key}: Pages has {pages_count} stories, .bak had {bak_count}"
            )


class TestRawTexts:
    def test_raw_texts_not_empty(self, raw_texts):
        """Raw texts file should have entries."""
        assert len(raw_texts) > 0, "No raw texts found"

    def test_raw_texts_gte_bak_article_count(self, bak_data, raw_texts):
        """Should have raw texts for most articles."""
        # Not every article has raw text, but should have a substantial number
        assert len(raw_texts) >= bak_data["article_count"] * 0.5, (
            f"Only {len(raw_texts)} raw texts for {bak_data['article_count']} .bak articles"
        )


class TestTitleSpotCheck:
    def test_random_titles_match(self, bak_data, pages_data):
        """Spot-check: 10 random .bak story titles should appear in Pages data."""
        bak_titles = bak_data["titles"]
        if len(bak_titles) < 10:
            pytest.skip("Not enough stories for spot check")

        pages_titles = {
            str(s.get("storyIdInt", "")): s.get("title", "")
            for s in pages_data.get("stories", [])
        }
        # Also index by title text for fuzzy matching
        pages_title_set = {t.lower().strip() for t in pages_titles.values() if t}

        sample_ids = random.sample(sorted(bak_titles.keys()), min(10, len(bak_titles)))
        missing = []
        for sid in sample_ids:
            bak_title = bak_titles[sid].lower().strip()
            # Check by ID or by title text
            if sid in pages_titles:
                continue
            if bak_title in pages_title_set:
                continue
            missing.append(f"Story {sid}: {bak_titles[sid][:60]}")

        assert not missing, f"Missing stories:\n" + "\n".join(missing)


class TestNoDuplicateUrls:
    def test_no_url_dups_within_story(self, pages_data):
        """No story should have duplicate article URLs."""
        dups_found = []
        for story in pages_data.get("stories", []):
            urls = [a.get("url", "") for a in story.get("articles", []) if a.get("url")]
            seen = set()
            for url in urls:
                if url in seen:
                    dups_found.append(
                        f"Story {story.get('storyIdInt')}: duplicate URL {url[:80]}"
                    )
                seen.add(url)
        assert not dups_found, f"Duplicate URLs found:\n" + "\n".join(dups_found[:10])
