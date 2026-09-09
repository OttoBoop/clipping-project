from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from tools import political_quality_check as quality


@pytest.fixture
def fixture():
    return quality.load_dataset()


def observed(dataset):
    return {row["id"]: [{"id": index, "target_keys": row["expected_target_keys"],
                          "published_at": row["date"] + "T12:00:00-03:00",
                          "body_status": "body_extracted", "text_object_key": "immutable/body.gz"}]
            for index, row in enumerate(dataset["cases"], 1)}


def test_starter_fixture_has_real_source_evidence_across_months_and_required_people(fixture):
    dataset, targets = fixture
    cases = dataset["cases"]
    assert 12 <= len(cases) <= 20
    assert {row["date"][:7] for row in cases} == {"2026-06", "2026-07", "2026-08", "2026-09"}
    assert len({row["publisher"] for row in cases if row["publisher_type"] == "news_outlet"}) >= 5
    expected = {key for row in cases for key in row["expected_target_keys"]}
    required = {row["key"] for row in targets if row["group"] in {"requested", "governor_opponents"}}
    assert required <= expected
    assert all(row["evidence"][0]["url"] == row["canonical_url"] for row in cases)
    assert all(row["kind"] == "synthetic_disambiguation" for row in dataset["synthetic_cases"])


def test_annotations_require_complete_assessment_and_source_evidence(tmp_path, fixture):
    dataset, _ = fixture
    broken = deepcopy(dataset)
    broken["cases"][0]["assessed_target_keys"] = []
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(broken))
    with pytest.raises(ValueError, match="expected and assessed"):
        quality.load_dataset(path)
    broken["cases"][0] = deepcopy(dataset["cases"][0])
    broken["cases"][0]["evidence"] = []
    path.write_text(json.dumps(broken))
    with pytest.raises(ValueError, match="evidence and scope"):
        quality.load_dataset(path)


def test_complete_annotated_observations_pass_without_claiming_production_ready(fixture):
    dataset, targets = fixture
    report = quality.build_report(dataset, targets, observations=observed(dataset))
    assert report["corpus"]["annotated_case_gates_passed"] is True
    assert report["corpus"]["article_recall"] == 1
    assert report["corpus"]["person_precision"] == 1
    assert report["corpus"]["full_text_available_articles"] == len(dataset["cases"])
    assert report["production_rollout_verified"] is False


def test_missing_multi_person_article_fails_person_recall_even_if_url_recall_passes(fixture):
    dataset, _ = fixture
    articles = observed(dataset)
    del articles["uol_candidatos_0907"]
    result = quality.score_cases(dataset, articles)
    assert result["gates"]["article_recall_at_least_90_percent"] is True
    assert result["gates"]["person_recall_at_least_90_percent"] is False
    assert result["missing_person_associations"] == 10
    assert result["annotated_case_gates_passed"] is False


def test_wrong_associations_fail_precision_and_unassessed_names_do_not_count(fixture):
    dataset, _ = fixture
    articles = observed(dataset)
    first = dataset["cases"][0]
    articles[first["id"]][0]["target_keys"] = [*first["expected_target_keys"],
        "carlo_caiado", "ronaldo_caiado", "otto_alencar", "outside_this_roster"]
    result = quality.score_cases(dataset, articles)
    assert result["false_positive_person_associations"] == 3
    assert result["gates"]["incorrect_person_matches_at_most_5_percent"] is False
    assert "outside_this_roster" not in result["cases"][0]["incorrect_target_keys"]


def test_zero_collected_records_cannot_pass_precision_vacuously(fixture):
    dataset, _ = fixture
    result = quality.score_cases(dataset, {})
    assert result["measured"] is True
    assert result["article_recall"] == 0
    assert result["person_recall"] == 0
    assert result["person_precision"] is None
    assert result["annotated_case_gates_passed"] is False


def test_unknown_date_metadata_only_and_duplicate_observations_remain_visible(fixture):
    dataset, _ = fixture
    articles = observed(dataset)
    row = articles[dataset["cases"][0]["id"]][0]
    row.update(published_at=None, body_status="metadata_only", text_object_key="")
    articles[dataset["cases"][0]["id"]].append({**row, "id": 99})
    result = quality.score_cases(dataset, articles)
    assert result["cases"][0]["publication_date_needs_review"] is True
    assert result["cases"][0]["duplicate_record_count"] == 1
    assert result["full_text_available_articles"] == len(dataset["cases"]) - 1
    assert result["true_positive_person_associations"] == sum(len(row["expected_target_keys"]) for row in dataset["cases"])


def test_date_comparison_uses_sao_paulo_day():
    assert quality._local_day(datetime(2026, 6, 2, 2, 59, tzinfo=timezone.utc)) == "2026-06-01"
    assert quality._local_day(None) is None
    assert quality._local_day("unknown") is None


def test_database_lookup_uses_read_only_snapshot_and_verified_aliases(fixture):
    dataset, _ = fixture
    case = deepcopy(dataset["cases"][0])
    case["aliases"] = [case["canonical_url"] + "?utm_source=test"]
    statements = []

    class Connection:
        def execute(self, sql, params=None):
            statements.append((sql, params))
            return self

        def fetchall(self):
            return [{"id": 42, "target_keys": []}]

    class Service:
        @contextmanager
        def _connect(self):
            yield Connection()

        def ensure_schema(self):
            pytest.fail("quality checker must never perform schema writes")

    result = quality.lookup_articles(Service(), [case])
    assert "READ ONLY" in statements[0][0]
    assert "REPEATABLE READ" in statements[0][0]
    assert "political_url_aliases" in statements[-1][0]
    assert "political_mentions" in statements[-1][0]
    assert statements[-1][1][0] == statements[-1][1][1]
    assert quality.canonicalize_url(case["canonical_url"]) in statements[-1][1][0]
    assert result[case["id"]][0]["target_keys"] == []  # finds unassociated articles too
    assert not any(sql.lstrip().startswith(("INSERT", "UPDATE", "CREATE", "DELETE")) for sql, _ in statements)


def test_synthetic_controls_pass_and_do_not_create_corpus_measurements(fixture):
    dataset, targets = fixture
    result = quality.build_report(dataset, targets)
    assert result["synthetic_controls"]["passed"] is True
    assert result["corpus"]["measured"] is False
    assert result["corpus"]["article_recall"] is None
    assert result["corpus"]["annotated_case_gates_passed"] is None


def test_validation_only_never_opens_database(monkeypatch, tmp_path, capsys):
    def unexpected_service(**_):
        pytest.fail("validation-only may not access database")
    monkeypatch.setattr(quality, "PoliticalCorpusService", unexpected_service)
    output = tmp_path / "pending.json"
    assert quality.main(["--validate-only", "--output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert result["corpus"]["reason"] == "validation_only"
    assert result["corpus"]["annotated_case_gates_passed"] is None
    capsys.readouterr()


def test_canary_without_annotated_cases_reports_pending_not_pass(capsys):
    assert quality.main(["--validate-only", "--date-from", "2026-06-01", "--date-to", "2026-06-01"]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["corpus"]["reason"] == "no_annotated_articles_in_selected_period"
    assert result["corpus"]["annotated_case_gates_passed"] is None
