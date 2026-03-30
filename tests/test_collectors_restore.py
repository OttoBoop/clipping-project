"""Tests for F2-T6b: Restore original collectors.py from 63MB Codex session log.

The original architecture uses collect_internal_site_search for Camara/Veja Rio/etc.
and collect_direct_scrape for generic site scraping (O Dia, R7, CONIB, etc.).
There are NO separate collect_odia_site/collect_r7_site functions — those were
invented in the simplified rewrite.
"""
import py_compile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_collectors_compiles():
    py_compile.compile(str(PROJECT_ROOT / "pipeline" / "collectors.py"), doraise=True)


def test_collectors_has_candidate_article():
    from pipeline.collectors import CandidateArticle
    c = CandidateArticle(
        url="http://x", title="t", source_name="s", source_type="st",
        published_at="2026-01-01", snippet="snip", metadata={},
    )
    assert c.url == "http://x"
    assert c.source_type == "st"


# --- Original collector functions ---

def test_collectors_has_google_news():
    from pipeline.collectors import collect_google_news
    assert callable(collect_google_news)


def test_collectors_has_rss():
    from pipeline.collectors import collect_rss
    assert callable(collect_rss)


def test_collectors_has_wordpress_api():
    from pipeline.collectors import collect_wordpress_api
    assert callable(collect_wordpress_api)


def test_collectors_has_internal_site_search():
    from pipeline.collectors import collect_internal_site_search
    assert callable(collect_internal_site_search)


def test_collectors_has_direct_scrape():
    """Original used collect_direct_scrape for generic site scraping."""
    from pipeline.collectors import collect_direct_scrape
    assert callable(collect_direct_scrape)


# --- Original helper functions ---

def test_collectors_has_dedupe():
    from pipeline.collectors import _dedupe_candidates_by_url
    assert callable(_dedupe_candidates_by_url)


def test_collectors_has_parse_pt_br_datetime():
    """Original had Portuguese date parsing."""
    from pipeline.collectors import _parse_pt_br_datetime
    assert callable(_parse_pt_br_datetime)


def test_collectors_has_clean_html_fragment():
    """Original had HTML fragment cleaning."""
    from pipeline.collectors import _clean_html_fragment
    assert callable(_clean_html_fragment)


def test_collectors_has_parse_rss_or_atom():
    """Original had RSS/Atom XML parser."""
    from pipeline.collectors import parse_rss_or_atom
    assert callable(parse_rss_or_atom)


def test_collectors_has_fetch_full_article_text():
    """Original had full article text fetcher."""
    from pipeline.collectors import fetch_full_article_text
    assert callable(fetch_full_article_text)


# --- Original regexes for site-specific selectors ---

def test_collectors_has_camara_selectors():
    """Original used dl.search-results for Camara."""
    from pipeline import collectors
    assert hasattr(collectors, "CAMARA_RESULT_RE"), "Missing Camara result regex"


def test_collectors_has_conib_selectors():
    """Original used article.uk-article for CONIB."""
    from pipeline import collectors
    assert hasattr(collectors, "CONIB_ARTICLE_RE"), "Missing CONIB article regex"


def test_collectors_has_vejario_date_re():
    from pipeline import collectors
    assert hasattr(collectors, "VEJARIO_DATE_RE"), "Missing Veja Rio date regex"


def test_collectors_has_pt_months():
    from pipeline.collectors import PT_MONTHS
    assert len(PT_MONTHS) >= 12, "PT_MONTHS should have at least 12 entries"


# --- Functional tests ---

def test_parse_pt_br_datetime_works():
    from pipeline.collectors import _parse_pt_br_datetime
    # Original parses Portuguese month names like "28 marco 2026"
    result = _parse_pt_br_datetime("28 marco 2026")
    assert result != "", f"Should parse Portuguese date, got: {result!r}"
    assert "2026" in result


def test_clean_html_fragment_works():
    from pipeline.collectors import _clean_html_fragment
    result = _clean_html_fragment("<b>Hello</b> <i>world</i>")
    assert "Hello" in result
    assert "world" in result
    assert "<b>" not in result


def test_dedupe_removes_duplicates():
    from pipeline.collectors import CandidateArticle, _dedupe_candidates_by_url
    candidates = [
        CandidateArticle(url="http://a.com/1", title="A", source_name="s",
                         source_type="t", published_at="", snippet="", metadata={}),
        CandidateArticle(url="http://a.com/1", title="A dup", source_name="s",
                         source_type="t", published_at="", snippet="", metadata={}),
        CandidateArticle(url="http://a.com/2", title="B", source_name="s",
                         source_type="t", published_at="", snippet="", metadata={}),
    ]
    result = _dedupe_candidates_by_url(candidates)
    assert len(result) == 2


def test_collectors_line_count():
    """Original was ~696+ lines. Should be substantially larger than the 520-line rewrite."""
    content = (PROJECT_ROOT / "pipeline" / "collectors.py").read_text(encoding="utf-8")
    lines = len(content.strip().splitlines())
    assert lines >= 600, f"collectors.py is {lines} lines — should be ≥600"
