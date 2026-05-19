from __future__ import annotations

from tools import pilot_ledger_check as ledger


BASE_LEDGER = """
## Current Measurement State

```text
measured_pilot_run_count=0
measured_weekly_summary_count=0
measured_support_issue_count=0
minimum_sustainable_monthly_price_decided=false
```

## Per-Update Ledger

| Date | Profile | Action | Minutes | Targets Checked | Useful Stories | False Positives | Missed Items | AI/Tool Cost Note | Support Issue | Follow-Up |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | profile_key | update_run / qa / summary / support / password_rotation | 0 | 0 | 0 | 0 | 0 | none | none | next action |

## Weekly Summary Ledger

| Week | Minutes To Prepare | Bullets Sent | Manual Screenshots/Exports | Buyer Reply | Renewal Signal | Scope Creep Risk |
| --- | --- | --- | --- | --- | --- | --- |
| YYYY-WW | 0 | 0 | none | none | unknown | none |
"""


def test_template_rows_do_not_count_as_pilot_evidence():
    result = ledger.validate_ledger(BASE_LEDGER)

    assert result["ok"] is True
    assert result["measured"] == {
        "measured_pilot_run_count": 0,
        "measured_weekly_summary_count": 0,
        "measured_support_issue_count": 0,
    }


def test_real_rows_must_match_declared_counts():
    text = BASE_LEDGER.replace("measured_pilot_run_count=0", "measured_pilot_run_count=1")
    text = text.replace(
        "| YYYY-MM-DD | profile_key | update_run / qa / summary / support / password_rotation | 0 | 0 | 0 | 0 | 0 | none | none | next action |",
        "| YYYY-MM-DD | profile_key | update_run / qa / summary / support / password_rotation | 0 | 0 | 0 | 0 | 0 | none | none | next action |\n"
        "| 2026-05-20 | prospect_alpha | update_run | 45 | 3 | 8 | 2 | 0 | none | review |",
    )

    result = ledger.validate_ledger(text)

    assert result["ok"] is True
    assert result["measured"]["measured_pilot_run_count"] == 1


def test_price_decision_requires_update_and_weekly_summary_evidence():
    text = BASE_LEDGER.replace(
        "minimum_sustainable_monthly_price_decided=false",
        "minimum_sustainable_monthly_price_decided=true",
    )

    result = ledger.validate_ledger(text)

    assert result["ok"] is False
    assert "price decided before any measured update_run" in result["failures"]
    assert "price decided before any measured weekly summary" in result["failures"]
