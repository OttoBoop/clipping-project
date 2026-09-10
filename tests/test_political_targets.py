from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

import pytest

from pipeline import settings
from pipeline.database import ClippingDB
from pipeline.matcher import CitationMatcher, Target, target_metadata
from web_app import db_admin


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "political_targets_v1.json"


def roster_rows():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["targets"]


def roster_matcher():
    return CitationMatcher([
        Target(key=r["key"], display_name=r["display_name"], keywords=r["keywords"],
               exact_aliases=r["exact_aliases"], **target_metadata(r))
        for r in roster_rows()
    ], exact_names_only=True)


def test_roster_preserves_original_groups_and_adds_approved_psd_profile():
    rows = roster_rows()
    by_key = {r["key"]: r for r in rows}
    assert len(rows) == len(by_key) == 44
    assert {r["key"] for r in rows if r["preferred_for_political_run"]} == {
        "flavio_valle", "pedro_duarte", "eduardo_paes", "pedro_paulo", "renan_ferreirinha",
    }
    assert sum(r["group"] == "rio_governor_opponents" for r in rows) == 8
    assert sum(r["group"] == "rio_psd" for r in rows) == 19
    assert by_key["pedro_duarte"]["party"] == "PSD"
    assert by_key["jane_reis"]["party"] == "MDB"
    assert by_key["jane_reis"]["group"] == "coalition_partners"
    assert all(r["verified_at"] in {"2026-09-09", "2026-09-10"} and r["sources"] for r in rows)
    inherited = {r["key"]: r for r in json.loads((ROOT / "data" / "targets.json").read_text())}
    assert inherited["flavio_valle"]["primary"] is True
    assert inherited["pedro_angelito"]["primary"] is True
    assert inherited["pedro_duarte"]["primary"] is False
    assert {"bernardo_rubiao", "shakira", "noozra_api"} <= inherited.keys()
    approved = json.loads((ROOT / "data" / "psd_rj_2026_profile.json").read_text())
    expected = {
        "eduardo_paes", "flavio_valle", "pedro_duarte", "renan_ferreirinha", "pedro_paulo",
        "eduardo_cavaliere", "daniel_soranz", "laura_carneiro", "hugo_leal", "carlo_caiado",
        "rosa_fernandes", "guilherme_schleder", "sergio_fernandes", "junior_da_lucinha",
        "joyce_trindade", "rafael_aloisio_freitas", "marcelo_diniz", "luiz_paulo", "atila_nunes",
        "otoni_de_paula", "joao_pires", "felipe_boro", "marcio_ribeiro", "salvino_oliveira",
    }
    original = expected.copy()
    expected |= {"douglas_ruas", "anthony_garotinho", "andre_marinho", "william_siri", "benedita_da_silva", "marcelo_crivella", "carlos_portinho", "carlos_jordy", "waguinho", "monica_benicio", "marcos_dias"}
    assert set(approved["original_target_keys"]) == original
    assert len(approved["target_keys"]) == approved["target_count"] == 35
    assert set(approved["target_keys"]) == expected
    assert {r["key"] for r in rows if "psd_rj_2026" in r.get("collection_profiles", [])} == expected
    assert {r["key"] for r in inherited.values() if "psd_rj_2026" in r.get("collection_profiles", [])} == original
    assert all(by_key[key]["party"] == "PSD" for key in original)
    assert "1948" in by_key["atila_nunes"]["role"]
    assert "renúncia" in by_key["felipe_boro"]["role"]
    assert any("Patriota" in s["note"] for s in by_key["felipe_boro"]["sources"])


@pytest.mark.parametrize("text,expected", [
    ("FLÁVIO-VALLE participa da sessão.", {"flavio_valle"}),
    ("Flavio Valley e Eduardo Paeson não são os nomes procurados.", set()),
    ("Pedro Duarte, vereador do Rio de Janeiro, apresenta proposta.", {"pedro_duarte"}),
    ("Pedro Duarte, do PSD, é o presidente da Câmara do Porto em Portugal.", set()),
    ("Pedro Duarte participa de evento.", set()),
    ("Pedro Duarte dos Santos Soares Junior participou de evento.", {"pedro_duarte"}),
    ("Pedro Paulo propõe mudanças no Senado pelo PSD.", {"pedro_paulo"}),
    ("O atacante Pedro Paulo joga no Rio de Janeiro.", set()),
    ("Pedro Paulo e Alex se apresentam no Rio.", set()),
    ("Renan Ferreirinha apresentou uma proposta.", {"renan_ferreirinha"}),
    ("Ferreirinha debate educação nas escolas cariocas.", {"renan_ferreirinha"}),
    ("O atacante Ferreirinha marcou gol no Rio.", set()),
    ("Ferreirinha deu entrevista.", set()),
    ("Carlo Caiado preside a Câmara do Rio.", {"carlo_caiado"}),
    ("Ronaldo Caiado disputa a Presidência.", {"ronaldo_caiado"}),
    ("Caiado deu entrevista.", set()),
    ("Otto Alencar Filho participou da reunião.", set()),
    ("Sérgio Fernandes debate educação em Petrópolis.", {"sergio_fernandes"}),
    ("Sergio Fernandes apresentou um concerto em Lisboa.", set()),
    ("Junior da Lucinha visitou a escola.", {"junior_da_lucinha"}),
    ("Joyce Trindade e Rafael Aloísio Freitas debatem orçamento.", {"joyce_trindade", "rafael_aloisio_freitas"}),
    ("Marcelo Diniz Anastacio da Silva compareceu.", {"marcelo_diniz"}),
    ("Luiz Paulo Corrêa da Rocha compareceu.", {"luiz_paulo"}),
    ("Luiz Paulo Conde foi prefeito do Rio de Janeiro.", set()),
    ("Átila Nunes, deputado estadual, discursou na ALERJ.", {"atila_nunes"}),
    ("O vereador Átila Nunes visitou a ALERJ.", set()),
    ("Átila Alexandre Nunes Pereira compareceu.", set()),
    ("Átila Nunes Pereira Filho compareceu.", {"atila_nunes"}),
    ("Otoni de Paula, deputado federal pelo PSD, discursou.", {"otoni_de_paula"}),
    ("Otoni de Paula Pai deu entrevista no Rio de Janeiro.", set()),
    ("João Pires fiscalizou postos pelo Procon.", {"joao_pires"}),
    ("João Pires, jogador, chegou ao Rio de Janeiro.", set()),
    ("João Vitor Pires Nascimento compareceu.", {"joao_pires"}),
    ("O humorista Márcio Ribeiro fez uma apresentação no Rio de Janeiro.", set()),
    ("Márcio Ribeiro, vereador do Rio de Janeiro, apresentou projeto.", {"marcio_ribeiro"}),
    ("Felipe Boró e Salvino Oliveira concederam entrevistas.", {"felipe_boro", "salvino_oliveira"}),
])
def test_roster_matches_names_with_boundaries_and_context(text, expected):
    assert {h.target_key for h in roster_matcher().find_hits(text)} == expected


def test_matcher_checks_later_valid_occurrence_and_keeps_shared_alias_targets():
    matcher = roster_matcher()
    text = "Pedro Duarte falou em Portugal. " + "Separação. " * 60 + "Pedro Duarte debate o Rio de Janeiro."
    assert {h.target_key for h in matcher.find_hits(text)} == {"pedro_duarte"}
    shared = CitationMatcher([Target(key="a", keywords=["Projeto Rio"]), Target(key="b", keywords=["Projeto Rio"])])
    assert {h.target_key for h in shared.find_hits("Projeto Rio funciona")} == {"a", "b"}


def test_roster_metadata_survives_normalize_load_update_and_creation(monkeypatch, tmp_path):
    path = tmp_path / "targets.json"
    row = next(r for r in roster_rows() if r["key"] == "pedro_duarte")
    path.write_text(json.dumps([row]))
    monkeypatch.setattr(settings, "TARGETS_JSON_PATH", path)
    monkeypatch.setattr(db_admin, "TARGETS_PATH", path)
    assert target_metadata(asdict(settings.get_active_targets()[0])) == target_metadata(row)
    changed = db_admin.update_secondary_target("pedro_duarte", {"keywords": ["Pedro Duarte", "vereador Pedro Duarte"]})
    assert target_metadata(changed) == target_metadata(row)
    assert target_metadata(db_admin.public_targets()["targets"][0]) == target_metadata(row)
    created = db_admin.create_secondary_target({"display_name": "Nome de Exemplo", **target_metadata(row)})
    assert target_metadata(created) == target_metadata(row)


def test_bootstrap_merge_preserves_archives_user_edits_permissions_and_is_idempotent(monkeypatch, tmp_path):
    path = tmp_path / "targets.json"
    archived = {"key": "pedro_duarte", "label": "Nome personalizado", "display_name": "Nome personalizado",
                "keywords": [], "exact_aliases": ["Alias privado"], "archived": True,
                "primary": False, "party": "anotação da equipe", "match_context": {}}
    protected = {"key": "flavio_valle", "display_name": "Flávio Valle", "primary": True, "keywords": ["Meu alias"]}
    unrelated = {"key": "meu_assunto", "display_name": "Meu assunto", "permissions": ["perfil_x"], "primary": False}
    path.write_text(json.dumps([archived, protected, unrelated]))
    monkeypatch.setattr(db_admin, "TARGETS_PATH", path)
    monkeypatch.setattr(db_admin, "POLITICAL_ROSTER_PATH", MANIFEST)
    result = db_admin.merge_political_roster()
    actual = {r["key"]: r for r in json.loads(path.read_text())}
    assert len(result["added"]) == 42
    assert all(actual["pedro_duarte"][k] == v for k, v in archived.items())
    assert all(actual["flavio_valle"][k] == v for k, v in protected.items())
    assert actual["meu_assunto"] == unrelated
    assert actual["eduardo_paes"]["primary"] is False
    before = path.read_bytes()
    assert db_admin.merge_political_roster()["changed"] is False
    assert path.read_bytes() == before


def test_collection_profile_metadata_is_a_bounded_unique_identifier_list():
    assert target_metadata({"collection_profiles": ["psd_rj_2026", " psd_rj_2026 ", "other_2", None, {}, "<script>"]}) == {
        "collection_profiles": ["psd_rj_2026", "other_2"]
    }
    assert target_metadata({"collection_profiles": "psd_rj_2026"}) == {"collection_profiles": []}
    assert len(target_metadata({"collection_profiles": [f"profile_{i}" for i in range(80)]})["collection_profiles"]) == 50


def review_db(monkeypatch, tmp_path, count=1):
    path = tmp_path / "review.db"
    ClippingDB(path)
    monkeypatch.setattr(db_admin, "configured_db_path", lambda: path)
    monkeypatch.setattr(db_admin, "selected_active_targets", lambda keys: [
        Target(key=k, display_name="Eduardo Paes", keywords=["Eduardo Paes"]) for k in keys
    ])
    with sqlite3.connect(path) as conn:
        conn.executemany(
            """INSERT INTO articles (url,title,source_name,source_type,published_at,discovered_at,full_text)
               VALUES (?, 'Eduardo Paes propõe medidas', 'Teste', 'test', '2026-06-10', '2026-06-10', ?)""",
            [(f"https://example.com/{i}", "Texto salvo. " * 1000) for i in range(count)],
        )
    return path


def test_existing_news_review_is_bounded_resumable_and_exact(monkeypatch, tmp_path):
    path = review_db(monkeypatch, tmp_path, 205)
    first = db_admin.backfill_missing_target_mentions(path, ["paes"], sample_limit=3, batch_size=500)
    assert first["scannedCount"] == first["mentionsInserted"] == first["updatedCount"] == 100
    assert len(first["updated"]) == 3 and first["sampleTruncated"] and first["hasMore"]
    second = db_admin.backfill_missing_target_mentions(path, ["paes"])
    assert second["cursor"] == 200 and second["scannedCount"] == 100 and second["hasMore"]
    third = db_admin.backfill_missing_target_mentions(path, ["paes"])
    assert third["cursor"] == 205 and third["scannedCount"] == 5 and not third["hasMore"]
    assert db_admin.backfill_missing_target_mentions(path, ["paes"])["mentionsInserted"] == 0
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0] == 205
        assert conn.execute("SELECT scanned_count FROM target_review_progress").fetchone()[0] == 205
    new_rule = db_admin.backfill_missing_target_mentions(path, ["paes"], rule_version="changed_rule")
    assert new_rule["checkpointKey"] != first["checkpointKey"]
    assert new_rule["scannedCount"] == 100 and new_rule["mentionsInserted"] == 0


def test_review_preserves_classifications_and_existing_story_content(monkeypatch, tmp_path):
    path = review_db(monkeypatch, tmp_path)
    with ClippingDB(path) as db:
        db.insert_mention(1, "old_target", "Eduardo Paes", "Eduardo Paes")
        mention_id = db.find_mention_id(1, "old_target")
        db.upsert_classification(mention_id, article_sentiment="positive", target_sentiment="negative",
                                 centimetragem=12, classified_by="editor", ai_generated=False)
        story_id = db.create_story("Título editado", "Resumo editado", 99, ["old_target"])
        db.attach_article_to_story(story_id, 1)
    with sqlite3.connect(path) as conn:
        original = conn.execute("SELECT * FROM classifications").fetchall()
    result = db_admin.backfill_missing_target_mentions(path, ["old_target", "new_target"])
    assert result["mentionsInserted"] == result["storiesTouched"] == 1
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT * FROM classifications").fetchall() == original
        assert conn.execute("SELECT title,summary,temperature FROM stories").fetchone() == ("Título editado", "Resumo editado", 99)
        assert conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0] == 1


def test_review_batch_rolls_back_mutations_and_cursor_on_interruption(monkeypatch, tmp_path):
    path = review_db(monkeypatch, tmp_path, 8)
    db_admin.ensure_app_tables(path)
    with sqlite3.connect(path) as conn:
        conn.execute("""CREATE TRIGGER fail_review BEFORE INSERT ON mentions WHEN NEW.article_id = 4
                        BEGIN SELECT RAISE(ABORT, 'injected interruption'); END""")
    with pytest.raises(sqlite3.IntegrityError, match="injected interruption"):
        db_admin.backfill_missing_target_mentions(path, ["paes"])
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM target_review_progress").fetchone()[0] == 0
        conn.execute("DROP TRIGGER fail_review")
    assert db_admin.backfill_missing_target_mentions(path, ["paes"])["mentionsInserted"] == 8


def test_review_date_scope_does_not_substitute_discovery_date(monkeypatch, tmp_path):
    path = review_db(monkeypatch, tmp_path, 4)
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE articles SET published_at='2026-05-31' WHERE id=1")
        conn.execute("UPDATE articles SET published_at=NULL WHERE id=2")
        conn.execute("UPDATE articles SET published_at='2026-10-01' WHERE id=4")
    result = db_admin.backfill_missing_target_mentions(path, ["paes"], date_from="2026-06-01", date_to="2026-09-09")
    assert result["mentionsInserted"] == result["scannedCount"] == 1
    assert result["updated"][0]["article_id"] == 3


def test_legacy_cleanup_cannot_delete_an_existing_classification(monkeypatch, tmp_path):
    path = review_db(monkeypatch, tmp_path)
    with ClippingDB(path) as db:
        db.insert_mention(1, "paes", "Eduardo Paes", "manual")
        mention_id = db.find_mention_id(1, "paes")
        db.upsert_classification(mention_id, article_sentiment="neutral", target_sentiment="neutral",
                                 centimetragem=0, classified_by="editor", ai_generated=False)
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE articles SET title='Título editado sem o nome'")
    assert db_admin.cleanup_false_backfilled_target_mentions(path, ["paes"])["removedMentions"] == 0


@pytest.mark.parametrize('text,expected',[
 ('Rosinha Garotinho participou de evento no Rio.',set()),
 ('Anthony Garotinho e Rosinha Garotinho participaram do debate.',{'anthony_garotinho'}),
 ('Garotinho apresentou propostas ao governo do Rio.',{'anthony_garotinho'}),
 ('Daniela do Waguinho participou de evento em Belford Roxo.',set()),
 ('O cantor Waguinho anunciou show em Belford Roxo.',set()),
 ('Waguinho, ex-prefeito de Belford Roxo, concorre ao Senado.',{'waguinho'}),
 ('Marcos Dias apresentou seu novo disco em Lisboa.',set()),
 ('O vereador Marcos Dias, do Podemos, discutiu o futuro do Rio de Janeiro.',{'marcos_dias'}),
 ('Benedita da Silva, Carlos Jordy e Carlos Portinho disputam o Senado pelo Rio.',{'benedita_da_silva','carlos_jordy','carlos_portinho'}),
])
def test_expanded_roster_context_and_namesakes(text,expected):
    approved={'anthony_garotinho','waguinho','marcos_dias','benedita_da_silva','carlos_jordy','carlos_portinho'}
    assert {h.target_key for h in roster_matcher().find_hits(text)} & approved == expected
