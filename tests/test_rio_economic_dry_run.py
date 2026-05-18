from __future__ import annotations

import json
from datetime import datetime, timezone

from pipeline.collectors import CandidateArticle
from tools import rio_economic_dry_run


def sample_article(url: str, title: str = "Rio hotelaria cresce") -> CandidateArticle:
    return CandidateArticle(
        title=title,
        url=url,
        source_name="Google News",
        source_type="google_news",
        published_at="2026-05-19T12:00:00+00:00",
        snippet="Snippet",
        metadata={},
    )


def test_selected_queries_avoid_single_broad_rio_economia_query():
    queries = [row.query for row in rio_economic_dry_run.selected_queries()]

    assert "Rio economia" not in queries
    assert "mercado Rio" not in queries
    assert any("hotelaria" in query for query in queries)
    assert any("orcamento" in query for query in queries)


def test_load_query_specs_uses_json_file(tmp_path):
    queries_path = tmp_path / "queries.json"
    queries_path.write_text(
        json.dumps(
            {
                "queries": [
                    {
                        "dimension": "budget_finance",
                        "query": '"Prefeitura do Rio" ISS',
                        "why_candidate": "municipal revenue signal",
                        "exclude_title_terms": ["Pernambuco"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    specs = rio_economic_dry_run.load_query_specs(queries_path)

    assert specs == [
        rio_economic_dry_run.RioEconomicQuery(
            "budget_finance",
            '"Prefeitura do Rio" ISS',
            "municipal revenue signal",
            ("Pernambuco",),
        )
    ]


def test_collect_rows_dedupes_urls_and_preserves_review_fields():
    calls: list[dict] = []

    def fake_collector(**kwargs):
        calls.append(kwargs)
        return [
            sample_article("https://example.com/a", "Primeira"),
            sample_article("https://example.com/a", "Duplicada"),
            sample_article("https://example.com/b", "Segunda"),
        ]

    rows = rio_economic_dry_run.collect_rows(
        max_queries=2,
        limit_per_query=3,
        request_timeout=2,
        resolve_timeout=1,
        collection_timeout=5,
        collector=fake_collector,
    )

    assert len(calls) == 2
    assert calls[0]["request_timeout"] == 2
    assert calls[0]["resolve_timeout"] == 1
    assert calls[0]["collection_timeout"] == 5
    assert [row["url"] for row in rows] == ["https://example.com/a", "https://example.com/b"]
    assert rows[0]["review_label"] == ""
    assert rows[0]["false_positive_reason"] == ""


def test_collect_rows_accepts_custom_query_specs():
    calls: list[dict] = []

    def fake_collector(**kwargs):
        calls.append(kwargs)
        return [sample_article("https://example.com/iss", "ISS sobe")]

    rows = rio_economic_dry_run.collect_rows(
        query_specs=[
            rio_economic_dry_run.RioEconomicQuery(
                "budget_finance",
                '"Prefeitura do Rio" ISS',
                "municipal revenue signal",
            )
        ],
        collector=fake_collector,
    )

    assert calls[0]["queries"] == ['"Prefeitura do Rio" ISS']
    assert rows[0]["dimension"] == "budget_finance"
    assert rows[0]["why_candidate"] == "municipal revenue signal"


def test_collect_rows_applies_title_exclusions():
    def fake_collector(**_kwargs):
        return [
            sample_article("https://example.com/rio", "Prefeitura do Rio amplia vagas"),
            sample_article("https://example.com/porto-velho", "Porto Velho oferece vagas pelo Sine"),
        ]

    rows = rio_economic_dry_run.collect_rows(
        query_specs=[
            rio_economic_dry_run.RioEconomicQuery(
                "jobs_income",
                '"Rio de Janeiro" vagas emprego Prefeitura',
                "city jobs signal",
                ("Porto Velho",),
            )
        ],
        collector=fake_collector,
    )

    assert [row["url"] for row in rows] == ["https://example.com/rio"]


def test_write_reports_creates_json_csv_and_markdown(tmp_path):
    rows = [rio_economic_dry_run.article_to_row(rio_economic_dry_run.selected_queries(1)[0], sample_article("https://example.com/a"))]
    generated_at = datetime(2026, 5, 19, 12, 0, tzinfo=timezone.utc)
    payload = rio_economic_dry_run.build_payload(
        rows,
        date_from="2026-05-01",
        date_to="2026-05-19",
        limit_per_query=1,
        max_queries=1,
        query_specs=[rio_economic_dry_run.selected_queries(1)[0]],
        generated_at=generated_at,
    )

    paths = rio_economic_dry_run.write_reports(payload, tmp_path, now=generated_at)

    json_payload = json.loads((tmp_path / "rio_economic_dry_run_20260519T120000Z.json").read_text(encoding="utf-8"))
    assert json_payload["meta"]["timeout_policy"] == "dry_run_smoke_timeouts_are_allowed"
    assert json_payload["meta"]["resolve_timeout"] == 0
    assert json_payload["meta"]["redirect_resolution_skipped"] is True
    assert json_payload["meta"]["writes_production_db"] is False
    assert json_payload["meta"]["writes_assets_payload"] is False
    assert json_payload["meta"]["writes_targets_json"] is False
    assert "Rio Economic Dry Run Review" in (tmp_path / "rio_economic_dry_run_20260519T120000Z.md").read_text(encoding="utf-8")
    assert set(paths) == {"json", "csv", "markdown"}


def test_offline_fixture_collector_returns_review_candidate():
    rows = rio_economic_dry_run.collect_rows(max_queries=1, collector=rio_economic_dry_run.offline_fixture_collector)

    assert len(rows) == 1
    assert rows[0]["source"] == "Offline Fixture"
    assert rows[0]["source_type"] == "offline_fixture"
    assert rows[0]["review_label"] == ""
