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
        "archived": False,
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


def test_update_archive_and_restore_secondary_target(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "flavio_valle", "label": "Flavio Valle", "keywords": ["Flavio Valle"]},
                {
                    "key": "instituto_aurora",
                    "label": "Instituto Aurora",
                    "display_name": "Instituto Aurora",
                    "keywords": ["Instituto Aurora", "Projeto Alfa"],
                    "exact_aliases": ["Aurora"],
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    updated = db_admin.update_secondary_target(
        "instituto_aurora",
        {"display_name": "Instituto Aurora Novo", "keywords": ["Projeto Alfa"], "exact_aliases": ["Aurora", "I. Aurora"]},
    )

    assert updated["label"] == "Instituto Aurora Novo"
    assert updated["keywords"] == ["Instituto Aurora Novo", "Projeto Alfa"]
    assert updated["exact_aliases"] == ["Aurora", "I. Aurora"]

    archived = db_admin.archive_secondary_target("instituto_aurora", "Erro de cadastro.")
    assert archived["archived"] is True
    assert archived["archive_reason"] == "Erro de cadastro."
    assert "instituto_aurora" not in {row["key"] for row in db_admin.public_targets()["targets"]}
    assert "instituto_aurora" in {row["key"] for row in db_admin.public_targets(include_archived=True)["targets"]}

    restored = db_admin.restore_secondary_target("instituto_aurora")
    assert restored["archived"] is False
    assert "instituto_aurora" in {row["key"] for row in db_admin.public_targets()["targets"]}


def test_primary_targets_cannot_be_managed_as_secondary(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(json.dumps([{"key": "flavio_valle", "label": "Flavio Valle"}]), encoding="utf-8")
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    for operation in (
        lambda: db_admin.update_secondary_target("flavio_valle", {"display_name": "Outro Nome"}),
        lambda: db_admin.archive_secondary_target("flavio_valle"),
        lambda: db_admin.restore_secondary_target("flavio_valle"),
    ):
        try:
            operation()
        except db_admin.ValidationError as exc:
            assert "Nomes principais" in str(exc)
        else:
            raise AssertionError("primary target mutation should fail")


def test_known_test_targets_are_auto_archived_and_hidden(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "flavio_valle", "label": "Flavio Valle", "keywords": ["Flavio Valle"]},
                {"key": "atlas_teste_secundario", "label": "Atlas Teste Secundario"},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    active_keys = {row["key"] for row in db_admin.public_targets()["targets"]}
    all_rows = {row["key"]: row for row in db_admin.public_targets(include_archived=True)["targets"]}

    assert "atlas_teste_secundario" not in active_keys
    assert all_rows["atlas_teste_secundario"]["archived"] is True
    try:
        db_admin.validate_target_keys(["atlas_teste_secundario"])
    except db_admin.ValidationError as exc:
        assert str(exc) == "Nome acompanhado desconhecido."
    else:
        raise AssertionError("archived test target should not validate for updates")


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


def test_job_progress_uses_live_source_totals_before_target_finishes(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    job_id = "shakira-live-progress"
    jobs.create_job(
        job_id,
        "update",
        {
            "preset": "custom",
            "collector": "all",
            "target_keys": ["shakira"],
            "date_from": "2026-04-01",
            "date_to": "2026-05-04",
        },
        started_by="coworker",
    )
    jobs.update_job(job_id, status="running")

    jobs.record_progress(
        job_id,
        "source_progress",
        {
            "source_name": "Agenda do Poder",
            "source_type": "wordpress_api",
            "candidates_seen": 30,
            "candidates_total": 86,
            "articles_inserted": 29,
            "mentions_inserted": 29,
            "stories_touched": 29,
        },
        target_key="shakira",
        target_label="shakira",
    )

    observed = jobs.get_job(job_id)

    assert observed["articles_inserted"] == 29
    assert observed["mentions_inserted"] == 29
    assert observed["stories_touched"] == 29
    assert observed["progress"]["articlesInserted"] == 29
    assert observed["progress"]["mentionsInserted"] == 29
    assert observed["progress"]["storiesTouched"] == 29
    assert observed["progress"]["targetKeys"] == ["shakira"]


def test_article_saved_events_drive_live_results_and_totals(monkeypatch, tmp_path):
    _, jobs, db_file = reload_admin_modules(monkeypatch, tmp_path)
    monkeypatch.setattr(jobs.artifact_store, "enabled", False)
    monkeypatch.setattr(jobs, "target_labels", lambda include_archived=False: {"shakira": "shakira"})
    job_id = "shakira-live-results"
    jobs.create_job(
        job_id,
        "update",
        {
            "preset": "custom",
            "collector": "all",
            "target_keys": ["shakira"],
            "date_from": "2026-04-01",
            "date_to": "2026-05-04",
        },
        started_by="coworker",
    )
    jobs.update_job(job_id, status="running")
    with ClippingDB(db_file) as db:
        article_id = db.insert_article(
            url="https://example.com/shakira-salva",
            title="Shakira anuncia show no Rio",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-05-01T12:00:00+00:00",
            snippet="Shakira aparece no Rio.",
            full_text="Shakira aparece no Rio.",
        )
        assert article_id is not None
        db.insert_mention(article_id, "shakira", "shakira", "shakira")
        story_id = db.create_story(
            title="Shakira anuncia show no Rio",
            summary="Resumo sobre Shakira.",
            temperature=34.0,
            target_keys=["shakira"],
        )
        db.attach_article_to_story(story_id, article_id)

    jobs.record_progress(
        job_id,
        "article_saved",
        {
            "article_id": article_id,
            "story_id": story_id,
            "url": "https://example.com/shakira-salva",
            "title": "Shakira anuncia show no Rio",
            "published_at": "2026-05-01T12:00:00+00:00",
            "source_name": "Fonte Teste",
            "source_type": "test",
            "target_keys": ["shakira"],
            "articles_inserted_delta": 1,
            "mentions_inserted_delta": 1,
            "stories_touched_delta": 1,
            "publication_state": "saved",
        },
        target_key="shakira",
        target_label="shakira",
    )

    observed = jobs.get_job(job_id)
    live = jobs.live_results_for_job(job_id)

    assert observed["articles_inserted"] == 1
    assert observed["mentions_inserted"] == 1
    assert observed["stories_touched"] == 1
    assert observed["progress"]["storiesTouched"] == 1
    assert live["count"] == 1
    assert live["items"][0]["title"] == "Shakira anuncia show no Rio"
    assert "shakira" in live["items"][0]["targetKeys"]
    assert live["items"][0]["publicationState"] == "saved"


def test_base_live_results_return_recent_saved_articles_after_export_job(monkeypatch, tmp_path):
    _, jobs, db_file = reload_admin_modules(monkeypatch, tmp_path)
    monkeypatch.setattr(jobs.artifact_store, "enabled", False)
    monkeypatch.setattr(jobs, "target_labels", lambda include_archived=False: {"shakira": "shakira"})
    update_job_id = "shakira-update-for-base"
    jobs.create_job(
        update_job_id,
        "update",
        {
            "preset": "custom",
            "collector": "all",
            "target_keys": ["shakira"],
            "date_from": "2026-04-01",
            "date_to": "2026-05-05",
        },
        started_by="coworker",
    )
    with ClippingDB(db_file) as db:
        article_id = db.insert_article(
            url="https://example.com/shakira-base-atual",
            title="Shakira entra direto na Base atual",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-05-02T12:00:00+00:00",
            snippet="Shakira aparece na Base atual.",
            full_text="Shakira aparece na Base atual.",
        )
        assert article_id is not None
        db.insert_mention(article_id, "shakira", "shakira", "shakira")
        story_id = db.create_story(
            title="Shakira entra direto na Base atual",
            summary="Resumo sobre Shakira.",
            temperature=34.0,
            target_keys=["shakira"],
        )
        db.attach_article_to_story(story_id, article_id)

    jobs.record_progress(
        update_job_id,
        "article_saved",
        {
            "article_id": article_id,
            "story_id": story_id,
            "url": "https://example.com/shakira-base-atual",
            "title": "Shakira entra direto na Base atual",
            "published_at": "2026-05-02T12:00:00+00:00",
            "source_name": "Fonte Teste",
            "source_type": "test",
            "target_keys": ["shakira"],
            "articles_inserted_delta": 1,
            "mentions_inserted_delta": 1,
            "stories_touched_delta": 1,
            "publication_state": "saved",
        },
        target_key="shakira",
        target_label="shakira",
    )
    jobs.create_job(
        "newer-export-job",
        "export",
        {"preset": "export", "collector": "export", "target_keys": [], "date_from": "", "date_to": ""},
        started_by="coworker",
        enforce_single_active=False,
    )

    live = jobs.live_results_for_job(scope="base", target_key="shakira", limit=10)

    assert live["status"] == "base"
    assert live["count"] == 1
    assert live["items"][0]["title"] == "Shakira entra direto na Base atual"
    assert live["items"][0]["targetKeys"] == ["shakira"]


def test_live_results_do_not_resurrect_removed_target_from_stale_event(monkeypatch, tmp_path):
    _, jobs, db_file = reload_admin_modules(monkeypatch, tmp_path)
    monkeypatch.setattr(jobs.artifact_store, "enabled", False)
    monkeypatch.setattr(jobs, "target_labels", lambda include_archived=False: {"shakira": "shakira"})
    job_id = "stale-event-target"
    jobs.create_job(
        job_id,
        "update",
        {
            "preset": "custom",
            "collector": "all",
            "target_keys": ["shakira"],
            "date_from": "2026-04-01",
            "date_to": "2026-05-05",
        },
        started_by="coworker",
    )
    with ClippingDB(db_file) as db:
        article_id = db.insert_article(
            url="https://example.com/not-shakira",
            title="Materia sem alvo depois da limpeza",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-05-02T12:00:00+00:00",
            snippet="Sem alvo ativo.",
            full_text="Sem alvo ativo.",
        )
        assert article_id is not None

    jobs.record_progress(
        job_id,
        "article_saved",
        {
            "article_id": article_id,
            "story_id": 0,
            "url": "https://example.com/not-shakira",
            "title": "Materia sem alvo depois da limpeza",
            "published_at": "2026-05-02T12:00:00+00:00",
            "source_name": "Fonte Teste",
            "source_type": "test",
            "target_keys": ["shakira"],
            "publication_state": "saved",
        },
        target_key="shakira",
        target_label="shakira",
    )

    live = jobs.live_results_for_job(job_id, target_key="shakira")

    assert live["count"] == 0


def test_job_progress_totals_stay_coherent_when_collection_events_age_out(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    job_id = "progress-window"
    jobs.create_job(
        job_id,
        "update",
        {
            "preset": "custom",
            "collector": "all",
            "target_keys": ["bernardo_rubiao"],
            "date_from": "2026-05-01",
            "date_to": "2026-05-01",
        },
        started_by="coworker",
    )
    jobs.record_progress(
        job_id,
        "source_progress",
        {
            "source_name": "RSS",
            "source_type": "rss",
            "candidates_seen": 220,
            "candidates_total": 226,
            "articles_inserted": 0,
            "mentions_inserted": 0,
            "stories_touched": 0,
        },
        target_key="bernardo_rubiao",
        target_label="Bernardo Rubião",
    )

    observed = jobs.get_job(job_id)

    assert observed["progress"]["candidatesSeen"] == 220
    assert observed["progress"]["candidatesTotal"] == 226


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


def test_cancel_active_keeps_process_slot_until_worker_boundary(monkeypatch, tmp_path):
    import threading

    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    jobs.create_job(
        "cancel-running",
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
    manager._active_job_id = "cancel-running"
    manager._cancel_events["cancel-running"] = threading.Event()

    cancelled = manager.cancel_active()

    assert cancelled["status"] == "cancelled"
    assert manager._cancel_events["cancel-running"].is_set()
    assert manager._active_job_id == "cancel-running"


def test_cancel_active_ignores_terminal_job_still_uploading(monkeypatch, tmp_path):
    import threading

    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    jobs.create_job(
        "terminal-uploading",
        "export",
        {
            "preset": "export",
            "collector": "export",
            "target_keys": [],
            "date_from": "",
            "date_to": "",
        },
        started_by="coworker",
    )
    jobs.update_job("terminal-uploading", status="succeeded")
    manager = jobs.JobManager(SimpleNamespace(writes_available=True))
    manager._active_job_id = "terminal-uploading"
    manager._cancel_events["terminal-uploading"] = threading.Event()

    try:
        manager.cancel_active()
    except jobs.JobConflict as exc:
        assert str(exc) == "no_active_job"
    else:
        raise AssertionError("expected no_active_job")

    assert jobs.get_job("terminal-uploading")["status"] == "succeeded"
    assert not manager._cancel_events["terminal-uploading"].is_set()


def test_startup_marks_orphaned_active_jobs_interrupted_not_cancelled(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    jobs.create_job(
        "orphaned-running",
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
    jobs.update_job("orphaned-running", status="running")

    interrupted = jobs.mark_orphaned_active_jobs_interrupted()

    assert interrupted == 1
    assert jobs.get_active_job() is None
    job = jobs.get_job("orphaned-running")
    assert job["status"] == "interrupted"
    assert "reinício do servidor" in job["error_message"]
    assert any(
        event["event"] == "job_interrupted"
        and event["payload"].get("reason") == "startup_recovered_active_job"
        for event in job["events"]
    )


def test_job_runner_passes_cancel_check_into_ingestion(monkeypatch, tmp_path):
    import threading

    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    spec = {
        "preset": "custom",
        "collector": "all",
        "target_keys": ["flavio_valle"],
        "date_from": "2026-04-01",
        "date_to": "2026-04-30",
        "export": False,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
    }
    jobs.create_job("runner-cancel-check", "update", spec, started_by="coworker")
    seen_cancel_checks = []

    def fake_run_ingestion(_collector, *, options, progress_callback):
        seen_cancel_checks.append(options.cancel_check)
        progress_callback(
            "source_progress",
            {
                "source_name": "RSS",
                "source_type": "rss",
                "candidates_seen": 1,
                "articles_inserted": 0,
                "mentions_inserted": 0,
                "stories_touched": 0,
            },
        )
        return []

    monkeypatch.setattr(jobs, "run_ingestion", fake_run_ingestion)
    upload_statuses = []

    def fake_upload_current_artifacts(**_kwargs):
        upload_statuses.append(jobs.get_job("runner-cancel-check")["status"])
        return []

    store = SimpleNamespace(
        writes_available=True,
        backup_current_artifacts=lambda _job_id: None,
        upload_current_artifacts=fake_upload_current_artifacts,
    )
    manager = jobs.JobManager(store)
    manager._active_job_id = "runner-cancel-check"
    cancel_event = threading.Event()
    manager._cancel_events["runner-cancel-check"] = cancel_event

    manager._run("runner-cancel-check", "update", spec, cancel_event)

    assert seen_cancel_checks
    assert seen_cancel_checks[0]() is False
    assert upload_statuses == ["succeeded"]
    assert jobs.get_job("runner-cancel-check")["status"] == "succeeded"


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


def test_export_job_cleans_secondary_false_matches_before_snapshot(monkeypatch, tmp_path):
    import threading

    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    spec = {
        "preset": "export",
        "collector": "export",
        "target_keys": [],
        "date_from": "",
        "date_to": "",
        "export": True,
    }
    jobs.create_job("export-cleanup", "export", spec, started_by="coworker")
    cleanup_calls = []
    export_calls = []
    upload_manifests = []

    monkeypatch.setattr(jobs, "active_secondary_target_keys", lambda: ["shakira"])

    def fake_cleanup(_db_path, target_keys):
        cleanup_calls.append(list(target_keys))
        return {"removedMentions": 2, "storiesTouched": 2}

    monkeypatch.setattr(jobs, "cleanup_false_backfilled_target_mentions", fake_cleanup)
    monkeypatch.setattr(jobs, "run_export_snapshot", lambda job_id: export_calls.append(job_id))

    store = SimpleNamespace(
        writes_available=True,
        backup_current_artifacts=lambda _job_id: None,
        upload_current_artifacts=lambda **kwargs: upload_manifests.append(kwargs) or [],
    )
    manager = jobs.JobManager(store)
    manager._active_job_id = "export-cleanup"
    cancel_event = threading.Event()
    manager._cancel_events["export-cleanup"] = cancel_event

    manager._run("export-cleanup", "export", spec, cancel_event)

    assert cleanup_calls == [["shakira"]]
    assert export_calls == ["export-cleanup"]
    assert upload_manifests
    job = jobs.get_job("export-cleanup")
    assert job["status"] == "succeeded"
    assert any(
        event["event"] == "target_backfill_cleanup" and event["payload"]["count"] == 2
        for event in job["events"]
    )


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


def test_process_candidates_tags_duplicate_article_for_new_secondary_target(monkeypatch, tmp_path):
    from pipeline import ingest
    from pipeline.matcher import Target

    db_file = tmp_path / "duplicate-target.db"
    with ClippingDB(db_file) as db:
        article_id = db.insert_article(
            url="https://example.com/noticia-compartilhada",
            title="Materia ja salva sobre agenda cultural",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-04-30T12:00:00+00:00",
            snippet="Materia original.",
            full_text="Materia original.",
        )
        assert article_id is not None
        db.insert_mention(article_id, "flavio_valle", "Flavio Valle", "Flavio Valle")
        story_id = db.create_story(
            title="Materia ja salva sobre agenda cultural",
            summary="Resumo original.",
            temperature=34.0,
            target_keys=["flavio_valle"],
        )
        db.attach_article_to_story(story_id, article_id)

    monkeypatch.setattr(
        ingest,
        "get_active_targets",
        lambda: [Target(key="shakira", display_name="shakira", keywords=["shakira"])],
    )
    candidate = ingest.CandidateArticle(
        title="Shakira anuncia agenda cultural no Rio",
        url="https://example.com/noticia-compartilhada",
        source_name="Google News",
        source_type="google_news",
        published_at="2026-04-30T12:00:00+00:00",
        snippet="Shakira aparece na programacao cultural.",
        metadata={},
    )

    result = ingest.process_candidates(
        "Google News",
        "google_news",
        [candidate],
        options=ingest.IngestionOptions(
            target_keys=["shakira"],
            date_from="2026-04-30",
            date_to="2026-04-30",
            db_path=str(db_file),
        ),
    )

    assert result.articles_inserted == 0
    assert result.mentions_inserted == 1
    assert result.stories_touched == 1
    with sqlite3.connect(db_file) as conn:
        mention_targets = {
            row[0]
            for row in conn.execute(
                "SELECT target_key FROM mentions WHERE article_id = ?",
                (article_id,),
            ).fetchall()
        }
        story_targets = {
            row[0]
            for row in conn.execute(
                "SELECT target_key FROM story_targets WHERE story_id = ?",
                (story_id,),
            ).fetchall()
        }
    assert mention_targets == {"flavio_valle", "shakira"}
    assert story_targets == {"flavio_valle", "shakira"}


def test_backfill_missing_target_mentions_retags_existing_secondary_story(monkeypatch, tmp_path):
    db_admin, _, db_file = reload_admin_modules(monkeypatch, tmp_path)
    from pipeline import settings

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
                },
                {
                    "key": "shakira",
                    "label": "shakira",
                    "display_name": "shakira",
                    "primary": False,
                    "keywords": ["shakira"],
                    "exact_aliases": [],
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)
    monkeypatch.setattr(settings, "TARGETS_JSON_PATH", targets_path)
    with ClippingDB(db_file) as db:
        article_id = db.insert_article(
            url="https://example.com/show-shakira",
            title="Show de Shakira movimenta turismo no Rio",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-04-30T12:00:00+00:00",
            snippet="Segundo Flavio Valle, Shakira deve atrair visitantes.",
            full_text="Segundo Flavio Valle, a apresentacao de Shakira deve atrair visitantes.",
        )
        assert article_id is not None
        db.insert_mention(article_id, "flavio_valle", "Flavio Valle", "Flavio Valle")
        story_id = db.create_story(
            title="Show de Shakira movimenta turismo no Rio",
            summary="Resumo original.",
            temperature=34.0,
            target_keys=["flavio_valle"],
        )
        db.attach_article_to_story(story_id, article_id)

    result = db_admin.backfill_missing_target_mentions(db_file, ["shakira"])

    assert result["mentionsInserted"] == 1
    assert result["storiesTouched"] == 1
    with sqlite3.connect(db_file) as conn:
        mention_targets = {
            row[0]
            for row in conn.execute(
                "SELECT target_key FROM mentions WHERE article_id = ?",
                (article_id,),
            ).fetchall()
        }
        story_targets = {
            row[0]
            for row in conn.execute(
                "SELECT target_key FROM story_targets WHERE story_id = ?",
                (story_id,),
            ).fetchall()
        }
    assert mention_targets == {"flavio_valle", "shakira"}
    assert story_targets == {"flavio_valle", "shakira"}


def test_backfill_ignores_full_text_noise_and_cleanup_removes_false_match(monkeypatch, tmp_path):
    db_admin, _, db_file = reload_admin_modules(monkeypatch, tmp_path)
    from pipeline import settings

    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "flavio_valle", "label": "Flavio Valle", "keywords": ["Flavio Valle"], "primary": True},
                {"key": "shakira", "label": "shakira", "keywords": ["shakira"], "primary": False},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)
    monkeypatch.setattr(settings, "TARGETS_JSON_PATH", targets_path)
    with ClippingDB(db_file) as db:
        article_id = db.insert_article(
            url="https://example.com/flavio-com-widget",
            title="Ciclovias em pauta no Rio",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-04-30T12:00:00+00:00",
            snippet=(
                "Flavio Valle fala sobre ciclovias. "
                "<h3>Notícias relacionadas:</h3><ul><li>Shakira no Rio.</li></ul>"
            ),
            full_text="Flavio Valle fala sobre ciclovias. Links relacionados: Shakira no Rio.",
        )
        assert article_id is not None
        db.insert_mention(article_id, "flavio_valle", "Flavio Valle", "Flavio Valle")
        story_id = db.create_story(
            title="Ciclovias em pauta no Rio",
            summary="Resumo sem a cantora.",
            temperature=34.0,
            target_keys=["flavio_valle"],
        )
        db.attach_article_to_story(story_id, article_id)
        db.insert_mentions(
            article_id,
            [
                {
                    "target_key": "shakira",
                    "target_name": "shakira",
                    "keyword_matched": "shakira",
                    "sentiment": "neutral",
                    "sentiment_reason": "",
                    "context": "",
                }
            ],
        )
        db.ensure_story_target(story_id, "shakira")

    backfill = db_admin.backfill_missing_target_mentions(db_file, ["shakira"])
    cleanup = db_admin.cleanup_false_backfilled_target_mentions(db_file, ["shakira"])

    assert backfill["mentionsInserted"] == 0
    assert cleanup["removedMentions"] == 1
    with sqlite3.connect(db_file) as conn:
        mention_targets = {
            row[0]
            for row in conn.execute(
                "SELECT target_key FROM mentions WHERE article_id = ?",
                (article_id,),
            ).fetchall()
        }
        story_targets = {
            row[0]
            for row in conn.execute(
                "SELECT target_key FROM story_targets WHERE story_id = ?",
                (story_id,),
            ).fetchall()
        }
    assert mention_targets == {"flavio_valle"}
    assert story_targets == {"flavio_valle"}


def test_process_candidates_skips_secondary_target_only_in_page_boilerplate(monkeypatch, tmp_path):
    from pipeline import ingest
    from pipeline.matcher import Target

    db_file = tmp_path / "secondary-boilerplate.db"
    events = []

    def fake_fetch_full_article_text(*_args, **_kwargs):
        full_text = (
            "A materia principal descreve a investigacao policial no Rio de Janeiro. "
            "Autoridades informaram novas etapas do processo nesta semana. "
            "O texto acompanha a apuracao local com detalhes oficiais. "
            "Links relacionados: Shakira faz show no Rio."
        )
        return (
            "https://example.com/policia-rio",
            "<html></html>",
            full_text,
            "Corregedoria investiga agentes no Rio",
            "2026-04-30T12:00:00+00:00",
        )

    monkeypatch.setattr(ingest, "fetch_full_article_text", fake_fetch_full_article_text)
    monkeypatch.setattr(
        ingest,
        "get_active_targets",
        lambda: [Target(key="shakira", display_name="shakira", keywords=["shakira"], primary=False)],
    )
    candidate = ingest.CandidateArticle(
        title="Corregedoria investiga agentes no Rio",
        url="https://example.com/policia-rio",
        source_name="Fonte Teste",
        source_type="rss",
        published_at="2026-04-30T12:00:00+00:00",
        snippet="A investigacao policial foi aberta nesta semana.",
        metadata={},
    )

    result = ingest.process_candidates(
        "Fonte Teste",
        "rss",
        [candidate],
        options=ingest.IngestionOptions(
            target_keys=["shakira"],
            date_from="2026-04-30",
            date_to="2026-04-30",
            db_path=str(db_file),
        ),
        progress_callback=lambda event, payload: events.append((event, payload)),
    )

    assert result.candidates_seen == 1
    assert result.articles_inserted == 0
    assert result.mentions_inserted == 0
    assert result.stories_touched == 0
    assert any(
        event == "candidate_evaluated" and payload.get("reason") == "target_only_in_page_boilerplate"
        for event, payload in events
    )
    with sqlite3.connect(db_file) as conn:
        assert conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0] == 0


def test_process_candidates_skips_secondary_target_only_in_related_snippet(monkeypatch, tmp_path):
    from pipeline import ingest
    from pipeline.matcher import Target

    db_file = tmp_path / "secondary-related-snippet.db"
    events = []

    def unexpected_fetch(*_args, **_kwargs):
        raise AssertionError("related-snippet preview match should not need article fetch")

    monkeypatch.setattr(ingest, "fetch_full_article_text", unexpected_fetch)
    monkeypatch.setattr(
        ingest,
        "get_active_targets",
        lambda: [Target(key="shakira", display_name="shakira", keywords=["shakira"], primary=False)],
    )
    candidate = ingest.CandidateArticle(
        title="Avião bimotor cai e bate em prédio em Belo Horizonte",
        url="https://example.com/aviao-bimotor",
        source_name="Agencia Brasil",
        source_type="rss",
        published_at="2026-05-04T19:32:00+00:00",
        snippet=(
            "Um avião bimotor atingiu um prédio em Belo Horizonte. "
            "<h3>Notícias relacionadas:</h3><ul><li>Mesmo com multidão, show de Shakira "
            "não registra ocorrências graves.</li></ul>"
        ),
        metadata={},
    )

    result = ingest.process_candidates(
        "Agencia Brasil",
        "rss",
        [candidate],
        options=ingest.IngestionOptions(
            target_keys=["shakira"],
            date_from="2026-05-04",
            date_to="2026-05-04",
            db_path=str(db_file),
        ),
        progress_callback=lambda event, payload: events.append((event, payload)),
    )

    assert result.candidates_seen == 1
    assert result.articles_inserted == 0
    assert result.mentions_inserted == 0
    assert result.stories_touched == 0
    assert any(
        event == "candidate_evaluated" and payload.get("reason") == "target_only_in_page_boilerplate"
        for event, payload in events
    )
    with sqlite3.connect(db_file) as conn:
        assert conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0] == 0


def test_process_candidates_reports_candidate_progress_before_fetch_fail(monkeypatch, tmp_path):
    from pipeline import ingest

    events = []

    def fake_fetch_full_article_text(*_args, **_kwargs):
        raise TimeoutError("slow article")

    monkeypatch.setattr(ingest, "fetch_full_article_text", fake_fetch_full_article_text)
    candidate = ingest.CandidateArticle(
        title="Materia sem alvo no resumo",
        url="https://example.com/sem-alvo",
        source_name="RSS",
        source_type="rss",
        published_at="2026-04-30T12:00:00+00:00",
        snippet="",
        metadata={},
    )

    result = ingest.process_candidates(
        "RSS",
        "rss",
        [candidate],
        options=ingest.IngestionOptions(
            target_keys=["flavio_valle"],
            date_from="2026-04-30",
            date_to="2026-04-30",
            db_path=str(tmp_path / "progress-before-fetch.db"),
        ),
        progress_callback=lambda event, payload: events.append((event, payload)),
    )

    progress_events = [payload for event, payload in events if event == "source_progress"]
    assert result.candidates_seen == 1
    assert any(error.startswith("fetch_fail:") for error in result.errors)
    assert progress_events[0]["candidates_seen"] == 1
    assert progress_events[0]["status"] == "processing"
    assert progress_events[-1]["status"] == "fetch_failed"


def test_process_candidates_stops_at_candidate_boundary_when_cancelled(monkeypatch, tmp_path):
    from pipeline import ingest

    cancel = {"requested": False}
    events = []

    def fake_fetch_full_article_text(*_args, **_kwargs):
        cancel["requested"] = True
        raise TimeoutError("slow article")

    monkeypatch.setattr(ingest, "fetch_full_article_text", fake_fetch_full_article_text)
    candidates = [
        ingest.CandidateArticle(
            title=f"Materia {idx}",
            url=f"https://example.com/materia-{idx}",
            source_name="RSS",
            source_type="rss",
            published_at="2026-04-30T12:00:00+00:00",
            snippet="",
            metadata={},
        )
        for idx in range(2)
    ]

    result = ingest.process_candidates(
        "RSS",
        "rss",
        candidates,
        options=ingest.IngestionOptions(
            target_keys=["flavio_valle"],
            date_from="2026-04-30",
            date_to="2026-04-30",
            db_path=str(tmp_path / "cancel-boundary.db"),
            cancel_check=lambda: cancel["requested"],
        ),
        progress_callback=lambda event, payload: events.append((event, payload)),
    )

    assert result.candidates_seen == 1
    assert "cancelled" in result.errors
    assert any(
        event == "source_progress" and payload.get("status") == "cancelled"
        for event, payload in events
    )
    assert any(
        event == "source_complete" and payload.get("status") == "cancelled"
        for event, payload in events
    )


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
