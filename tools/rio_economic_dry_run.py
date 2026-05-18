from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.collectors import CandidateArticle, collect_google_news


REPORTS_DIR = PROJECT_ROOT / "data" / "reports"


@dataclass(frozen=True)
class RioEconomicQuery:
    dimension: str
    query: str
    why_candidate: str


RIO_ECONOMIC_QUERIES: tuple[RioEconomicQuery, ...] = (
    RioEconomicQuery("tourism_events", '"Rio de Janeiro" hotelaria', "hotel occupancy and visitor economy"),
    RioEconomicQuery("tourism_events", '"cidade do Rio" turismo', "city-specific tourism agenda"),
    RioEconomicQuery("commerce_services", '"cidade do Rio" comercio', "local commerce/services signal"),
    RioEconomicQuery("commerce_services", '"Prefeitura do Rio" comercio', "municipal policy affecting commerce"),
    RioEconomicQuery("jobs_income", '"Rio de Janeiro" emprego', "local jobs and labor market"),
    RioEconomicQuery("construction_real_estate", '"Rio de Janeiro" construcao civil', "construction activity"),
    RioEconomicQuery("budget_finance", '"Prefeitura do Rio" orcamento', "municipal budget and public finance"),
    RioEconomicQuery("budget_finance", '"municipio do Rio" arrecadacao', "city tax/revenue signal"),
    RioEconomicQuery("logistics_port", '"Porto do Rio" logistica', "port and logistics activity"),
    RioEconomicQuery("business_open_close", '"Rio de Janeiro" inaugura loja', "business opening signal"),
    RioEconomicQuery("business_open_close", '"cidade do Rio" fechamento comercio', "business closure signal"),
    RioEconomicQuery("cost_of_living", '"Rio de Janeiro" cesta basica', "local cost-of-living signal"),
)


def _query_spec_from_mapping(row: dict[str, Any]) -> RioEconomicQuery:
    dimension = str(row.get("dimension") or "").strip()
    query = str(row.get("query") or "").strip()
    why_candidate = str(row.get("why_candidate") or row.get("why") or "").strip()
    if not dimension or not query:
        raise ValueError("each Rio query spec must include non-empty dimension and query")
    return RioEconomicQuery(dimension, query, why_candidate or "manual revised query")


def load_query_specs(path: Path | None) -> list[RioEconomicQuery]:
    if not path:
        return list(RIO_ECONOMIC_QUERIES)
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("queries") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("queries file must be a JSON list or an object with a queries list")
    return [_query_spec_from_mapping(row) for row in rows if isinstance(row, dict)]


def offline_fixture_collector(**kwargs: Any) -> list[CandidateArticle]:
    query = str((kwargs.get("queries") or ["rio"])[0])
    slug = (
        query.lower()
        .replace('"', "")
        .replace(" ", "-")
        .replace("ç", "c")
        .replace("ã", "a")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
    return [
        CandidateArticle(
            title=f"Amostra offline para {query}",
            url=f"https://example.com/rio-economic-dry-run/{slug}",
            source_name="Offline Fixture",
            source_type="offline_fixture",
            published_at="2026-05-19T12:00:00+00:00",
            snippet="Amostra offline para validar o formato de revisão sem rede.",
            metadata={"query": query, "offline_fixture": True},
        )
    ]


def selected_queries(max_queries: int = 0, query_specs: list[RioEconomicQuery] | None = None) -> list[RioEconomicQuery]:
    queries = list(query_specs or RIO_ECONOMIC_QUERIES)
    if max_queries > 0:
        return queries[:max_queries]
    return queries


def article_to_row(spec: RioEconomicQuery, article: CandidateArticle) -> dict[str, Any]:
    return {
        "query": spec.query,
        "dimension": spec.dimension,
        "source": article.source_name,
        "source_type": article.source_type,
        "title": article.title,
        "url": article.url,
        "published_at": article.published_at,
        "why_candidate": spec.why_candidate,
        "review_label": "",
        "false_positive_reason": "",
        "notes": "",
    }


def collect_rows(
    *,
    date_from: str = "",
    date_to: str = "",
    limit_per_query: int = 5,
    max_queries: int = 0,
    request_timeout: int = 10,
    resolve_timeout: int = 0,
    collection_timeout: int = 6000,
    query_specs: list[RioEconomicQuery] | None = None,
    collector: Callable[..., list[CandidateArticle]] = collect_google_news,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for spec in selected_queries(max_queries, query_specs):
        articles = collector(
            queries=[spec.query],
            date_from=date_from,
            date_to=date_to,
            limit_per_query=limit_per_query,
            request_timeout=request_timeout,
            resolve_timeout=resolve_timeout,
            collection_timeout=collection_timeout,
        )
        for article in articles:
            url_key = str(article.url or "").strip()
            if url_key and url_key in seen_urls:
                continue
            if url_key:
                seen_urls.add(url_key)
            rows.append(article_to_row(spec, article))
    return rows


def output_prefix(now: datetime | None = None) -> str:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    return f"rio_economic_dry_run_{stamp}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "query",
        "dimension",
        "source",
        "source_type",
        "title",
        "url",
        "published_at",
        "why_candidate",
        "review_label",
        "false_positive_reason",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def md_escape(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    lines = [
        "# Rio Economic Dry Run Review",
        "",
        f"Generated at: `{payload['meta']['generated_at']}`",
        f"Date from: `{payload['meta']['date_from'] or 'none'}`",
        f"Date to: `{payload['meta']['date_to'] or 'none'}`",
        f"Queries: `{payload['meta']['query_count']}`",
        f"Candidate rows: `{payload['meta']['row_count']}`",
        "",
        "| Dimension | Query | Source | Published | Title | Review | False Positive Reason | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(row.get("dimension")),
                    md_escape(row.get("query")),
                    md_escape(row.get("source")),
                    md_escape(row.get("published_at")),
                    md_escape(row.get("title")),
                    "",
                    "",
                    "",
                ]
            )
            + " |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_payload(
    rows: list[dict[str, Any]],
    *,
    date_from: str = "",
    date_to: str = "",
    limit_per_query: int = 5,
    max_queries: int = 0,
    request_timeout: int = 10,
    resolve_timeout: int = 0,
    collection_timeout: int = 6000,
    query_specs: list[RioEconomicQuery] | None = None,
    queries_file: str = "",
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    query_count = len(selected_queries(max_queries, query_specs))
    generated = (generated_at or datetime.now(timezone.utc)).isoformat()
    return {
        "meta": {
            "generated_at": generated,
            "date_from": date_from,
            "date_to": date_to,
            "limit_per_query": limit_per_query,
            "request_timeout": request_timeout,
            "resolve_timeout": resolve_timeout,
            "collection_timeout": collection_timeout,
            "redirect_resolution_skipped": resolve_timeout <= 0,
            "queries_file": queries_file,
            "query_count": query_count,
            "row_count": len(rows),
            "timeout_policy": "dry_run_smoke_timeouts_are_allowed",
            "writes_production_db": False,
            "writes_assets_payload": False,
            "writes_targets_json": False,
        },
        "queries": [spec.__dict__ for spec in selected_queries(max_queries, query_specs)],
        "rows": rows,
    }


def write_reports(payload: dict[str, Any], output_dir: Path, *, now: datetime | None = None) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_prefix(now)
    json_path = output_dir / f"{prefix}.json"
    csv_path = output_dir / f"{prefix}.csv"
    md_path = output_dir / f"{prefix}.md"
    write_json(json_path, payload)
    write_csv(csv_path, payload["rows"])
    write_markdown(md_path, payload)
    return {"json": str(json_path), "csv": str(csv_path), "markdown": str(md_path)}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run Rio economic queries without touching production payloads.")
    parser.add_argument("--date-from", default="", help="YYYY-MM-DD lower bound for Google News queries.")
    parser.add_argument("--date-to", default="", help="YYYY-MM-DD upper bound for Google News queries.")
    parser.add_argument("--limit-per-query", type=int, default=5)
    parser.add_argument("--max-queries", type=int, default=0, help="Limit query count for a cheap smoke run.")
    parser.add_argument("--request-timeout", type=int, default=10)
    parser.add_argument("--resolve-timeout", type=int, default=0, help="Seconds for Google redirect resolution; 0 skips it for safe smoke runs.")
    parser.add_argument("--collection-timeout", type=int, default=6000)
    parser.add_argument("--output-dir", type=Path, default=REPORTS_DIR)
    parser.add_argument("--queries-file", type=Path, default=None, help="JSON list/object of revised Rio query specs.")
    parser.add_argument("--offline-fixture", action="store_true", help="Generate review artifacts without network calls.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    query_specs = load_query_specs(args.queries_file)
    rows = collect_rows(
        date_from=args.date_from,
        date_to=args.date_to,
        limit_per_query=max(1, args.limit_per_query),
        max_queries=max(0, args.max_queries),
        request_timeout=max(1, args.request_timeout),
        resolve_timeout=max(0, args.resolve_timeout),
        collection_timeout=max(1, args.collection_timeout),
        query_specs=query_specs,
        collector=offline_fixture_collector if args.offline_fixture else collect_google_news,
    )
    payload = build_payload(
        rows,
        date_from=args.date_from,
        date_to=args.date_to,
        limit_per_query=max(1, args.limit_per_query),
        max_queries=max(0, args.max_queries),
        request_timeout=max(1, args.request_timeout),
        resolve_timeout=max(0, args.resolve_timeout),
        collection_timeout=max(1, args.collection_timeout),
        query_specs=query_specs,
        queries_file=str(args.queries_file or ""),
    )
    if args.offline_fixture:
        payload["meta"]["offline_fixture"] = True
    paths = write_reports(payload, args.output_dir)
    print(json.dumps({"ok": True, "row_count": len(rows), "paths": paths}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
