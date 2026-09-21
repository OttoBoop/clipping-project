"""Public editorial state from an actual page whose lazy DOM was empty."""
import gzip
import hashlib
import json
from pathlib import Path

from web_app.political_editorial_extraction import extract_for_publisher
from web_app.political_estadao_lazy_body import extract

ROOT = Path(__file__).parent / "fixtures" / "political_estadao"


def read():
    case = json.loads((ROOT / "lazy-editorial-manifest.json").read_text())
    raw = gzip.decompress((ROOT / "real-lazy-editorial.html.gz").read_bytes())
    assert hashlib.sha256(raw).hexdigest() == case["htmlHash"]
    return raw.decode(), case["url"]


def test_real_public_html_restores_body_and_date_without_running_scripts():
    raw, url = read()
    result = extract_for_publisher(raw, url)
    assert result["extraction_method"] == "publisher_public_editorial_raw_html"
    assert result["published_at"] == "2026-06-09T20:13:26+00:00"
    assert result["full_text"].startswith("Após um longo período sem novidades, Kingdom Hearts 4")
    assert "Sora explorando Quadratum" in result["full_text"]
    assert result["full_text"].endswith("redes sociais do Voxel!")
    assert "youtube.com" not in result["full_text"]
    assert "data-message-author-role" not in result["full_text"]
    assert len(result["full_text"]) > 2000
    assert result["text_extent"] == "unknown"
    assert result["format_provenance"]["embedded_scripts_executed"] is False


def test_public_state_cannot_supply_another_articles_body():
    raw, url = read()
    assert extract(raw, url + "-different") is None
    assert extract(raw, url.replace("www.estadao.com.br", "unrelated.example")) is None
