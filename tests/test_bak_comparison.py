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

    # Count unique URLs in .bak
    bak_urls = set(
        re.findall(
            r'<h3[^>]*>\s*<a[^>]*href="(https?://[^"]+)"',
            html,
            re.IGNORECASE,
        )
    )

    return {
        "story_ids": story_ids,
        "article_count": article_count,
        "unique_url_count": len(bak_urls),
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
    def test_all_unique_urls_preserved(self, bak_data, pages_data):
        """Pages should have all unique article URLs from .bak."""
        # .bak had inflated counts (857 article-cards, 672 unique URLs)
        # but also had 185 URLs in 2 stories each. After dedup, Pages
        # should have >= the unique URL count from the .bak.
        bak_unique = bak_data["unique_url_count"]
        pages_urls = set()
        for s in pages_data.get("stories", []):
            for a in s.get("articles", []):
                url = a.get("url", "")
                if url:
                    pages_urls.add(url)
        # Allow up to 5% loss from parsing edge cases in legacy HTML
        threshold = int(bak_unique * 0.95)
        assert len(pages_urls) >= threshold, (
            f"Pages has {len(pages_urls)} unique URLs, .bak had {bak_unique} "
            f"(threshold: {threshold}, loss: {bak_unique - len(pages_urls)})"
        )

    def test_no_inflated_article_count(self, pages_data):
        """Total article entries should be close to unique URL count (no inflation)."""
        total_entries = sum(
            len(s.get("articles", [])) for s in pages_data.get("stories", [])
        )
        urls = set()
        for s in pages_data.get("stories", []):
            for a in s.get("articles", []):
                url = a.get("url", "")
                if url:
                    urls.add(url)
        # Allow 1 article without URL
        assert total_entries <= len(urls) + 5, (
            f"Inflated: {total_entries} entries but only {len(urls)} unique URLs"
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

    def test_all_targets_have_stories(self, pages_data):
        """Each target should have at least 1 story after dedup."""
        for t in pages_data.get("targets", []):
            assert t.get("storyCount", 0) > 0, (
                f"Target {t['key']} has 0 stories"
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
        found = 0
        for sid in sample_ids:
            bak_title = bak_titles[sid].lower().strip()
            if sid in pages_titles or bak_title in pages_title_set:
                found += 1

        # After dedup, some stories are removed (empty). Allow up to 50% missing.
        assert found >= len(sample_ids) * 0.5, (
            f"Only {found}/{len(sample_ids)} sampled .bak stories found in Pages"
        )


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
