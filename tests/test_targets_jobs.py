from __future__ import annotations

import importlib
import json
import sqlite3
import sys
from types import SimpleNamespace

from pipeline.database import ClippingDB


def reload_admin_modules(monkeypatch, tmp_path):
    db_file = tmp_path / "clipping.db"
    ClippingDB(db_file)
    monkeypatch.setenv("CLIPPING_DB_PATH", str(db_file))
    for name in list(sys.modules):
        if name in {"web_app.db_admin", "web_app.jobs"}:
            del sys.modules[name]
    db_admin = importlib.import_module("web_app.db_admin")
    jobs = importlib.import_module("web_app.jobs")
    db_admin.ensure_app_tables(db_file)
    return db_admin, jobs, db_file


def test_create_secondary_target_writes_sanitized_non_primary_target_atomically(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {
                    "key": "flavio_valle",
                    "label": "Flavio Valle",
                    "display_name": "Flavio Valle",
                    "primary": False,
                    "className": "",
                    "keywords": ["Flavio Valle"],
                },
                {
                    "key": "ana_maria",
                    "label": "Ana Maria",
                    "display_name": "Ana Maria",
                    "primary": True,
                    "className": "primary",
                    "keywords": ["Ana Maria"],
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    created = db_admin.create_secondary_target(
        {
            "display_name": "Ana Maria",
            "keywords": ["Ana Maria", "  ", "Secretaria Ana Maria"],
            "aliases": ["A. Maria", "A. Maria"],
            "primary": True,
            "className": "primary",
        }
    )

    assert created == {
        "key": "ana_maria_2",
        "label": "Ana Maria",
        "display_name": "Ana Maria",
        "className": "",
        "primary": False,
        "keywords": ["Ana Maria", "Secretaria Ana Maria"],
        "exact_aliases": ["A. Maria"],
    }
    stored = json.loads(targets_path.read_text(encoding="utf-8"))
    assert stored[-1]["key"] == "ana_maria_2"
    assert stored[-1]["primary"] is False
    assert stored[-1]["className"] == ""

    public = db_admin.public_targets()
    assert public["primaryKeys"] == ["flavio_valle", "pedro_angelito"]
    by_key = {row["key"]: row for row in public["targets"]}
    assert by_key["flavio_valle"]["primary"] is True
    assert by_key["ana_maria"]["primary"] is False
    assert by_key["ana_maria_2"]["primary"] is False


def test_create_secondary_target_simple_path_uses_display_name_keyword(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {
                    "key": "flavio_valle",
                    "label": "Flavio Valle",
                    "display_name": "Flavio Valle",
                    "primary": True,
                    "keywords": ["Flavio Valle"],
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    created = db_admin.create_secondary_target({"display_name": "Carla Souza", "primary": True, "className": "primary"})

    assert created["key"] == "carla_souza"
    assert created["primary"] is False
    assert created["className"] == ""
    assert created["keywords"] == ["Carla Souza"]
    stored = json.loads(targets_path.read_text(encoding="utf-8"))
    assert stored[-1]["primary"] is False
    assert stored[-1]["keywords"] == ["Carla Souza"]


def test_normalize_targets_file_forces_current_primary_contract(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "flavio_valle", "label": "Flavio Valle", "primary": False, "keywords": ["Flavio Valle"]},
                {"key": "pedro_angelito", "label": "Pedro Angelito", "primary": False, "keywords": ["Pedro Angelito"]},
                {"key": "bernardo_rubiao", "label": "Bernardo Rubiao", "primary": True, "className": "primary", "keywords": ["Bernardo Rubiao"]},
                {"key": "ana_maria", "label": "Ana Maria", "primary": True, "className": "primary", "keywords": ["Ana Maria"]},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    changed = db_admin.normalize_targets_file()

    assert changed is True
    public = db_admin.public_targets()
    assert public["primaryKeys"] == ["flavio_valle", "pedro_angelito"]
    by_key = {row["key"]: row for row in public["targets"]}
    assert by_key["flavio_valle"]["primary"] is True
    assert by_key["pedro_angelito"]["primary"] is True
    assert by_key["bernardo_rubiao"]["primary"] is False
    assert by_key["ana_maria"]["primary"] is False
    stored = {row["key"]: row for row in json.loads(targets_path.read_text(encoding="utf-8"))}
    assert stored["pedro_angelito"]["className"] == "primary"
    assert stored["bernardo_rubiao"]["className"] == ""


def test_build_update_spec_uses_safe_all_collector_and_accepts_long_custom_dates(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)

    spec = jobs.build_update_spec(
        {
            "preset": "custom",
            "target_keys": ["flavio_valle"],
            "date_from": "2026-04-01",
            "date_to": "2026-04-30",
            "collector": "direct_scrape",
            "export": False,
        }
    )

    assert spec["collector"] == "all"
    assert spec["skip_direct_scrape"] is True
    assert "direct_scrape" not in jobs.SAFE_COLLECTORS
    assert spec["date_from"] == "2026-04-01"
    assert spec["date_to"] == "2026-04-30"
    assert spec["max_candidates"] == 90000
    assert spec["max_process_seconds"] == 90000

    try:
        jobs.build_update_spec(
            {
                "preset": "custom",
                "target_keys": ["flavio_valle"],
                "date_from": "2026-05-01",
                "date_to": "2099-01-01",
            }
        )
    except ValueError as exc:
        assert str(exc) == "data_futura"
    else:
        raise AssertionError("expected data_futura")


def test_completo_preset_uses_current_primary_circle_without_bernardo(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)

    spec = jobs.build_update_spec({"preset": "completo", "export": True})

    assert spec["target_keys"] == ["flavio_valle", "pedro_angelito"]
    assert "bernardo_rubiao" not in spec["target_keys"]
    assert spec["max_candidates"] == 90000
    assert spec["max_process_seconds"] == 90000


def test_job_progress_contract_includes_target_source_counts_and_recent_events(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    job_id = "progress-observed"
    jobs.create_job(
        job_id,
        "update",
        {
            "preset": "custom",
            "collector": "all",
            "target_keys": ["flavio_valle"],
            "date_from": "2026-04-29",
            "date_to": "2026-04-30",
        },
        started_by="admin",
    )
    jobs.record_progress(
        job_id,
        "run_started",
        {"collector": "all", "sources_total": 1, "candidates_total": 3},
        target_key="flavio_valle",
        target_label="Flavio Valle",
    )
    jobs.record_progress(
        job_id,
        "source_collected",
        {"source_name": "Google News", "source_type": "google_news", "candidates_total": 3},
        target_key="flavio_valle",
        target_label="Flavio Valle",
    )
    jobs.record_progress(
        job_id,
        "source_progress",
        {"source_name": "Google News", "source_type": "google_news", "candidates_seen": 2, "articles_inserted": 1},
        target_key="flavio_valle",
        target_label="Flavio Valle",
    )
    jobs.update_job(job_id, status="running", articles_inserted=1, mentions_inserted=1, stories_touched=1)

    observed = jobs.get_job(job_id)

    assert observed is not None
    assert observed["progress"]["targetKeys"] == ["flavio_valle"]
    assert observed["progress"]["targetLabels"] == {"flavio_valle": "Flavio Valle"}
    assert observed["progress"]["sourcesTotal"] == 1
    assert observed["progress"]["candidatesSeen"] == 2
    assert observed["progress"]["candidatesTotal"] == 3
    assert observed["progress"]["articlesInserted"] == 1
    latest = observed["recentEvents"][0]
    assert latest["payload"]["target_key"] == "flavio_valle"
    assert latest["payload"]["target_label"] == "Flavio Valle"
    assert latest["payload"]["source"] == "Google News"


def test_cancel_active_marks_job_cancelled_and_clears_active_state(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    jobs.create_job(
        "cancel-me",
        "update",
        {
            "preset": "custom",
            "collector": "all",
            "target_keys": ["flavio_valle"],
            "date_from": "2026-04-01",
            "date_to": "2026-04-30",
        },
        started_by="coworker",
    )
    manager = jobs.JobManager(SimpleNamespace(writes_available=True))

    cancelled = manager.cancel_active()

    assert cancelled["status"] == "cancelled"
    assert jobs.get_active_job() is None
    events = jobs.get_job("cancel-me")["events"]
    assert any(event["event"] == "job_cancelled" for event in events)


def test_run_export_snapshot_preserves_historical_merge_contract(monkeypatch, tmp_path):
    _, jobs, db_file = reload_admin_modules(monkeypatch, tmp_path)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return SimpleNamespace(returncode=0, stdout="exported\n")

    monkeypatch.setattr(jobs.subprocess, "run", fake_run)

    jobs.run_export_snapshot("export-contract")

    cmd = calls[0]["cmd"]
    assert cmd[1:] == [
        "tools/export_mobile_snapshot.py",
        "--all-stories",
        "--merge-from",
        "index.html",
        "--db",
        str(db_file.resolve()),
    ]
    assert calls[0]["cwd"] == jobs.ROOT


def test_run_ingestion_builds_collection_queries_for_selected_target(monkeypatch, tmp_path):
    from pipeline import ingest

    captured = {}

    def fake_collect_google_news(*, queries, **_kwargs):
        captured["queries"] = list(queries)
        return []

    def fake_process_candidates(source_name, source_type, candidates, *, options=None, progress_callback=None):
        return ingest.IngestionResult(
            source_name=source_name,
            source_type=source_type,
            candidates_seen=0,
            articles_inserted=0,
            mentions_inserted=0,
            stories_touched=0,
            errors=[],
        )

    monkeypatch.setattr(ingest, "collect_google_news", fake_collect_google_news)
    monkeypatch.setattr(ingest, "process_candidates", fake_process_candidates)

    ingest.run_ingestion(
        "google_news",
        options=ingest.IngestionOptions(
            target_keys=["pedro_angelito"],
            date_from="2026-04-01",
            date_to="2026-05-01",
            db_path=str(tmp_path / "selected-target.db"),
        ),
    )

    assert captured["queries"]
    assert any("Pedro Angelito" in query for query in captured["queries"])
    assert all("Flavio Valle" not in query and "Flávio Valle" not in query for query in captured["queries"])


def test_classification_listing_survives_missing_article_context(tmp_path):
    db_file = tmp_path / "clipping.db"
    db = ClippingDB(db_file)
    mention_id = db.create_mention(
        article_id=643,
        target_key="bernardo_rubiao",
        target_name="Bernardo Rubiao",
    )
    db.upsert_classification(
        mention_id=mention_id,
        article_sentiment="neutral",
        target_sentiment="neutral",
    )

    rows = db.get_classifications_with_context(limit=10)

    assert len(rows) == 1
    assert rows[0]["article_id"] == 643
    assert rows[0]["target_key"] == "bernardo_rubiao"
    assert rows[0]["article_sentiment"] == "neutral"


def test_sqlite_snapshot_includes_uncheckpointed_wal_rows(tmp_path):
    from web_app.storage_bridge import sqlite_snapshot_bytes

    db_file = tmp_path / "clipping.db"
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("CREATE TABLE rows (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    conn.execute("INSERT INTO rows (name) VALUES ('persisted')")
    conn.commit()

    wal_file = db_file.with_name(db_file.name + "-wal")
    assert wal_file.exists()

    snapshot = sqlite_snapshot_bytes(db_file)
    conn.close()

    copied = tmp_path / "copied.db"
    copied.write_bytes(snapshot)
    with sqlite3.connect(copied) as conn:
        rows = conn.execute("SELECT name FROM rows").fetchall()
    assert rows == [("persisted",)]
