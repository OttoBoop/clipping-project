from __future__ import annotations

import importlib
import json
import sqlite3
import sys

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
    assert public["primaryKeys"] == ["flavio_valle", "pedro_angelito", "bernardo_rubiao"]
    by_key = {row["key"]: row for row in public["targets"]}
    assert by_key["flavio_valle"]["primary"] is True
    assert by_key["ana_maria"]["primary"] is False
    assert by_key["ana_maria_2"]["primary"] is False


def test_build_update_spec_uses_safe_all_collector_and_rejects_future_or_long_dates(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)

    spec = jobs.build_update_spec(
        {
            "preset": "custom",
            "target_keys": ["flavio_valle"],
            "date_from": "2026-04-29",
            "date_to": "2026-04-30",
            "collector": "direct_scrape",
            "export": False,
        }
    )

    assert spec["collector"] == "all"
    assert spec["skip_direct_scrape"] is True
    assert "direct_scrape" not in jobs.SAFE_COLLECTORS

    try:
        jobs.build_update_spec(
            {
                "preset": "custom",
                "target_keys": ["flavio_valle"],
                "date_from": "2026-04-20",
                "date_to": "2026-04-30",
            }
        )
    except ValueError as exc:
        assert str(exc) == "periodo_muito_longo"
    else:
        raise AssertionError("expected periodo_muito_longo")


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


def test_sqlite_wal_is_checkpointed_before_artifact_upload(tmp_path):
    from web_app.storage_bridge import checkpoint_sqlite_wal

    db_file = tmp_path / "clipping.db"
    with sqlite3.connect(db_file) as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE rows (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO rows (name) VALUES ('persisted')")

    wal_file = db_file.with_name(db_file.name + "-wal")
    assert wal_file.exists()

    checkpoint_sqlite_wal(db_file)

    copied = tmp_path / "copied.db"
    copied.write_bytes(db_file.read_bytes())
    with sqlite3.connect(copied) as conn:
        rows = conn.execute("SELECT name FROM rows").fetchall()
    assert rows == [("persisted",)]
