#!/usr/bin/env python3
"""Validate buyer quote evidence before pricing decisions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import pilot_ledger_check  # noqa: E402


DEFAULT_TRACKER = (
    PROJECT_ROOT
    / "md documents"
    / "clipping-segregation-product-loop-2026-05-18"
    / "BUYER_QUOTE_VALIDATION_TRACKER.md"
)
DEFAULT_LEDGER = pilot_ledger_check.DEFAULT_LEDGER

STATE_KEYS = {
    "final_price_decided": bool,
    "real_buyer_conversation_count": int,
    "hands_on_demo_reaction_count": int,
    "measured_pilot_run_count": int,
}


@dataclass
class TableRow:
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


def rows_after_heading(text: str, heading: str) -> list[TableRow]:
    heading_index = text.find(heading)
    if heading_index < 0:
        raise ValueError(f"missing tracker section: {heading}")
    rows: list[TableRow] = []
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
        rows.append(TableRow(cells))
    return rows[1:] if rows else []


def is_real_date(value: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()))


def measured_counts(text: str) -> dict[str, int]:
    rows = rows_after_heading(text, "## Conversation Record Template")
    real_rows = [row for row in rows if is_real_date(row.cell(0))]
    hands_on_rows = [
        row
        for row in real_rows
        if "hands_on_demo" in " ".join(row.cells).lower()
        or "screen_share_demo" in " ".join(row.cells).lower()
    ]
    return {
        "real_buyer_conversation_count": len(real_rows),
        "hands_on_demo_reaction_count": len(hands_on_rows),
    }


def validate_tracker(text: str, ledger_text: str | None = None) -> dict[str, Any]:
    declared = parse_state(text)
    measured = measured_counts(text)
    failures: list[str] = []

    for key, actual in measured.items():
        if declared.get(key) != actual:
            failures.append(f"{key} declared={declared.get(key)} measured={actual}")

    ledger_result: dict[str, Any] | None = None
    if ledger_text is not None:
        ledger_result = pilot_ledger_check.validate_ledger(ledger_text)
        pilot_count = int(ledger_result["measured"]["measured_pilot_run_count"])
        if declared["measured_pilot_run_count"] != pilot_count:
            failures.append(
                "measured_pilot_run_count "
                f"declared={declared['measured_pilot_run_count']} ledger={pilot_count}"
            )

    if declared["final_price_decided"]:
        if measured["real_buyer_conversation_count"] < 3:
            failures.append("final price decided before 3 real buyer conversations")
        if measured["hands_on_demo_reaction_count"] < 1:
            failures.append("final price decided before 1 hands_on_demo or screen_share_demo reaction")
        if declared["measured_pilot_run_count"] < 1:
            failures.append("final price decided before 1 measured pilot run")

    return {
        "ok": not failures,
        "declared": declared,
        "measured": measured,
        "ledger": ledger_result,
        "failures": failures,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate buyer quote tracker evidence.")
    parser.add_argument("tracker", nargs="?", type=Path, default=DEFAULT_TRACKER)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ledger_text = args.ledger.read_text(encoding="utf-8") if args.ledger else None
    result = validate_tracker(args.tracker.read_text(encoding="utf-8"), ledger_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
