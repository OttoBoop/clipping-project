from __future__ import annotations

from tools import buyer_quote_tracker_check as tracker


BASE_TRACKER = """
## Current Pricing Decision

```text
final_price_decided=false
real_buyer_conversation_count=0
hands_on_demo_reaction_count=0
measured_pilot_run_count=0
```

## Conversation Record Template

| Date | Buyer Type | Current Process | Pain | Desired Frequency | Target Count | Preferred Delivery | Quote Signal | Expected Extras | Operator Risk | Follow-Up |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | vereador / assessor / consultor / campanha | manual / agency / none / tool | misses / noise / summary / speed | weekly / 2x-week / daily | 0 | dashboard / WhatsApp / email / PDF | low / viable / premium / unclear | alerts / adversaries / custom sources | low / medium / high | next action |
"""

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


def test_template_rows_do_not_count_as_buyer_evidence():
    result = tracker.validate_tracker(BASE_TRACKER, BASE_LEDGER)

    assert result["ok"] is True
    assert result["measured"] == {
        "real_buyer_conversation_count": 0,
        "hands_on_demo_reaction_count": 0,
    }


def test_real_buyer_rows_and_demo_markers_must_match_declared_counts():
    text = BASE_TRACKER.replace("real_buyer_conversation_count=0", "real_buyer_conversation_count=1")
    text = text.replace("hands_on_demo_reaction_count=0", "hands_on_demo_reaction_count=1")
    text = text.replace(
        "| YYYY-MM-DD | vereador / assessor / consultor / campanha | manual / agency / none / tool | misses / noise / summary / speed | weekly / 2x-week / daily | 0 | dashboard / WhatsApp / email / PDF | low / viable / premium / unclear | alerts / adversaries / custom sources | low / medium / high | next action |",
        "| YYYY-MM-DD | vereador / assessor / consultor / campanha | manual / agency / none / tool | misses / noise / summary / speed | weekly / 2x-week / daily | 0 | dashboard / WhatsApp / email / PDF | low / viable / premium / unclear | alerts / adversaries / custom sources | low / medium / high | next action |\n"
        "| 2026-05-20 | vereador | manual | misses | 2x-week | 3 | dashboard | viable | none | low | screen_share_demo positive |",
    )

    result = tracker.validate_tracker(text, BASE_LEDGER)

    assert result["ok"] is True
    assert result["measured"]["real_buyer_conversation_count"] == 1
    assert result["measured"]["hands_on_demo_reaction_count"] == 1


def test_final_price_requires_buyer_demo_and_pilot_evidence():
    text = BASE_TRACKER.replace("final_price_decided=false", "final_price_decided=true")

    result = tracker.validate_tracker(text, BASE_LEDGER)

    assert result["ok"] is False
    assert "final price decided before 3 real buyer conversations" in result["failures"]
    assert "final price decided before 1 hands_on_demo or screen_share_demo reaction" in result["failures"]
    assert "final price decided before 1 measured pilot run" in result["failures"]
