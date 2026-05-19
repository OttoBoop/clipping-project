#!/usr/bin/env python3
"""Validate the V1 pilot operating ledger without inventing pricing evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = (
    PROJECT_ROOT
    / "md documents"
    / "clipping-segregation-product-loop-2026-05-18"
    / "V1_PILOT_OPERATING_LEDGER.md"
)

STATE_KEYS = {
    "measured_pilot_run_count": int,
    "measured_weekly_summary_count": int,
    "measured_support_issue_count": int,
    "minimum_sustainable_monthly_price_decided": bool,
}
UPDATE_ACTIONS = {"update_run", "qa", "summary", "support", "password_rotation"}


@dataclass
class LedgerRow:
    cells: list[str]

    def cell(self, index: int) -> str:
        return self.cells[index].strip() if index < len(self.cells) else ""


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"expected true/false, got {value!r}")


def parse_state(text: str) -> dict[str, Any]:
    state: dict[str, Any] = {}
    for key, parser in STATE_KEYS.items():
        match = re.search(rf"^{re.escape(key)}=(.+)$", text, flags=re.MULTILINE)
        if not match:
            raise ValueError(f"missing state key: {key}")
        raw = match.group(1).strip()
        state[key] = parse_bool(raw) if parser is bool else parser(raw)
    return state


def rows_after_heading(text: str, heading: str) -> list[LedgerRow]:
    heading_index = text.find(heading)
    if heading_index < 0:
        raise ValueError(f"missing ledger section: {heading}")
    rows: list[LedgerRow] = []
    for line in text[heading_index:].splitlines()[1:]:
        stripped = line.strip()
        if not stripped:
            if rows:
                break
            continue
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if all(set(cell) <= {"-", " "} for cell in cells):
            continue
        rows.append(LedgerRow(cells))
    return rows[1:] if rows else []


def is_real_date(value: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()))


def is_real_week(value: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-W\d{2}", value.strip()))


def measured_counts(text: str) -> dict[str, int]:
    update_rows = rows_after_heading(text, "## Per-Update Ledger")
    weekly_rows = rows_after_heading(text, "## Weekly Summary Ledger")
    real_updates = [row for row in update_rows if is_real_date(row.cell(0))]
    real_weeklies = [row for row in weekly_rows if is_real_week(row.cell(0))]

    unknown_actions = sorted({row.cell(2) for row in real_updates if row.cell(2) not in UPDATE_ACTIONS})
    if unknown_actions:
        raise ValueError(f"unknown per-update action(s): {', '.join(unknown_actions)}")

    return {
        "measured_pilot_run_count": sum(1 for row in real_updates if row.cell(2) == "update_run"),
        "measured_weekly_summary_count": len(real_weeklies),
        "measured_support_issue_count": sum(1 for row in real_updates if row.cell(2) == "support"),
    }


def validate_ledger(text: str) -> dict[str, Any]:
    declared = parse_state(text)
    measured = measured_counts(text)
    failures: list[str] = []

    for key, actual in measured.items():
        if declared.get(key) != actual:
            failures.append(f"{key} declared={declared.get(key)} measured={actual}")

    if declared["minimum_sustainable_monthly_price_decided"]:
        if measured["measured_pilot_run_count"] < 1:
            failures.append("price decided before any measured update_run")
        if measured["measured_weekly_summary_count"] < 1:
            failures.append("price decided before any measured weekly summary")

    return {
        "ok": not failures,
        "declared": declared,
        "measured": measured,
        "failures": failures,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate V1 pilot ledger counts.")
    parser.add_argument("ledger", nargs="?", type=Path, default=DEFAULT_LEDGER)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate_ledger(args.ledger.read_text(encoding="utf-8"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
