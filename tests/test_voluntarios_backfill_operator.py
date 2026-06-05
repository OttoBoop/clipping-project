from __future__ import annotations

from pathlib import Path

from tools import voluntarios_backfill_operator as op


def test_parse_target_keys_accepts_json_string() -> None:
    raw = '["seguranca_presente", "crime"]'

    assert op.parse_target_keys(raw) == ["seguranca_presente", "crime"]


def test_summarize_status_parses_production_string_target_keys() -> None:
    payload = {
        "current": {
            "id": op.JOB_ID,
            "status": "interrupted_resumable",
            "target_keys": "[\"seguranca_presente\", \"crime\"]",
            "date_from": "2014-01-01",
            "date_to": "2026-06-02",
            "sourceRunCounts": {"complete": 23, "interrupted_resumable": 22889},
        }
    }

    summary = op.summarize_status(payload)

    assert summary["targetKeys"] == ["seguranca_presente", "crime"]
    assert summary["sourceRunCounts"] == {"complete": 23, "interrupted_resumable": 22889}


def test_password_note_parser_finds_plain_voluntarios_password() -> None:
    text = """
# Senhas

## Admin
| **Senha** | `admin-secret` |

## Voluntários-Lab-Políticas-Públicas (voluntarios_lab_politicas) - 2026-06-02
- Production viewer password: viewer-secret
"""

    parsed = op.parse_password_note(text)

    assert "admin-secret" in parsed["candidates"]
    assert "viewer-secret" in parsed["candidates"]
    assert parsed["viewerPassword"] == "viewer-secret"


def test_update_password_note_replaces_only_voluntarios_line(tmp_path: Path) -> None:
    note = tmp_path / "senhas.md"
    note.write_text(
        """
## Other
- Production viewer password: keep-me

## Voluntários-Lab-Políticas-Públicas (voluntarios_lab_politicas) - 2026-06-02
- Production viewer password: old
""".lstrip(),
        encoding="utf-8",
    )

    op.update_password_note("new-secret", path=note)

    text = note.read_text(encoding="utf-8")
    assert "- Production viewer password: keep-me" in text
    assert "- Production viewer password: new-secret" in text
    assert "- Production viewer password: old" not in text


def test_detect_barriers_flags_resumable_and_viewer_login_failure() -> None:
    summary = {
        "status": {
            "jobId": op.JOB_ID,
            "status": "interrupted_resumable",
            "coverage": "",
            "targetKeysExact": True,
            "dateFrom": "2014-01-01",
            "dateTo": "2026-06-02",
        },
        "viewerLogin": {"ok": False},
        "targets": {"primaryExact": True},
        "viewerProfile": {"found": True, "missing": [], "extra": []},
        "http": {},
        "memory": {"vm_rss_mib": 120},
        "disk": {"filesystem": {"free_mib": 2048}},
        "sqlite": {"probes": {"readOnly": {"quickCheck": "ok"}}},
    }

    barriers = op.detect_barriers(summary)

    assert "job_status:interrupted_resumable" in barriers
    assert "viewer_login_failed" in barriers


def test_markdown_entry_does_not_require_secrets() -> None:
    entry = op.markdown_entry(
        "Baseline",
        {
            "sampledAt": "2026-06-04 10:00:00 -03",
            "status": {"jobId": op.JOB_ID, "status": "running", "sourceRunCounts": {}},
            "viewerLogin": {"ok": True},
            "viewerProfile": {"found": True},
            "targets": {"primaryExact": True},
            "asset": {},
            "live": {},
            "memory": {},
            "disk": {},
            "sqlite": {"files": {}},
            "http": {},
            "events": {"latest": []},
            "storage": {"enabled": False},
            "barriers": [],
        },
    )

    assert "Baseline" in entry
    assert "Production viewer password" not in entry


def test_summarize_events_keeps_source_run_insert_metrics() -> None:
    summary = op.summarize_events(
        {
            "events": [
                {
                    "created_at": "2026-06-05T12:13:06+00:00",
                    "event": "source_run_checkpoint",
                    "payload": {
                        "target_key": "seguranca_presente",
                        "source_name": "Agenda do Poder",
                        "status": "pending",
                        "candidates_seen": 25,
                        "candidates_total": 25,
                        "articles_inserted": 9,
                        "mentions_inserted": 9,
                        "stories_touched": 9,
                    },
                }
            ]
        }
    )

    event = summary["latest"][0]
    assert event["candidatesTotal"] == 25
    assert event["articlesInserted"] == 9
    assert event["mentionsInserted"] == 9
    assert event["storiesTouched"] == 9


def test_ui_markdown_entry_records_playwright_contract() -> None:
    entry = op.markdown_entry(
        "Playwright UI Contract Check",
        {
            "sampledAt": "2026-06-04 10:30:00 -03",
            "ui": {
                "profileListed": True,
                "loginHttp": 200,
                "targetsHttp": 200,
                "targetContract": {"count": 18, "primaryExact": True},
                "primaryKeys": op.EXPECTED_TARGET_KEYS,
                "checkedPrimary": op.EXPECTED_TARGET_KEYS,
                "secondaryKeys": [],
                "primaryExact": True,
                "checkedPrimaryExact": True,
                "secondaryEmpty": True,
                "runnerStatus": "Atualizando",
                "errors": [],
            },
            "barriers": [],
        },
    )

    assert "Profile listed: `True`" in entry
    assert "Viewer login HTTP: `200`" in entry
    assert "Primary keys exact: `True`; default-checked exact: `True`" in entry
    assert "Secondary keys: `[]`; secondary empty `True`" in entry
    assert "Production viewer password" not in entry
