from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
CURRENT_PERIOD_STATUSES = {"same_day"}
MANUAL_REVIEW_STATUSES = {"near_date"}
PASS_STATUSES_BY_STRENGTH = ("same_day", "near_date")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    return payload


def row_number_from_duplicate(value: Any) -> int | None:
    raw = str(value or "").strip()
    if not raw.startswith("row:"):
        return None
    try:
        return int(raw.split(":", 1)[1])
    except ValueError:
        return None


def canonical_by_row(canonical_payload: dict[str, Any] | None) -> dict[int, dict[str, Any]]:
    if not canonical_payload:
        return {}
    rows = canonical_payload.get("rows") or []
    output: dict[int, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            row_number = int(row.get("row") or 0)
        except (TypeError, ValueError):
            continue
        if row_number > 0:
            output[row_number] = row
    return output


def representative_row_number(index: int, row: dict[str, Any]) -> int:
    duplicate_of = row_number_from_duplicate(row.get("duplicate_of"))
    return duplicate_of or index


def date_quality_policy(status: str) -> str:
    if status in CURRENT_PERIOD_STATUSES:
        return "count_current_period"
    if status in MANUAL_REVIEW_STATUSES:
        return "manual_review_before_counting"
    if status == "not_checked":
        return "canonical_check_required"
    return "research_only"


def select_canonical_evidence(
    member_rows: list[int],
    canonical_rows: dict[int, dict[str, Any]],
) -> tuple[int | None, dict[str, Any] | None, list[tuple[int, dict[str, Any]]]]:
    evidence = [(row_number, canonical_rows[row_number]) for row_number in member_rows if row_number in canonical_rows]
    if not evidence:
        return None, None, []

    for status in PASS_STATUSES_BY_STRENGTH:
        for row_number, canonical in evidence:
            if str(canonical.get("status") or "not_checked") == status:
                return row_number, canonical, evidence

    return evidence[0][0], evidence[0][1], evidence


def build_stories(clustered_payload: dict[str, Any], canonical_payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    rows = clustered_payload.get("rows") or []
    if not isinstance(rows, list):
        raise ValueError("clustered report must contain a rows list")
    canonical_rows = canonical_by_row(canonical_payload)
    grouped: dict[int, dict[str, Any]] = {}

    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            continue
        representative = representative_row_number(index, row)
        story = grouped.setdefault(
            representative,
            {
                "representative_row": representative,
                "cluster_key": "",
                "cluster_label": "",
                "primary_dimension": "",
                "secondary_dimensions": "",
                "article_count": 0,
                "member_rows": [],
                "dimensions": [],
                "sources": [],
                "title": "",
                "url": "",
                "published_at": "",
                "date_quality_status": "not_checked",
                "date_quality_policy": "canonical_check_required",
            },
        )
        story["article_count"] += 1
        story["member_rows"].append(index)
        for field, fallback in (
            ("cluster_key", ""),
            ("cluster_label", ""),
            ("primary_dimension", row.get("dimension", "")),
            ("secondary_dimensions", ""),
        ):
            if row.get(field) and not story.get(field):
                story[field] = row.get(field)
            elif not story.get(field) and fallback:
                story[field] = fallback
        dimension = str(row.get("dimension") or "").strip()
        if dimension and dimension not in story["dimensions"]:
            story["dimensions"].append(dimension)
        source = str(row.get("source") or "").strip()
        if source and source not in story["sources"]:
            story["sources"].append(source)
        if index == representative or not story["title"]:
            story["title"] = str(row.get("title") or "")
            story["url"] = str(row.get("representative_url") or row.get("url") or "")
            story["published_at"] = str(row.get("published_at") or "")

    for story in grouped.values():
        canonical_row_number, canonical, evidence = select_canonical_evidence(story["member_rows"], canonical_rows)
        story["date_quality_evidence_rows"] = [row_number for row_number, _canonical in evidence]
        story["date_quality_evidence_statuses"] = {
            str(row_number): str(row.get("status") or "not_checked") for row_number, row in evidence
        }
        story["date_quality_source_row"] = canonical_row_number or ""
        if canonical:
            status = str(canonical.get("status") or "not_checked")
            story["date_quality_status"] = status
            story["canonical_url"] = str(canonical.get("final_url") or "")
            story["canonical_published_at"] = str(canonical.get("canonical_published_at") or "")
        else:
            status = "not_checked"
            story["canonical_url"] = ""
            story["canonical_published_at"] = ""
        story["date_quality_policy"] = date_quality_policy(status)

    return [grouped[key] for key in sorted(grouped)]


def summarize(stories: list[dict[str, Any]], source_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    status_counts = Counter(str(story.get("date_quality_status") or "unknown") for story in stories)
    policy_counts = Counter(str(story.get("date_quality_policy") or "unknown") for story in stories)
    dimension_counts = Counter()
    for story in stories:
        primary = str(story.get("primary_dimension") or "").strip()
        if primary:
            dimension_counts[primary] += 1
    article_count = sum(int(story.get("article_count") or 0) for story in stories)
    return {
        "story_count": len(stories),
        "article_count": article_count,
        "date_quality_status_counts": dict(sorted(status_counts.items())),
        "date_quality_policy_counts": dict(sorted(policy_counts.items())),
        "primary_dimension_story_counts": dict(sorted(dimension_counts.items())),
        "source_row_count": (source_meta or {}).get("row_count"),
        "source_cluster_count": (source_meta or {}).get("cluster_count"),
        "source_clustered_row_count": (source_meta or {}).get("clustered_row_count"),
    }


def build_payload(clustered_report: Path, canonical_report: Path | None = None) -> dict[str, Any]:
    clustered_payload = load_json(clustered_report)
    canonical_payload = load_json(canonical_report) if canonical_report else None
    stories = build_stories(clustered_payload, canonical_payload)
    source_meta = clustered_payload.get("meta") if isinstance(clustered_payload.get("meta"), dict) else {}
    canonical_meta = canonical_payload.get("meta") if canonical_payload and isinstance(canonical_payload.get("meta"), dict) else {}
    generated_at = datetime.now(timezone.utc)
    return {
        "meta": {
            "generated_at": generated_at.isoformat(),
            "clustered_report": str(clustered_report),
            "canonical_report": str(canonical_report) if canonical_report else "",
            "writes_production_db": False,
            "writes_assets_payload": False,
            "writes_targets_json": False,
            "target_row_approved": False,
            **summarize(stories, source_meta),
            "canonical_rows_checked": canonical_meta.get("rows_checked", 0),
        },
        "stories": stories,
    }


def output_prefix(now: datetime | None = None) -> str:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    return f"rio_economic_topic_report_{stamp}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, stories: list[dict[str, Any]]) -> None:
    fieldnames = [
        "representative_row",
        "cluster_key",
        "primary_dimension",
        "article_count",
        "member_rows",
        "date_quality_status",
        "date_quality_policy",
        "date_quality_source_row",
        "date_quality_evidence_rows",
        "sources",
        "title",
        "url",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for story in stories:
            row = dict(story)
            row["member_rows"] = ", ".join(str(item) for item in story.get("member_rows", []))
            row["date_quality_evidence_rows"] = ", ".join(
                str(item) for item in story.get("date_quality_evidence_rows", [])
            )
            row["sources"] = ", ".join(str(item) for item in story.get("sources", []))
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def md_cell(value: Any) -> str:
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    meta = payload["meta"]
    lines = [
        "# Rio Economic Topic Report",
        "",
        f"Generated at: `{meta['generated_at']}`",
        f"Stories: `{meta['story_count']}`",
        f"Articles: `{meta['article_count']}`",
        f"Canonical rows checked: `{meta['canonical_rows_checked']}`",
        f"Target row approved: `{meta['target_row_approved']}`",
        "",
        "Date-quality policy counts:",
        "",
        "```text",
        *[f"{key}={value}" for key, value in meta["date_quality_policy_counts"].items()],
        "```",
        "",
        "| Story Row | Articles | Policy | Date Status | Date Evidence Row | Dimension | Sources | Title |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for story in payload["stories"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(story.get("representative_row")),
                    md_cell(story.get("article_count")),
                    md_cell(story.get("date_quality_policy")),
                    md_cell(story.get("date_quality_status")),
                    md_cell(story.get("date_quality_source_row")),
                    md_cell(story.get("primary_dimension")),
                    md_cell(story.get("sources")),
                    md_cell(story.get("title")),
                ]
            )
            + " |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_reports(payload: dict[str, Any], output_dir: Path, *, now: datetime | None = None) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_prefix(now)
    json_path = output_dir / f"{prefix}.json"
    csv_path = output_dir / f"{prefix}.csv"
    md_path = output_dir / f"{prefix}.md"
    write_json(json_path, payload)
    write_csv(csv_path, payload["stories"])
    write_markdown(md_path, payload)
    return {"json": str(json_path), "csv": str(csv_path), "markdown": str(md_path)}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a scoped Rio economic topic report from review artifacts without touching production data.",
    )
    parser.add_argument("clustered_report", type=Path)
    parser.add_argument("--canonical-report", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=REPORTS_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args.clustered_report, args.canonical_report)
    paths = write_reports(payload, args.output_dir)
    print(
        json.dumps(
            {
                "ok": True,
                "story_count": payload["meta"]["story_count"],
                "article_count": payload["meta"]["article_count"],
                "target_row_approved": payload["meta"]["target_row_approved"],
                "paths": paths,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
