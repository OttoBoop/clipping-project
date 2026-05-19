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

from pipeline.collectors import fetch_full_article_text


REPORTS_DIR = PROJECT_ROOT / "data" / "reports"


def parse_dt(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def date_status(original: str, extracted: str, final_url: str) -> str:
    if "news.google.com" in (final_url or ""):
        return "unresolved_google_url"
    original_dt = parse_dt(original)
    extracted_dt = parse_dt(extracted)
    if not extracted_dt:
        return "canonical_date_missing"
    if not original_dt:
        return "original_date_missing"
    delta_days = abs((original_dt.date() - extracted_dt.date()).days)
    if delta_days == 0:
        return "same_day"
    if delta_days <= 2:
        return "near_date"
    return "date_mismatch"


def load_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("input report must be a JSON list or an object with a rows list")
    return [row for row in rows if isinstance(row, dict)]


def review_rows(rows: list[dict[str, Any]], *, max_rows: int, request_timeout: int) -> list[dict[str, Any]]:
    selected = rows[:max_rows] if max_rows > 0 else rows
    reviewed: list[dict[str, Any]] = []
    for index, row in enumerate(selected, 1):
        url = str(row.get("url") or "").strip()
        original_published = str(row.get("published_at") or "").strip()
        result = {
            "row": index,
            "dimension": row.get("dimension", ""),
            "source": row.get("source", ""),
            "original_title": row.get("title", ""),
            "original_url": url,
            "original_published_at": original_published,
            "final_url": "",
            "canonical_title": "",
            "canonical_published_at": "",
            "word_count": "",
            "status": "not_checked",
            "error": "",
        }
        if not url:
            result["status"] = "missing_url"
            reviewed.append(result)
            continue
        try:
            final_url, _raw_html, full_text, canonical_title, canonical_published = fetch_full_article_text(
                url,
                request_timeout=request_timeout,
            )
            result["final_url"] = final_url
            result["canonical_title"] = canonical_title
            result["canonical_published_at"] = canonical_published
            result["word_count"] = str(len((full_text or "").split()))
            result["status"] = date_status(original_published, canonical_published, final_url)
        except Exception as exc:
            result["status"] = "fetch_error"
            result["error"] = f"{type(exc).__name__}: {exc}"
        reviewed.append(result)
    return reviewed


def output_prefix(now: datetime | None = None) -> str:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    return f"rio_economic_canonical_review_{stamp}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "row",
        "dimension",
        "source",
        "original_title",
        "original_url",
        "original_published_at",
        "final_url",
        "canonical_title",
        "canonical_published_at",
        "word_count",
        "status",
        "error",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def md_cell(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    lines = [
        "# Rio Economic Canonical Review",
        "",
        f"Generated at: `{payload['meta']['generated_at']}`",
        f"Input report: `{payload['meta']['input_report']}`",
        f"Rows checked: `{payload['meta']['rows_checked']}`",
        f"Request timeout: `{payload['meta']['request_timeout']}`",
        "",
        "| Row | Dimension | Status | Original Published | Canonical Published | Source | Title |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(row.get("row")),
                    md_cell(row.get("dimension")),
                    md_cell(row.get("status")),
                    md_cell(row.get("original_published_at")),
                    md_cell(row.get("canonical_published_at")),
                    md_cell(row.get("source")),
                    md_cell(row.get("original_title")),
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
    write_csv(csv_path, payload["rows"])
    write_markdown(md_path, payload)
    return {"json": str(json_path), "csv": str(csv_path), "markdown": str(md_path)}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review canonical URL/date evidence for a Rio economic dry-run report without touching production data.",
    )
    parser.add_argument("input_report", type=Path, help="Rio economic dry-run JSON report.")
    parser.add_argument("--max-rows", type=int, default=10)
    parser.add_argument("--request-timeout", type=int, default=8)
    parser.add_argument("--output-dir", type=Path, default=REPORTS_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_rows = load_rows(args.input_report)
    rows = review_rows(
        source_rows,
        max_rows=max(0, args.max_rows),
        request_timeout=max(1, args.request_timeout),
    )
    generated_at = datetime.now(timezone.utc)
    payload = {
        "meta": {
            "generated_at": generated_at.isoformat(),
            "input_report": str(args.input_report),
            "rows_checked": len(rows),
            "request_timeout": max(1, args.request_timeout),
            "writes_production_db": False,
            "writes_assets_payload": False,
            "writes_targets_json": False,
            "stores_article_body": False,
        },
        "rows": rows,
    }
    paths = write_reports(payload, args.output_dir, now=generated_at)
    print(json.dumps({"ok": True, "rows_checked": len(rows), "paths": paths}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
