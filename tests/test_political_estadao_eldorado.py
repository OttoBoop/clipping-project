"""Real episode HTML: body-only text, related episodes, dates and identity."""
import gzip
import hashlib
import json
from pathlib import Path

from web_app.political_editorial_extraction import extract_for_publisher
from web_app.political_estadao_eldorado import extract

ROOT = Path(__file__).parent / "fixtures" / "political_estadao"
CASES = json.loads((ROOT / "eldorado-manifest.json").read_text())


def read(index=0):
    case = CASES[index]
    data = gzip.decompress((ROOT / case["fixture"]).read_bytes())
    assert hashlib.sha256(data).hexdigest() == case["htmlHash"]
    return data.decode(), case["url"]


def test_real_episode_retains_three_paragraphs_and_original_publication():
    raw, url = read()
    result = extract_for_publisher(raw, url)
    assert result["published_at"] == "2025-08-29T11:41:07.352000+00:00"
    assert result["canonical_url"].rstrip("/") == url
    assert result["title"].startswith("TV 3.0 muda a lógica")
    assert len(result["full_text"].split("\n\n")) == 3
    assert "Luiz Inácio Lula da Silva" in result["full_text"]
    assert result["full_text"].endswith("por 10 a 15 anos.")
    assert "Amyr Klink" not in result["full_text"]
    assert "Novo Desenrola Brasil" not in result["full_text"]
    assert result["publication_date_evidence"]["publisher_republish_date"].startswith("2026-06-10")
    assert result["text_extent"] == "unknown"
    assert result["format_provenance"]["audio_transcribed"] is False


def test_real_music_synopsis_does_not_become_transcript():
    raw, url = read(1)
    result = extract_for_publisher(raw, url)
    assert result["extraction_state"] == "metadata_only"
    assert len(result["full_text"]) == 102
    assert "Egberto Gismonti" not in result["full_text"]


def test_other_episode_or_host_cannot_reuse_page_text():
    raw, url = read()
    assert extract(raw, url + "-different") is None
    assert extract(raw, url.replace("www.estadao.com.br", "unrelated.example")) is None


def test_missing_original_date_never_uses_republish_or_today():
    raw, url = read()
    result = extract(raw.replace('"first_publish_date":', '"unavailable_first_publish_date":'), url)
    assert result["published_at"] == ""
    assert result["publication_date_evidence"]["method"] == "missing_original_post_date"
