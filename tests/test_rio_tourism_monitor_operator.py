from __future__ import annotations

import urllib.error
from datetime import date
from types import SimpleNamespace

from tools import rio_tourism_monitor as mon


def test_month_window_caps_current_month_at_today() -> None:
    assert mon.month_window(2026, 7, today=date(2026, 7, 1)) == ("2026-07-01", "2026-07-01")


def test_backfill_windows_month_skips_future_months() -> None:
    windows = mon.backfill_windows(2026, 2026, mode="month", today=date(2026, 3, 15))

    assert windows == [
        ("2026-01", "2026-01-01", "2026-01-31"),
        ("2026-02", "2026-02-01", "2026-02-28"),
        ("2026-03", "2026-03-01", "2026-03-15"),
    ]


def test_backfill_windows_year_keeps_existing_year_mode() -> None:
    assert mon.backfill_windows(2025, 2025, mode="year") == [("2025", "2025-01-01", "2025-12-31")]


def test_resource_barriers_flag_memory_and_disk() -> None:
    snapshot = {
        "memory": {"vm_rss_mib": 546.5},
        "disk": {"filesystem": {"free_mib": 45000}},
    }
    args = SimpleNamespace(memory_rss_max_mib=512, disk_free_min_mib=50000)

    assert mon.resource_barriers(snapshot, args) == [
        "memory_rss_mib:546.50>512.00",
        "disk_free_mib:45000.00<50000.00",
    ]


def test_resource_barriers_are_disabled_by_default() -> None:
    snapshot = {
        "memory": {"vm_rss_mib": 999},
        "disk": {"filesystem": {"free_mib": 1}},
    }
    args = SimpleNamespace(memory_rss_max_mib=0, disk_free_min_mib=0)

    assert mon.resource_barriers(snapshot, args) == []


def test_summarize_endpoint_trims_verbose_current_job_spec() -> None:
    summary = mon.summarize_endpoint(
        200,
        {
            "current": {
                "id": "job-1",
                "status": "succeeded",
                "spec_json": "x" * 1000,
                "funnel": {"articles_saved": 10},
            }
        },
    )

    assert summary["current"] == {
        "id": "job-1",
        "status": "succeeded",
        "funnel": {"articles_saved": 10},
    }


def test_client_request_returns_structured_network_failure(monkeypatch) -> None:
    client = mon.Client("https://example.test")

    def fail_open(_request, timeout=0):
        raise urllib.error.URLError("[Errno -3] Temporary failure in name resolution")

    monkeypatch.setattr(client.opener, "open", fail_open)

    status, body = client.request("GET", "/api/update/status")

    assert status == 0
    assert body["error"] == "request_failed"
    assert "Temporary failure" in body["detail"]
