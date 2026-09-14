"""Regression cases from real preserved publisher responses, not collection data."""
import gzip
import hashlib
import json
from pathlib import Path
import re

import pytest

from web_app.political_editorial_extraction import EXTRACTION_VERSION, extract_for_publisher

FIXTURES = Path(__file__).parent / "fixtures" / "political_editorial_real"
CASES = json.loads((FIXTURES / "manifest.json").read_text())["cases"]


def read_case(case):
    raw = gzip.decompress((FIXTURES / case["fixture"]).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == case["fixture_html_sha256"]
    return raw.decode()


def normalized(text):
    return " ".join(text.split())


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_real_editorial_bodies_dates_and_provenance(case):
    result = extract_for_publisher(read_case(case), case["url"])
    if not case["expected_extracted"]:
        assert result is None  # Electoral directory's broad wrapper is not news-body.
        return
    assert result["extraction_state"] == "full_text"
    assert result["title"] and result["canonical_url"] == case["url"]
    assert result["published_at"] == case["expected_publication"]
    assert result["text_extent"] == case["expected_extent"]
    assert result["extraction_version"] == EXTRACTION_VERSION
    assert result["extraction_method"] == "publisher_selector:" + case["selector"]
    body = normalized(result["full_text"])
    for paragraph in case["expected_editorial_blocks"]:
        assert paragraph in body, f"Lost real editorial block: {paragraph[:120]}"


@pytest.mark.parametrize("ident, unwanted", [
    ("7904", ["Gerando resumo", "Vale ler também", "Tensão no STF: Mendonça recorre", "PUBLICIDADE", "Canella desiste de disputa ao Senado"]),
    ("101135", ["Gerando resumo", "Fiscal pagava propina mensal", "Alexandre de Moraes perder o inquérito", "Vale ler também", "Prefeito do Rio compara bets a cigarro e anuncia"]),
    ("171117", ["Moraes pede explicações a Daniel Silveira após vídeo com senador"]),
    ("124305", ["Compartilhe:", "facebook", "whatsapp"]),
])
def test_real_related_story_and_interface_blocks_are_excluded(ident, unwanted):
    case = next(case for case in CASES if case["id"] == ident)
    text = extract_for_publisher(read_case(case), case["url"])["full_text"]
    for phrase in unwanted:
        assert phrase not in text


def test_real_interview_retains_questions_and_final_answer_after_related_card():
    case = next(case for case in CASES if case["id"] == "101135")
    result = extract_for_publisher(read_case(case), case["url"])
    assert "O senhor comparou as bets com o cigarro." in result["full_text"]
    assert "Cabe a uma cidade como o Rio cumprir esse papel para o Brasil." in result["full_text"]
    assert "article_jsonld:isAccessibleForFree=false" in result["restriction_evidence"]
    assert result["text_extent"] == "unknown"  # Public DOM is not proof of paid completeness.


def test_public_free_estadao_body_does_not_infer_paywall_from_wrapper_name():
    case = next(case for case in CASES if case["id"] == "7904")
    result = extract_for_publisher(read_case(case), case["url"])
    assert result["text_extent"] == "available"
    assert result["restriction_evidence"] == []


def test_missing_date_in_real_page_does_not_become_today():
    case = next(case for case in CASES if case["id"] == "118257")
    raw = re.sub(r'<div class="grid-6 grid-s-12 post-detalhe-data">.*?</div>', '', read_case(case), flags=re.S)
    result = extract_for_publisher(raw, case["url"])
    assert result["published_at"] == ""
    assert "Uma certidão do Supremo Tribunal Federal" in result["full_text"]


def test_same_html_requires_exact_publisher_host():
    case = next(case for case in CASES if case["id"] == "125485")
    raw = read_case(case)
    assert extract_for_publisher(raw, "https://exame.com.unrelated.example/news/") is None
    assert extract_for_publisher(raw, "https://another.example/news/") is None
