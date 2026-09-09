"""Focused regression for the genuine editorial mention in live article 43."""
from dataclasses import fields
import json
from pathlib import Path

import pytest

from pipeline.matcher import CitationMatcher, Target


ROOT = Path(__file__).resolve().parents[1]


def target_row(path="data/political_targets_v1.json"):
    data = json.loads((ROOT / path).read_text())
    rows = data["targets"] if isinstance(data, dict) else data
    return next(row for row in rows if row["key"] == "pedro_paulo")


def matches(value):
    accepted = {field.name for field in fields(Target)}
    target = Target(**{key: value for key, value in target_row().items() if key in accepted})
    return bool(CitationMatcher([target]).find_hits(value))


def test_editorial_riotur_mention_matches_without_distant_rio_anchor():
    # Verified body excerpt, Aug 9, 2026 (live saved article 43):
    # https://agendadopoder.com.br/paes-vira-alvo-de-ruas-marinho-e-siri-em-primeiro-bloco-do-debate-da-band
    excerpt = "nomes ligados politicamente a Paes, entre eles Pedro Paulo e um ex-presidente da Riotur."
    assert matches(excerpt)


@pytest.mark.parametrize("name", [
    "atacante Pedro Paulo", "goleiro Pedro Paulo", "cantor Pedro Paulo",
    "Pedro Paulo e Alex", "Pedro Paulo Bazana", "Pedro Paulo Venzon",
])
def test_riotur_context_does_not_override_homonym_exclusions(name):
    assert not matches(f"A Riotur informou uma programação com {name}.")


def test_riotur_cue_keeps_token_boundaries_and_local_window():
    assert not matches("Pedro Paulo participou de um evento da Rioturismo.")
    assert not matches("Riotur. " + "Separação. " * 60 + "Pedro Paulo participou do evento.")
    assert not matches("Pedro Paulo participou do evento.")


def test_both_seed_contexts_match_and_preserve_existing_rules():
    context = target_row()["match_context"]
    assert context == target_row("data/targets.json")["match_context"]
    assert context["any_of"].count("Riotur") == 1
    assert context["window_chars"] == 220
    assert context["required_for"] == ["Pedro Paulo"]
    assert context["exempt_aliases"] == ["Pedro Paulo Carvalho Teixeira"]
    assert {"Rio", "PSD", "Eduardo Paes", "deputado federal", "Senado"} <= set(context["any_of"])
    assert len(context["none_of"]) == 6
