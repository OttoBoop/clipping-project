from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
CLUSTER_FIELDS = [
    "cluster_key",
    "cluster_label",
    "primary_dimension",
    "secondary_dimensions",
    "representative_url",
    "duplicate_of",
]


def load_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("rows"), list):
        raise ValueError("input report must be a JSON object with a rows list")
    return payload


def load_annotation_groups(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    groups = payload.get("annotations") if isinstance(payload, dict) else payload
    if not isinstance(groups, list):
        raise ValueError("annotation file must be a JSON list or an object with an annotations list")
    return [group for group in groups if isinstance(group, dict)]


def row_url(rows: list[dict[str, Any]], row_number: int) -> str:
    index = row_number - 1
    if index < 0 or index >= len(rows):
        return ""
    return str(rows[index].get("url") or "")


def normalize_secondary(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value or "").strip()


def build_annotation_map(rows: list[dict[str, Any]], groups: list[dict[str, Any]]) -> dict[int, dict[str, str]]:
    annotations: dict[int, dict[str, str]] = {}
    for group in groups:
        row_numbers = [int(row) for row in group.get("rows", [])]
        representative_row = int(group.get("representative_row") or (row_numbers[0] if row_numbers else 0))
        representative_url = row_url(rows, representative_row)
        for row_number in row_numbers:
            annotations[row_number] = {
                "cluster_key": str(group.get("cluster_key") or "").strip(),
                "cluster_label": str(group.get("cluster_label") or "").strip(),
                "primary_dimension": str(group.get("primary_dimension") or "").strip(),
                "secondary_dimensions": normalize_secondary(group.get("secondary_dimensions")),
                "representative_url": representative_url,
                "duplicate_of": "" if row_number == representative_row else f"row:{representative_row}",
            }
    return annotations


def annotated_rows(rows: list[dict[str, Any]], annotations: dict[int, dict[str, str]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        next_row = dict(row)
        for field in CLUSTER_FIELDS:
            next_row[field] = ""
        next_row.update(annotations.get(index, {}))
        output.append(next_row)
    return output


def output_prefix(now: datetime | None = None) -> str:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    return f"rio_economic_clustered_review_{stamp}"


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
        *CLUSTER_FIELDS,
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def md_cell(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    lines = [
        "# Rio Economic Clustered Review",
        "",
        f"Generated at: `{payload['meta']['generated_at']}`",
        f"Input report: `{payload['meta']['input_report']}`",
        f"Annotations file: `{payload['meta']['annotations_file']}`",
        f"Rows: `{payload['meta']['row_count']}`",
        f"Clustered rows: `{payload['meta']['clustered_row_count']}`",
        f"Cluster count: `{payload['meta']['cluster_count']}`",
        "",
        "| Row | Cluster | Primary Dimension | Duplicate Of | Dimension | Source | Title |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, row in enumerate(rows, 1):
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(index),
                    md_cell(row.get("cluster_key")),
                    md_cell(row.get("primary_dimension")),
                    md_cell(row.get("duplicate_of")),
                    md_cell(row.get("dimension")),
                    md_cell(row.get("source")),
                    md_cell(row.get("title")),
                ]
            )
            + " |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_payload(input_report: Path, annotations_file: Path) -> dict[str, Any]:
    source_payload = load_payload(input_report)
    rows = source_payload["rows"]
    groups = load_annotation_groups(annotations_file)
    annotation_map = build_annotation_map(rows, groups)
    output_rows = annotated_rows(rows, annotation_map)
    generated_at = datetime.now(timezone.utc)
    return {
        "meta": {
            "generated_at": generated_at.isoformat(),
            "input_report": str(input_report),
            "annotations_file": str(annotations_file),
            "row_count": len(output_rows),
            "cluster_count": len({row.get("cluster_key") for row in output_rows if row.get("cluster_key")}),
            "clustered_row_count": sum(1 for row in output_rows if row.get("cluster_key")),
            "writes_production_db": False,
            "writes_assets_payload": False,
            "writes_targets_json": False,
        },
        "source_meta": source_payload.get("meta", {}),
        "rows": output_rows,
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
    parser = argparse.ArgumentParser(description="Apply manual Rio economic cluster annotations to a dry-run report.")
    parser.add_argument("input_report", type=Path)
    parser.add_argument("annotations_file", type=Path)
    parser.add_argument("--output-dir", type=Path, default=REPORTS_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args.input_report, args.annotations_file)
    paths = write_reports(payload, args.output_dir)
    print(
        json.dumps(
            {
                "ok": True,
                "row_count": payload["meta"]["row_count"],
                "cluster_count": payload["meta"]["cluster_count"],
                "clustered_row_count": payload["meta"]["clustered_row_count"],
                "paths": paths,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
