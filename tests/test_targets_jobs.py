from __future__ import annotations

import importlib
import json
import sqlite3
import sys
import threading
import time
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


def test_connect_falls_back_when_wal_mode_hits_disk_io(monkeypatch, tmp_path):
    db_admin, _, db_file = reload_admin_modules(monkeypatch, tmp_path)
    calls: list[str] = []

    class FakeConnection:
        row_factory = None
        closed = False

        def execute(self, sql, params=()):
            calls.append(sql)
            if sql == "PRAGMA journal_mode = WAL":
                raise sqlite3.OperationalError("disk I/O error")
            return SimpleNamespace(fetchone=lambda: ("delete",))

        def close(self):
            self.closed = True

    fake = FakeConnection()
    monkeypatch.setattr(db_admin.sqlite3, "connect", lambda path: fake)

    conn = db_admin.connect(db_file)

    assert conn is fake
    assert "PRAGMA busy_timeout = 5000" in calls
    assert "PRAGMA journal_mode = WAL" in calls
    assert "PRAGMA journal_mode = DELETE" in calls
    assert fake.closed is False


def test_effective_candidate_workers_clamps_to_safe_default(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)

    assert jobs.effective_candidate_workers({"candidate_workers": 4}) == 1

    monkeypatch.setenv("CLIPPING_MAX_CANDIDATE_WORKERS", "2")
    assert jobs.effective_candidate_workers({"candidate_workers": 4}) == 2
    assert jobs.effective_candidate_workers({"candidate_workers": 1}) == 1


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
                    "primary": False,
                    "className": "",
                    "keywords": ["Ana Maria"],
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    created = db_admin.create_secondary_target(
        {
            "display_name": "Marina Costa",
            "keywords": ["Marina Costa", "  ", "Secretaria Marina Costa"],
            "aliases": ["M. Costa", "M. Costa"],
            "primary": True,
            "className": "primary",
        }
    )

    assert created == {
        "key": "marina_costa",
        "label": "Marina Costa",
        "display_name": "Marina Costa",
        "className": "",
        "primary": False,
        "archived": False,
        "keywords": ["Marina Costa", "Secretaria Marina Costa"],
        "exact_aliases": ["M. Costa"],
    }
    stored = json.loads(targets_path.read_text(encoding="utf-8"))
    assert stored[-1]["key"] == "marina_costa"
    assert stored[-1]["primary"] is False
    assert stored[-1]["className"] == ""

    public = db_admin.public_targets()
    assert public["primaryKeys"] == ["flavio_valle", "pedro_angelito"]
    by_key = {row["key"]: row for row in public["targets"]}
    assert by_key["flavio_valle"]["primary"] is True
    assert by_key["ana_maria"]["primary"] is False
    assert by_key["marina_costa"]["primary"] is False


def test_create_secondary_target_rejects_duplicate_display_name(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {
                    "key": "shakira",
                    "label": "Shakira",
                    "display_name": "Shakira",
                    "primary": False,
                    "keywords": ["Shakira"],
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    for payload in (
        {"display_name": "Shakira"},
        {"display_name": "shakira"},
        {"display_name": "  Shakira  "},
        {"display_name": "SHAKIRA"},
    ):
        try:
            db_admin.create_secondary_target(payload)
        except db_admin.ValidationError as exc:
            assert "Já existe um nome cadastrado" in str(exc)
            assert "Shakira" in str(exc)
        else:
            raise AssertionError(f"duplicate display_name {payload!r} should have been rejected")

    stored = json.loads(targets_path.read_text(encoding="utf-8"))
    assert len(stored) == 1, "no extra row should have been written"
    assert stored[0]["key"] == "shakira"


def test_create_primary_target_writes_primary_row_and_appears_in_primary_keys(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "flavio_valle", "label": "Flavio Valle", "primary": True, "keywords": ["Flavio Valle"]},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    created = db_admin.create_primary_target({"display_name": "Maria Silva", "keywords": ["Maria S.", "M. Silva"]})

    assert created["key"] == "maria_silva"
    assert created["primary"] is True
    assert created["className"] == "primary"
    assert created["keywords"] == ["Maria Silva", "Maria S.", "M. Silva"]

    public = db_admin.public_targets()
    assert "maria_silva" in public["primaryKeys"]
    assert "flavio_valle" in public["primaryKeys"]
    by_key = {row["key"]: row for row in public["targets"]}
    assert by_key["maria_silva"]["primary"] is True


def test_promote_secondary_target_to_primary_sets_flags(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "shakira", "label": "Shakira", "primary": False, "keywords": ["Shakira"]},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    promoted = db_admin.promote_target_to_primary("shakira")
    assert promoted["primary"] is True
    assert promoted["className"] == "primary"
    stored = {row["key"]: row for row in json.loads(targets_path.read_text(encoding="utf-8"))}
    assert stored["shakira"]["primary"] is True
    assert stored["shakira"]["className"] == "primary"
    assert "shakira" in db_admin.public_targets()["primaryKeys"]


def test_promote_already_primary_target_raises(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "flavio_valle", "label": "Flavio Valle", "primary": True, "keywords": ["Flavio Valle"]},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    try:
        db_admin.promote_target_to_primary("flavio_valle")
    except db_admin.ValidationError as exc:
        assert "ja e principal" in str(exc)
    else:
        raise AssertionError("promoting already-primary target should fail")


def test_demote_primary_target_clears_flags(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "maria_silva", "label": "Maria Silva", "primary": True, "className": "primary", "keywords": ["Maria Silva"]},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    demoted = db_admin.demote_target_to_secondary("maria_silva")
    assert demoted["primary"] is False
    assert demoted["className"] == ""
    stored = {row["key"]: row for row in json.loads(targets_path.read_text(encoding="utf-8"))}
    assert stored["maria_silva"]["primary"] is False
    assert stored["maria_silva"]["className"] == ""
    public = db_admin.public_targets()
    assert "maria_silva" not in public["primaryKeys"]


def test_demote_protected_primary_target_is_blocked(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "flavio_valle", "label": "Flavio Valle", "primary": True, "keywords": ["Flavio Valle"]},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    try:
        db_admin.demote_target_to_secondary("flavio_valle")
    except db_admin.ValidationError as exc:
        assert "principais" in str(exc)
    else:
        raise AssertionError("protected primary target must not be demotable")

    # File state unchanged.
    public = db_admin.public_targets()
    assert "flavio_valle" in public["primaryKeys"]


def test_demote_already_secondary_target_raises(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "shakira", "label": "Shakira", "primary": False, "keywords": ["Shakira"]},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    try:
        db_admin.demote_target_to_secondary("shakira")
    except db_admin.ValidationError as exc:
        assert "ja e secundario" in str(exc)
    else:
        raise AssertionError("demoting already-secondary target should fail")


def test_create_primary_target_rejects_duplicate_display_name_against_secondary(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "shakira", "label": "Shakira", "primary": False, "keywords": ["Shakira"]},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    try:
        db_admin.create_primary_target({"display_name": "Shakira"})
    except db_admin.ValidationError as exc:
        assert "Já existe um nome cadastrado" in str(exc)
    else:
        raise AssertionError("primary creation should be rejected when display_name collides with active secondary")

    stored = json.loads(targets_path.read_text(encoding="utf-8"))
    assert len(stored) == 1


def test_update_secondary_target_rejects_renaming_to_existing_display_name(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "shakira", "label": "Shakira", "display_name": "Shakira", "keywords": ["Shakira"]},
                {"key": "vorcaro", "label": "Vorcaro", "display_name": "Vorcaro", "keywords": ["Vorcaro"]},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    try:
        db_admin.update_secondary_target("vorcaro", {"display_name": "Shakira"})
    except db_admin.ValidationError as exc:
        assert "Já existe um nome cadastrado" in str(exc)
        assert "Shakira" in str(exc)
    else:
        raise AssertionError("rename to existing display_name should be rejected")

    stored = json.loads(targets_path.read_text(encoding="utf-8"))
    by_key = {row["key"]: row for row in stored}
    assert by_key["vorcaro"]["display_name"] == "Vorcaro", "original row must not have been mutated"


def test_update_secondary_target_allows_rename_to_own_current_name(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "shakira", "label": "Shakira", "display_name": "Shakira", "keywords": ["Shakira"]},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    updated = db_admin.update_secondary_target("shakira", {"display_name": "Shakira", "keywords": ["Shakira", "Shak"]})
    assert updated["display_name"] == "Shakira"
    assert "Shak" in updated["keywords"]


def test_create_secondary_target_allows_duplicate_against_archived_row(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {
                    "key": "shakira",
                    "label": "Shakira",
                    "display_name": "Shakira",
                    "primary": False,
                    "archived": True,
                    "keywords": ["Shakira"],
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    created = db_admin.create_secondary_target({"display_name": "Shakira"})
    assert created["display_name"] == "Shakira"
    assert created["archived"] is False
    assert created["key"] != "shakira"


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


def test_restore_secondary_target_rejects_conflict_with_active_homonym(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "flavio_valle", "label": "Flavio Valle", "keywords": ["Flavio Valle"]},
                {
                    "key": "shakira",
                    "label": "Shakira",
                    "display_name": "Shakira",
                    "archived": True,
                    "archived_at": "2026-05-19T17:00:00+00:00",
                    "keywords": ["Shakira"],
                },
                {
                    "key": "shakira_2",
                    "label": "Shakira",
                    "display_name": "Shakira",
                    "archived": False,
                    "keywords": ["Shakira"],
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    try:
        db_admin.restore_secondary_target("shakira")
    except db_admin.ValidationError as exc:
        assert "Já existe um nome ativo" in str(exc)
    else:
        raise AssertionError("Expected ValidationError when restoring would create a homonym pair.")

    rows = {row["key"]: row for row in json.loads(targets_path.read_text(encoding="utf-8"))}
    assert rows["shakira"]["archived"] is True, "archived target must stay archived when restore is blocked"


def test_restore_secondary_target_allows_when_no_active_homonym(monkeypatch, tmp_path):
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "flavio_valle", "label": "Flavio Valle", "keywords": ["Flavio Valle"]},
                {
                    "key": "shakira",
                    "label": "Shakira",
                    "display_name": "Shakira",
                    "archived": True,
                    "archived_at": "2026-05-19T17:00:00+00:00",
                    "keywords": ["Shakira"],
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    restored = db_admin.restore_secondary_target("shakira")
    assert restored["archived"] is False
    assert restored["key"] == "shakira"


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


def test_normalize_targets_forces_protected_keys_primary_and_honors_promoted_flag(monkeypatch, tmp_path):
    """
    Contract:
    - PROTECTED_PRIMARY_KEYS (flavio_valle, pedro_angelito) are always primary,
      even if the file says otherwise.
    - Other rows honor their primary flag from the file (allows admin-promoted
      primaries via API).
    """
    db_admin, _, _ = reload_admin_modules(monkeypatch, tmp_path)
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "flavio_valle", "label": "Flavio Valle", "primary": False, "keywords": ["Flavio Valle"]},
                {"key": "pedro_angelito", "label": "Pedro Angelito", "primary": False, "keywords": ["Pedro Angelito"]},
                {"key": "bernardo_rubiao", "label": "Bernardo Rubiao", "primary": True, "className": "primary", "keywords": ["Bernardo Rubiao"]},
                {"key": "ana_maria", "label": "Ana Maria", "primary": False, "className": "", "keywords": ["Ana Maria"]},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    changed = db_admin.normalize_targets_file()

    assert changed is True
    public = db_admin.public_targets()
    assert set(public["primaryKeys"]) == {"flavio_valle", "pedro_angelito", "bernardo_rubiao"}
    by_key = {row["key"]: row for row in public["targets"]}
    # Protected keys are forced primary even if file said False.
    assert by_key["flavio_valle"]["primary"] is True
    assert by_key["pedro_angelito"]["primary"] is True
    # Promoted-via-file key honors the flag.
    assert by_key["bernardo_rubiao"]["primary"] is True
    # Non-primary file flag stays non-primary.
    assert by_key["ana_maria"]["primary"] is False
    stored = {row["key"]: row for row in json.loads(targets_path.read_text(encoding="utf-8"))}
    assert stored["flavio_valle"]["className"] == "primary"
    assert stored["pedro_angelito"]["className"] == "primary"
    assert stored["bernardo_rubiao"]["className"] == "primary"
    assert stored["ana_maria"]["className"] == ""


def test_build_update_spec_accepts_safe_custom_collector_and_long_dates(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)

    spec = jobs.build_update_spec(
        {
            "preset": "custom",
            "target_keys": ["flavio_valle"],
            "date_from": "2026-04-01",
            "date_to": "2026-04-30",
            "collector": "google_news",
            "export": False,
        }
    )

    assert spec["collector"] == "google_news"
    assert spec["skip_direct_scrape"] is True
    assert "direct_scrape" not in jobs.SAFE_COLLECTORS
    assert spec["date_from"] == "2026-04-01"
    assert spec["date_to"] == "2026-04-30"
    assert spec["max_candidates"] == 90000
    assert spec["max_process_seconds"] == 90000
    assert spec["candidate_workers"] == 4

    try:
        jobs.build_update_spec(
            {
                "preset": "custom",
                "target_keys": ["flavio_valle"],
                "date_from": "2026-04-01",
                "date_to": "2026-04-30",
                "collector": "direct_scrape",
            }
        )
    except ValueError as exc:
        assert str(exc) == "coletor_invalido"
    else:
        raise AssertionError("expected coletor_invalido")

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


def test_update_spec_freezes_target_snapshot_for_active_job(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    from pipeline.matcher import Target

    original = Target(
        key="ana_teste",
        label="Ana Teste",
        display_name="Ana Teste",
        keywords=["Ana Teste"],
        exact_aliases=["A. Teste"],
        primary=False,
    )
    renamed = Target(
        key="ana_teste",
        label="Ana Renomeada",
        display_name="Ana Renomeada",
        keywords=["Ana Renomeada"],
        exact_aliases=[],
        primary=False,
    )
    monkeypatch.setattr(jobs, "get_active_targets", lambda: [original])
    monkeypatch.setattr(jobs, "validate_target_keys", lambda values: list(values))

    spec = jobs.build_update_spec(
        {
            "preset": "custom",
            "target_keys": ["ana_teste"],
            "date_from": "2026-05-01",
            "date_to": "2026-05-17",
            "collector": "google_news",
            "export": False,
        }
    )

    assert spec["target_snapshots"][0]["display_name"] == "Ana Teste"
    monkeypatch.setattr(jobs, "get_active_targets", lambda: [renamed])
    units = jobs.build_source_units(spec, "ana_teste")

    assert units
    assert any("Ana Teste" in unit.cursor["query"] for unit in units)
    assert all("Ana Renomeada" not in unit.cursor["query"] for unit in units)


def test_completo_preset_uses_current_primary_circle_without_bernardo(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)

    spec = jobs.build_update_spec({"preset": "completo", "export": True})

    assert spec["target_keys"] == ["flavio_valle", "pedro_angelito"]
    assert "bernardo_rubiao" not in spec["target_keys"]
    assert spec["max_candidates"] == 90000
    assert spec["max_process_seconds"] == 90000
    assert spec["candidate_workers"] == 4


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


def test_update_without_export_keeps_base_live_result_saved(monkeypatch, tmp_path):
    _, jobs, db_file = reload_admin_modules(monkeypatch, tmp_path)
    monkeypatch.setattr(jobs.artifact_store, "enabled", False)
    monkeypatch.setattr(jobs, "target_labels", lambda include_archived=False: {"shakira": "shakira"})
    job_id = "shakira-update-no-export"
    jobs.create_job(
        job_id,
        "update",
        {
            "preset": "custom",
            "collector": "all",
            "target_keys": ["shakira"],
            "date_from": "2026-04-01",
            "date_to": "2026-05-05",
            "export": False,
        },
        started_by="coworker",
    )
    with ClippingDB(db_file) as db:
        article_id = db.insert_article(
            url="https://example.com/shakira-saved-no-export",
            title="Shakira salva sem exportar painel",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-05-02T12:00:00+00:00",
            snippet="Shakira aparece antes do export.",
            full_text="Shakira aparece antes do export.",
        )
        assert article_id is not None
        db.insert_mention(article_id, "shakira", "shakira", "shakira")
        story_id = db.create_story(
            title="Shakira salva sem exportar painel",
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
            "url": "https://example.com/shakira-saved-no-export",
            "title": "Shakira salva sem exportar painel",
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
    jobs.update_job(
        job_id,
        status="succeeded",
        finished_at="2026-05-18T22:10:00+00:00",
        articles_inserted=1,
        mentions_inserted=1,
        stories_touched=1,
    )

    live = jobs.live_results_for_job(scope="base", target_key="shakira", limit=10)

    assert live["count"] == 1
    assert live["items"][0]["title"] == "Shakira salva sem exportar painel"
    assert live["items"][0]["publicationState"] == "saved"


def test_target_sync_backfills_new_target_into_base_live_results(monkeypatch, tmp_path):
    db_admin, jobs, db_file = reload_admin_modules(monkeypatch, tmp_path)
    from pipeline import settings

    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {
                    "key": "shakira",
                    "label": "Shakira",
                    "display_name": "Shakira",
                    "primary": False,
                    "keywords": ["Shakira"],
                    "exact_aliases": [],
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)
    monkeypatch.setattr(settings, "TARGETS_JSON_PATH", targets_path)
    monkeypatch.setattr(jobs.artifact_store, "enabled", False)
    with ClippingDB(db_file) as db:
        article_id = db.insert_article(
            url="https://example.com/shakira-target-sync",
            title="Shakira entra na base depois do nome criado",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-05-17T12:00:00+00:00",
            snippet="Shakira aparece na noticia ja salva.",
            full_text="Shakira aparece na noticia ja salva.",
        )
        assert article_id is not None

    result = jobs.record_target_sync("shakira", reason="target-created")
    live = jobs.live_results_for_job(scope="base", target_key="shakira", limit=10)

    assert result["updatedCount"] == 1
    assert result["mentionsInserted"] == 1
    assert result["storiesTouched"] == 1
    assert live["status"] == "base"
    assert live["count"] == 1
    assert live["items"][0]["title"] == "Shakira entra na base depois do nome criado"
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


def test_durable_jobs_become_resumable_on_startup_restart(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    spec = {
        "preset": "custom",
        "collector": "rss",
        "target_keys": ["shakira"],
        "date_from": "2026-04-01",
        "date_to": "2026-05-05",
        "export": True,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
        "durable": True,
    }
    monkeypatch.setattr(jobs, "RSS_FEEDS", [{"source_name": "Fonte RSS", "url": "https://example.com/rss.xml"}])
    jobs.create_job("durable-orphan", "update", spec, started_by="coworker")
    jobs.ensure_source_runs("durable-orphan", spec, "shakira")
    jobs.update_job("durable-orphan", status="running")

    interrupted = jobs.mark_orphaned_active_jobs_interrupted()

    assert interrupted == 1
    job = jobs.get_job("durable-orphan")
    assert job["status"] == "interrupted_resumable"
    assert job["resumeAvailable"] is True
    assert job["coverageState"] == "interrupted_resumable"
    assert job["sourceRuns"][0]["status"] == "interrupted_resumable"
    assert "retomada" in job["error_message"]


def test_reset_resumable_source_runs_requeues_failed_and_interrupted_rows(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    spec = {
        "preset": "custom",
        "collector": "rss",
        "target_keys": ["shakira"],
        "date_from": "2026-04-01",
        "date_to": "2026-05-05",
        "export": True,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
        "durable": True,
    }
    monkeypatch.setattr(jobs, "RSS_FEEDS", [{"source_name": "Fonte RSS", "url": "https://example.com/rss.xml"}])
    jobs.create_job("resume-rows", "update", spec, started_by="coworker")
    jobs.ensure_source_runs("resume-rows", spec, "shakira")
    row = jobs.source_run_rows("resume-rows")[0]
    jobs.update_source_run(row["id"], status="failed_needs_fix", cursor={}, last_error="parser_error", finished=True)

    jobs.reset_resumable_source_runs("resume-rows")

    row = jobs.source_run_rows("resume-rows")[0]
    assert row["status"] == "pending"
    assert row["finished_at"] is None


def test_source_observability_reports_counts_and_incremental_publish_time(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    spec = {
        "preset": "custom",
        "collector": "rss",
        "target_keys": ["shakira"],
        "date_from": "2026-04-01",
        "date_to": "2026-05-05",
        "export": True,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
        "durable": True,
    }
    monkeypatch.setattr(
        jobs,
        "RSS_FEEDS",
        [
            {"source_name": "Fonte RSS 1", "url": "https://example.com/1.xml"},
            {"source_name": "Fonte RSS 2", "url": "https://example.com/2.xml"},
        ],
    )
    jobs.create_job("old-export", "export", {**spec, "target_keys": []}, started_by="coworker")
    jobs.update_job("old-export", status="succeeded", finished_at="2026-05-06T00:00:00+00:00")
    jobs.create_job("durable-visible", "update", spec, started_by="coworker")
    jobs.ensure_source_runs("durable-visible", spec, "shakira")
    rows = jobs.source_run_rows("durable-visible")
    jobs.update_source_run(rows[0]["id"], status="complete", cursor={}, candidates_seen=2, candidates_total=2, finished=True)
    jobs.update_source_run(rows[1]["id"], status="failed_needs_fix", cursor={}, last_error="feed broke", finished=True)
    jobs.append_event("durable-visible", "incremental_publish_complete", {"count": 1, "items": ["assets/clipping-data.json"]})

    observed = jobs.get_job("durable-visible")

    assert observed["sourceRunCount"] == 2
    assert observed["sourceRunVisibleCount"] == 2
    assert observed["sourceRunCounts"] == {"complete": 1, "failed_needs_fix": 1}
    assert observed["coverageState"] == "failed_needs_fix"
    assert observed["publishedAt"] > "2026-05-06T00:00:00+00:00"


def test_grouped_durable_source_units_keep_one_ledger_per_source_window(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    monkeypatch.setattr(jobs, "RSS_FEEDS", [{"source_name": "Fonte RSS", "url": "https://example.com/rss.xml"}])
    monkeypatch.setattr(jobs, "WORDPRESS_API_SITES", [{"source_name": "WP", "base_url": "https://example.com"}])
    monkeypatch.setattr(
        jobs,
        "FLAVIO_INTERNAL_SEARCH_TARGETS",
        [SimpleNamespace(source_name="Busca Interna", page_size=10)],
    )
    monkeypatch.setattr(
        jobs,
        "SITEMAP_DAILY_SOURCES",
        [{"source_name": "Sitemap", "host": "example.com", "sitemap_url_template": "https://example.com/{yyyy}/{mm}/{dd}.xml"}],
    )
    monkeypatch.setattr(jobs, "VEJARIO_ARCHIVE_TARGETS", [])
    monkeypatch.setattr(jobs, "CAMARA_MAX_PAGES", 0)
    spec = {
        "preset": "custom",
        "collector": "all",
        "target_keys": ["alpha", "beta"],
        "target_snapshots": [
            {"key": "alpha", "display_name": "Alpha", "keywords": ["Alpha"], "primary": True},
            {"key": "beta", "display_name": "Beta", "keywords": ["Beta"], "primary": True},
        ],
        "date_from": "2026-04-01",
        "date_to": "2026-04-01",
        "export": False,
        "durable": True,
    }

    units = jobs.build_grouped_source_units(spec)

    assert [unit.source_type for unit in units] == [
        "rss",
        "google_news",
        "wordpress_api",
        "internal_search",
        "sitemap_daily",
    ]
    query_cursors = [unit.cursor for unit in units if unit.source_type != "rss"]
    assert all(cursor["queries"] == ["Alpha", "Beta"] or cursor["queries"] == ['"Alpha"', '"Beta"'] for cursor in query_cursors)


def test_grouped_durable_runner_migrates_legacy_rows_and_ingests_all_targets(monkeypatch, tmp_path):
    import threading
    from pipeline import ingest
    from pipeline.collectors import CandidateArticle

    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    monkeypatch.setenv("CLIPPING_SOURCE_RUN_YIELD_SECONDS", "0")
    monkeypatch.setattr(jobs, "RSS_FEEDS", [{"source_name": "Fonte RSS", "url": "https://example.com/rss.xml"}])
    spec = {
        "preset": "custom",
        "collector": "rss",
        "target_keys": ["alpha", "beta"],
        "target_snapshots": [
            {"key": "alpha", "display_name": "Alpha", "keywords": ["Alpha"], "primary": True},
            {"key": "beta", "display_name": "Beta", "keywords": ["Beta"], "primary": True},
        ],
        "date_from": "2026-04-01",
        "date_to": "2026-04-01",
        "export": False,
        "durable": True,
    }
    jobs.create_job("grouped-runner", "update", spec, started_by="coworker")
    jobs.ensure_source_runs("grouped-runner", spec, "alpha")
    assert {row["target_key"] for row in jobs.source_run_rows("grouped-runner")} == {"alpha"}
    observed_options: dict[str, object] = {}

    monkeypatch.setattr(
        jobs,
        "collect_rss",
        lambda **_kwargs: [
            CandidateArticle(
                title="Alpha e Beta aparecem no mesmo texto",
                url="https://example.com/alpha-beta",
                source_name="Fonte RSS",
                source_type="rss",
                published_at="2026-04-01T12:00:00+00:00",
                snippet="Alpha Beta",
                metadata={},
            )
        ],
    )

    def fake_process_candidates(source_name, source_type, candidates, *, options=None, progress_callback=None):
        observed_options["target_keys"] = list(options.target_keys or [])
        observed_options["snapshots"] = [item["key"] for item in list(options.target_snapshots or [])]
        return ingest.IngestionResult(source_name, source_type, len(candidates), 1, 2, 1, [])

    monkeypatch.setattr(jobs, "process_candidates", fake_process_candidates)

    result = jobs.run_durable_update("grouped-runner", spec, threading.Event())
    rows = jobs.source_run_rows("grouped-runner")
    observed = jobs.get_job("grouped-runner")

    assert result["coverage_state"] == "complete"
    assert len(rows) == 1
    assert rows[0]["target_key"] == jobs.GROUPED_SOURCE_RUN_TARGET_KEY
    assert observed_options["target_keys"] == ["alpha", "beta"]
    assert observed_options["snapshots"] == ["alpha", "beta"]
    assert any(event["event"] == "source_run_ledger_migrated" for event in observed["events"])


def test_grouped_wordpress_source_run_tracks_completed_queries(monkeypatch, tmp_path):
    from pipeline.collectors import CandidateArticle

    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    monkeypatch.setattr(jobs, "WORDPRESS_API_SITES", [{"source_name": "WP", "base_url": "https://example.com"}])
    calls: list[tuple[str, int]] = []

    def fake_collect_wordpress_api(query, **kwargs):
        page = int(kwargs["start_page"])
        calls.append((query, page))
        if query == "Alpha" and page == 1:
            return [
                CandidateArticle(
                    title=f"Alpha {idx}",
                    url=f"https://example.com/alpha-{idx}",
                    source_name="WP",
                    source_type="wordpress_api",
                    published_at="2026-04-01T12:00:00+00:00",
                    snippet="Alpha",
                    metadata={},
                )
                for idx in range(jobs.WORDPRESS_PAGE_SIZE)
            ]
        return []

    monkeypatch.setattr(jobs, "collect_wordpress_api", fake_collect_wordpress_api)
    spec = {"date_from": "2026-04-01", "date_to": "2026-04-01"}

    candidates, next_cursor, complete = jobs.collect_source_run_candidates(
        spec,
        {"source_type": "wordpress_api", "source_name": "WP", "candidates_seen": 0, "candidates_total": 0},
        {"site_index": 0, "queries": ["Alpha", "Beta"], "page": 1, "complete_queries": []},
    )
    assert len(candidates) == jobs.WORDPRESS_PAGE_SIZE
    assert complete is False
    assert next_cursor["page"] == 2
    assert next_cursor["complete_queries"] == ["Beta"]

    candidates, next_cursor, complete = jobs.collect_source_run_candidates(
        spec,
        {"source_type": "wordpress_api", "source_name": "WP", "candidates_seen": 25, "candidates_total": 25},
        next_cursor,
    )
    assert candidates == []
    assert complete is True
    assert next_cursor["complete_queries"] == ["Alpha", "Beta"]
    assert calls == [("Alpha", 1), ("Beta", 1), ("Alpha", 2)]


def test_disabled_source_units_are_reconciled_out_of_resumed_jobs(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    spec = {
        "preset": "custom",
        "collector": "rss",
        "target_keys": ["shakira"],
        "date_from": "2026-04-01",
        "date_to": "2026-05-05",
        "export": True,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
        "durable": True,
    }
    monkeypatch.setattr(
        jobs,
        "RSS_FEEDS",
        [
            {"source_name": "R7", "url": "https://noticias.r7.com/rss.xml"},
            {"source_name": "Band", "url": "https://example.com/band.xml"},
        ],
    )
    jobs.create_job("disabled-feed", "update", spec, started_by="coworker")
    jobs.ensure_source_runs("disabled-feed", spec, "shakira")
    assert [row["source_key"] for row in jobs.source_run_rows("disabled-feed")] == ["rss:0", "rss:1"]

    monkeypatch.setattr(
        jobs,
        "RSS_FEEDS",
        [
            {"source_name": "R7", "url": "https://noticias.r7.com/rss.xml", "disabled": "true"},
            {"source_name": "Band", "url": "https://example.com/band.xml"},
        ],
    )
    jobs.ensure_source_runs("disabled-feed", spec, "shakira")

    rows = jobs.source_run_rows("disabled-feed")
    disabled = next(row for row in rows if row["source_key"] == "rss:0")
    active = next(row for row in rows if row["source_key"] == "rss:1")
    assert disabled["status"] == "complete"
    assert "desativada" in disabled["last_error"]
    assert active["status"] == "pending"


def test_durable_wordpress_units_use_secondary_target_query_not_flavio_site_variants(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    monkeypatch.setattr(
        jobs,
        "WORDPRESS_API_SITES",
        [{"source_name": "Agenda do Poder", "base_url": "https://agendadopoder.com.br", "query_variants": ["Flavio Valle"]}],
    )

    units = jobs.build_source_units({"collector": "wordpress_api"}, "shakira")

    assert units
    assert all(unit.source_key.startswith("wordpress_api_v2:") for unit in units)
    assert {unit.cursor["query"] for unit in units} == {"Shakira"}
    assert {unit.cursor["page_size"] for unit in units} == {25}


def test_durable_wordpress_source_runs_use_small_api_pages(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    spec = {
        "preset": "custom",
        "collector": "wordpress_api",
        "target_keys": ["shakira"],
        "date_from": "2026-04-01",
        "date_to": "2026-05-05",
        "export": True,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
        "durable": True,
    }
    monkeypatch.setattr(jobs, "WORDPRESS_API_SITES", [{"source_name": "Diario", "base_url": "https://example.com"}])
    observed: dict[str, object] = {}

    def fake_collect_wordpress_api(query, **kwargs):
        observed["query"] = query
        observed.update(kwargs)
        return []

    monkeypatch.setattr(jobs, "collect_wordpress_api", fake_collect_wordpress_api)

    candidates, next_cursor, complete = jobs.collect_source_run_candidates(
        spec,
        {"source_type": "wordpress_api", "source_name": "Diario"},
        {"site_index": 0, "query_index": 0, "query": "Shakira", "page": 3},
    )

    assert candidates == []
    assert complete is True
    assert next_cursor["page"] == 3
    assert observed["query"] == "Shakira"
    assert observed["per_site_limit"] == jobs.WORDPRESS_PAGE_SIZE == 25
    assert observed["per_page"] == 25
    assert observed["start_page"] == 3
    assert observed["max_pages"] == 1


def test_late_wordpress_hard_timeout_completes_source_run(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    spec = {
        "preset": "custom",
        "collector": "wordpress_api",
        "target_keys": ["shakira"],
        "date_from": "2026-04-01",
        "date_to": "2026-05-05",
        "export": True,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
        "durable": True,
    }
    monkeypatch.setattr(jobs, "WORDPRESS_API_SITES", [{"source_name": "Agenda", "base_url": "https://example.com"}])

    def timeout_wordpress_api(*_args, **_kwargs):
        raise TimeoutError("fetch_url hard timeout (35s): https://example.com/wp-json/wp/v2/posts?page=25")

    monkeypatch.setattr(jobs, "collect_wordpress_api", timeout_wordpress_api)

    candidates, next_cursor, complete = jobs.collect_source_run_candidates(
        spec,
        {
            "source_type": "wordpress_api",
            "source_name": "Agenda",
            "candidates_seen": 600,
            "candidates_total": 600,
        },
        {"site_index": 0, "query_index": 0, "query": "Shakira", "page": 25},
    )

    assert candidates == []
    assert complete is True
    assert next_cursor["page"] == 25


def test_early_wordpress_hard_timeout_still_fails_source_run(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    spec = {
        "preset": "custom",
        "collector": "wordpress_api",
        "target_keys": ["shakira"],
        "date_from": "2026-04-01",
        "date_to": "2026-05-05",
        "export": True,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
        "durable": True,
    }
    monkeypatch.setattr(jobs, "WORDPRESS_API_SITES", [{"source_name": "Agenda", "base_url": "https://example.com"}])

    def timeout_wordpress_api(*_args, **_kwargs):
        raise TimeoutError("fetch_url hard timeout (35s): https://example.com/wp-json/wp/v2/posts?page=2")

    monkeypatch.setattr(jobs, "collect_wordpress_api", timeout_wordpress_api)

    try:
        jobs.collect_source_run_candidates(
            spec,
            {
                "source_type": "wordpress_api",
                "source_name": "Agenda",
                "candidates_seen": 25,
                "candidates_total": 25,
            },
            {"site_index": 0, "query_index": 0, "query": "Shakira", "page": 2},
        )
    except TimeoutError:
        pass
    else:
        raise AssertionError("early WordPress timeout should still fail the source run")


def test_durable_internal_search_units_are_versioned_and_paged(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    units = jobs.build_source_units({"collector": "internal_search"}, "shakira")

    assert units
    assert all(unit.source_key.startswith("internal_search_v2:") for unit in units)
    assert {unit.cursor["query"] for unit in units} == {"Shakira"}
    assert all(unit.cursor["page"] == 1 for unit in units)
    assert all(unit.cursor["page_size"] >= 1 for unit in units)


def test_durable_internal_search_source_runs_use_one_page(monkeypatch, tmp_path):
    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    spec = {
        "preset": "custom",
        "collector": "internal_search",
        "target_keys": ["shakira"],
        "date_from": "2026-04-01",
        "date_to": "2026-05-05",
        "export": True,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
        "durable": True,
    }
    adapter = jobs.FLAVIO_INTERNAL_SEARCH_TARGETS[0]
    observed: dict[str, object] = {}

    def fake_collect_internal_site_search(**kwargs):
        observed.update(kwargs)
        return [object()] * int(adapter.page_size or 10)

    monkeypatch.setattr(jobs, "collect_internal_site_search", fake_collect_internal_site_search)

    candidates, next_cursor, complete = jobs.collect_source_run_candidates(
        spec,
        {"source_type": "internal_search", "source_name": adapter.source_name},
        {"adapter_index": 0, "query_index": 0, "query": "Shakira", "page": 4},
    )

    assert len(candidates) == int(adapter.page_size or 10)
    assert complete is False
    assert next_cursor["page"] == 5
    assert next_cursor["page_size"] == int(adapter.page_size or 10)
    assert observed["queries"] == ["Shakira"]
    assert observed["adapters"] == [adapter]
    assert observed["limit_per_adapter"] == int(adapter.page_size or 10)
    assert observed["max_pages_per_adapter"] == 1
    assert observed["start_page"] == 4


def test_durable_runner_processes_source_units_and_exposes_coverage(monkeypatch, tmp_path):
    import threading
    from pipeline import ingest
    from pipeline.collectors import CandidateArticle

    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    monkeypatch.setattr(jobs.artifact_store, "enabled", False)
    monkeypatch.setattr(jobs, "RSS_FEEDS", [{"source_name": "Fonte RSS", "url": "https://example.com/rss.xml"}])
    spec = {
        "preset": "custom",
        "collector": "rss",
        "target_keys": ["shakira"],
        "date_from": "2026-04-01",
        "date_to": "2026-05-05",
        "export": False,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
        "durable": True,
    }
    jobs.create_job("durable-runner", "update", spec, started_by="coworker")

    def fake_collect_rss(**_kwargs):
        return [
            CandidateArticle(
                title="Shakira canta em Copacabana",
                url="https://example.com/shakira",
                source_name="Fonte RSS",
                source_type="rss",
                published_at="2026-05-05T12:00:00+00:00",
                snippet="Shakira no Rio.",
                metadata={},
            )
        ]

    def fake_process_candidates(source_name, source_type, candidates, *, options=None, progress_callback=None):
        if progress_callback:
            progress_callback(
                "article_saved",
                {
                    "article_id": 1,
                    "story_id": 1,
                    "url": candidates[0].url,
                    "title": candidates[0].title,
                    "published_at": candidates[0].published_at,
                    "source_name": source_name,
                    "source_type": source_type,
                    "target_keys": ["shakira"],
                    "articles_inserted_delta": 1,
                    "mentions_inserted_delta": 1,
                    "stories_touched_delta": 1,
                    "publication_state": "saved",
                },
            )
        return ingest.IngestionResult(source_name, source_type, len(candidates), 1, 1, 1, [])

    monkeypatch.setattr(jobs, "collect_rss", fake_collect_rss)
    monkeypatch.setattr(jobs, "process_candidates", fake_process_candidates)

    result = jobs.run_durable_update("durable-runner", spec, threading.Event())
    observed = jobs.get_job("durable-runner")

    assert result["coverage_state"] == "complete"
    assert result["stories_touched"] == 1
    assert observed["coverageState"] == "complete"
    assert observed["sourceRuns"][0]["status"] == "complete"
    assert observed["progress"]["storiesTouched"] == 1


def test_durable_runner_throttles_empty_source_checkpoints(monkeypatch, tmp_path):
    import threading
    from pipeline import ingest

    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    monkeypatch.setattr(jobs, "RSS_FEEDS", [{"source_name": "Fonte RSS", "url": "https://example.com/rss.xml"}])
    monkeypatch.setenv("CLIPPING_SOURCE_RUN_YIELD_SECONDS", "0")
    spec = {
        "preset": "custom",
        "collector": "rss",
        "target_keys": ["shakira"],
        "date_from": "2026-04-01",
        "date_to": "2026-05-05",
        "export": False,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
        "durable": True,
    }
    jobs.create_job("durable-empty-checkpoint", "update", spec, started_by="coworker")
    checkpoint_calls = []

    monkeypatch.setattr(jobs, "collect_rss", lambda **_kwargs: [])
    monkeypatch.setattr(
        jobs,
        "process_candidates",
        lambda source_name, source_type, candidates, **_kwargs: ingest.IngestionResult(
            source_name,
            source_type,
            len(candidates),
            0,
            0,
            0,
            [],
        ),
    )
    monkeypatch.setattr(jobs, "publish_incremental_snapshot", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        jobs,
        "upload_live_checkpoint",
        lambda job_id, *, reason, force=False: checkpoint_calls.append((job_id, reason, force)) or [],
    )

    jobs.run_durable_update("durable-empty-checkpoint", spec, threading.Event())

    assert checkpoint_calls == [("durable-empty-checkpoint", "source-run-checkpoint", False)]


def test_durable_runner_forces_checkpoint_when_source_saves(monkeypatch, tmp_path):
    import threading
    from pipeline import ingest
    from pipeline.collectors import CandidateArticle

    _, jobs, _ = reload_admin_modules(monkeypatch, tmp_path)
    monkeypatch.setattr(jobs, "RSS_FEEDS", [{"source_name": "Fonte RSS", "url": "https://example.com/rss.xml"}])
    monkeypatch.setenv("CLIPPING_SOURCE_RUN_YIELD_SECONDS", "0")
    spec = {
        "preset": "custom",
        "collector": "rss",
        "target_keys": ["shakira"],
        "date_from": "2026-04-01",
        "date_to": "2026-05-05",
        "export": False,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
        "durable": True,
    }
    jobs.create_job("durable-saved-checkpoint", "update", spec, started_by="coworker")
    checkpoint_calls = []

    monkeypatch.setattr(
        jobs,
        "collect_rss",
        lambda **_kwargs: [
            CandidateArticle(
                title="Shakira canta em Copacabana",
                url="https://example.com/shakira",
                source_name="Fonte RSS",
                source_type="rss",
                published_at="2026-05-05T12:00:00+00:00",
                snippet="Shakira no Rio.",
                metadata={},
            )
        ],
    )
    monkeypatch.setattr(
        jobs,
        "process_candidates",
        lambda source_name, source_type, candidates, **_kwargs: ingest.IngestionResult(
            source_name,
            source_type,
            len(candidates),
            1,
            1,
            1,
            [],
        ),
    )
    monkeypatch.setattr(jobs, "publish_incremental_snapshot", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        jobs,
        "upload_live_checkpoint",
        lambda job_id, *, reason, force=False: checkpoint_calls.append((job_id, reason, force)) or [],
    )

    jobs.run_durable_update("durable-saved-checkpoint", spec, threading.Event())

    assert checkpoint_calls == [("durable-saved-checkpoint", "source-run-saved-checkpoint", True)]


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


def test_process_candidates_uses_frozen_target_snapshot(monkeypatch, tmp_path):
    from pipeline import ingest
    from pipeline.matcher import Target

    db_file = tmp_path / "frozen-target.db"
    monkeypatch.setattr(
        ingest,
        "get_active_targets",
        lambda: [Target(key="ana_teste", display_name="Ana Renomeada", keywords=["Ana Renomeada"])],
    )
    candidate = ingest.CandidateArticle(
        title="Ana Teste confirma agenda cultural",
        url="https://example.com/ana-teste",
        source_name="Google News",
        source_type="google_news",
        published_at="2026-05-17T12:00:00+00:00",
        snippet="Ana Teste foi citada na programacao cultural.",
        metadata={},
    )

    result = ingest.process_candidates(
        "Google News",
        "google_news",
        [candidate],
        options=ingest.IngestionOptions(
            target_keys=["ana_teste"],
            target_snapshots=[
                {
                    "key": "ana_teste",
                    "display_name": "Ana Teste",
                    "keywords": ["Ana Teste"],
                    "primary": False,
                }
            ],
            date_from="2026-05-17",
            date_to="2026-05-17",
            db_path=str(db_file),
        ),
    )

    assert result.articles_inserted == 1
    assert result.mentions_inserted == 1
    with sqlite3.connect(db_file) as conn:
        rows = conn.execute("SELECT target_key, target_name, keyword_matched FROM mentions").fetchall()
    assert rows == [("ana_teste", "Ana Teste", "Ana Teste")]


def test_run_source_run_accepts_persisted_dict_target_snapshot(monkeypatch, tmp_path):
    _, jobs, db_file = reload_admin_modules(monkeypatch, tmp_path)
    from pipeline import ingest

    spec = {
        "preset": "custom",
        "collector": "rss",
        "target_keys": ["ana_teste"],
        "target_snapshots": [
            {
                "key": "ana_teste",
                "display_name": "Ana Teste",
                "keywords": ["Ana Teste"],
                "primary": False,
            }
        ],
        "date_from": "2026-05-17",
        "date_to": "2026-05-17",
        "export": False,
        "max_candidates": 10,
        "max_process_seconds": 30,
        "candidate_workers": 1,
        "durable": True,
    }
    monkeypatch.setattr(jobs, "RSS_FEEDS", [{"source_name": "Fonte RSS", "url": "https://example.com/rss.xml"}])
    jobs.create_job("dict-target-source-run", "update", spec, started_by="coworker")
    jobs.ensure_source_runs("dict-target-source-run", spec, "ana_teste")

    candidate = ingest.CandidateArticle(
        title="Ana Teste confirma agenda cultural",
        url="https://example.com/ana-teste-source-run",
        source_name="Fonte RSS",
        source_type="rss",
        published_at="2026-05-17T12:00:00+00:00",
        snippet="Ana Teste foi citada na programacao cultural.",
        metadata={},
    )
    monkeypatch.setattr(jobs, "collect_source_run_candidates", lambda *_args: ([candidate], {}, True))

    row = jobs.source_run_rows("dict-target-source-run")[0]
    result = jobs.run_source_run(
        "dict-target-source-run",
        spec,
        row,
        target_label="Ana Teste",
        cancel_event=threading.Event(),
    )

    assert result["articles_inserted"] == 1
    assert jobs.source_run_rows("dict-target-source-run")[0]["status"] == "complete"
    with sqlite3.connect(db_file) as conn:
        rows = conn.execute("SELECT target_key, target_name, keyword_matched FROM mentions").fetchall()
    assert rows == [("ana_teste", "Ana Teste", "Ana Teste")]


def test_process_candidates_prefetches_articles_with_serial_db_writes(monkeypatch, tmp_path):
    from pipeline import ingest
    from pipeline.matcher import Target

    db_file = tmp_path / "parallel-candidates.db"
    active_fetches = 0
    max_active_fetches = 0
    fetch_lock = threading.Lock()
    write_threads: list[str] = []
    events: list[tuple[str, dict]] = []

    def fake_fetch_full_article_text(url, *, request_timeout):
        nonlocal active_fetches, max_active_fetches
        with fetch_lock:
            active_fetches += 1
            max_active_fetches = max(max_active_fetches, active_fetches)
        time.sleep(0.05)
        with fetch_lock:
            active_fetches -= 1
        return (
            url,
            "<html></html>",
            (
                "Flavio Valle confirmou uma agenda cultural no Rio de Janeiro com reunioes "
                "publicas, visitas tecnicas, planejamento local e novas entregas para moradores."
            ),
            "Agenda cultural no Rio",
            "2026-05-17T12:00:00+00:00",
        )

    original_insert_article = ClippingDB.insert_article_if_new

    def tracked_insert_article(self, *args, **kwargs):
        write_threads.append(threading.current_thread().name)
        return original_insert_article(self, *args, **kwargs)

    monkeypatch.setattr(ingest, "fetch_full_article_text", fake_fetch_full_article_text)
    monkeypatch.setattr(ClippingDB, "insert_article_if_new", tracked_insert_article)
    monkeypatch.setattr(
        ingest,
        "get_active_targets",
        lambda: [Target(key="flavio_valle", display_name="Flavio Valle", keywords=["Flavio Valle"], primary=True)],
    )
    candidates = [
        ingest.CandidateArticle(
            title=f"Agenda cultural no Rio {idx}",
            url=f"https://example.com/agenda-cultural-{idx}",
            source_name="Fonte Teste",
            source_type="rss",
            published_at="2026-05-17T12:00:00+00:00",
            snippet="Sem mencao no resumo para forcar busca no texto completo.",
            metadata={},
        )
        for idx in range(3)
    ]

    result = ingest.process_candidates(
        "Fonte Teste",
        "rss",
        candidates,
        options=ingest.IngestionOptions(
            target_keys=["flavio_valle"],
            date_from="2026-05-17",
            date_to="2026-05-17",
            db_path=str(db_file),
            candidate_workers=2,
            archive_full_text=False,
        ),
        progress_callback=lambda event, payload: events.append((event, payload)),
    )

    assert max_active_fetches >= 2
    assert result.candidates_seen == 3
    assert result.articles_inserted == 3
    assert set(write_threads) == {threading.current_thread().name}
    assert [event for event, _ in events].count("article_saved") == 3
    with sqlite3.connect(db_file) as conn:
        assert conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0] == 3


def test_process_candidates_times_out_stuck_prefetch_future(monkeypatch, tmp_path):
    from concurrent.futures import TimeoutError as FuturesTimeoutError
    from pipeline import ingest
    from pipeline.matcher import Target

    db_file = tmp_path / "prefetch-timeout.db"
    observed_timeouts: list[int] = []
    cancelled: list[bool] = []
    events: list[tuple[str, dict]] = []

    class StuckFuture:
        def result(self, timeout=None):
            observed_timeouts.append(timeout)
            raise FuturesTimeoutError()

        def cancel(self):
            cancelled.append(True)

    class FakeExecutor:
        def __init__(self, *args, **kwargs):
            pass

        def submit(self, *args, **kwargs):
            return StuckFuture()

        def shutdown(self, *args, **kwargs):
            pass

    monkeypatch.setattr(ingest, "ThreadPoolExecutor", FakeExecutor)
    monkeypatch.setattr(
        ingest,
        "get_active_targets",
        lambda: [Target(key="alpha", display_name="Alpha", keywords=["Alpha"], primary=True)],
    )
    candidate = ingest.CandidateArticle(
        title="Texto sem alvo visivel",
        url="https://example.com/stuck-google-redirect",
        source_name="Google News",
        source_type="google_news",
        published_at="2026-05-17T12:00:00+00:00",
        snippet="Resumo sem correspondencia para forcar fetch.",
        metadata={"force_full_fetch": True},
    )

    result = ingest.process_candidates(
        "Google News",
        "google_news",
        [candidate],
        options=ingest.IngestionOptions(
            target_keys=["alpha"],
            date_from="2026-05-17",
            date_to="2026-05-17",
            db_path=str(db_file),
            request_timeout_seconds=3,
            candidate_workers=2,
            archive_full_text=False,
        ),
        progress_callback=lambda event, payload: events.append((event, payload)),
    )

    assert observed_timeouts == [8]
    assert cancelled == [True]
    assert result.candidates_seen == 1
    assert result.articles_inserted == 0
    assert any("article_prefetch hard timeout" in error for error in result.errors)
    assert any(
        event == "candidate_evaluated" and payload.get("reason", "").startswith("fetch_fail:article_prefetch hard timeout")
        for event, payload in events
    )


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
    events: list[tuple[str, dict]] = []

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
        progress_callback=lambda event, payload: events.append((event, payload)),
    )

    assert result.articles_inserted == 0
    assert result.mentions_inserted == 1
    assert result.stories_touched == 1
    article_saved = [payload for event, payload in events if event == "article_saved"]
    assert len(article_saved) == 1
    assert article_saved[0]["article_id"] == article_id
    assert article_saved[0]["story_id"] == story_id
    assert article_saved[0]["target_keys"] == ["shakira"]
    assert article_saved[0]["articles_inserted_delta"] == 0
    assert article_saved[0]["mentions_inserted_delta"] == 1
    assert article_saved[0]["stories_touched_delta"] == 1
    assert article_saved[0]["publication_state"] == "saved"
    assert article_saved[0]["reason"] == "existing_article_target_updated"
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


def test_cleanup_removes_secondary_target_only_in_late_incidental_preview(monkeypatch, tmp_path):
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
    late_incidental_context = (
        "Projeto com palestras e orientacao profissional para mulheres maduras. "
        "A iniciativa aborda inteligencia emocional, empreendedorismo, saude e carreira. "
        + ("Contexto institucional sem relacao direta com musica ou espetaculo. " * 10)
        + "A responsavel tambem trabalhou em eventos como Rock in Rio, Madonna, Lady Gaga e Shakira."
    )
    assert late_incidental_context.lower().find("shakira") > 500
    with ClippingDB(db_file) as db:
        article_id = db.insert_article(
            url="https://example.com/projeto-transicao",
            title="Projeto busca orientar mulheres a lidarem com processos de transicao na vida",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-05-05T14:56:48+00:00",
            snippet=late_incidental_context,
            full_text=late_incidental_context,
        )
        assert article_id is not None
        db.insert_mention(article_id, "flavio_valle", "Flavio Valle", "Flavio Valle")
        story_id = db.create_story(
            title="Projeto busca orientar mulheres a lidarem com processos de transicao na vida",
            summary=late_incidental_context,
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

    cleanup = db_admin.cleanup_false_backfilled_target_mentions(db_file, ["shakira"])

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


def test_cleanup_prefers_saved_text_over_misleading_secondary_snippet(monkeypatch, tmp_path):
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
            url="https://example.com/projeto-sem-shakira",
            title="Projeto busca orientar mulheres a lidarem com processos de transicao na vida",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-05-05T14:56:48+00:00",
            snippet="Trecho de busca enganoso cita Shakira em uma lista lateral.",
            full_text="Texto real da materia sobre empreendedorismo, carreira e inteligencia emocional.",
        )
        assert article_id is not None
        db.conn.execute(
            "UPDATE articles SET summary = ? WHERE id = ?",
            ("Resumo real da materia sobre empreendedorismo, carreira e inteligencia emocional.", article_id),
        )
        db.conn.commit()
        db.insert_mention(article_id, "flavio_valle", "Flavio Valle", "Flavio Valle")
        story_id = db.create_story(
            title="Projeto busca orientar mulheres a lidarem com processos de transicao na vida",
            summary="Resumo real da materia.",
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

    cleanup = db_admin.cleanup_false_backfilled_target_mentions(db_file, ["shakira"])

    assert cleanup["removedMentions"] == 1
    with sqlite3.connect(db_file) as conn:
        assert {
            row[0]
            for row in conn.execute(
                "SELECT target_key FROM mentions WHERE article_id = ?",
                (article_id,),
            ).fetchall()
        } == {"flavio_valle"}
        assert {
            row[0]
            for row in conn.execute(
                "SELECT target_key FROM story_targets WHERE story_id = ?",
                (story_id,),
            ).fetchall()
        } == {"flavio_valle"}


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


def test_process_candidates_skips_secondary_target_only_as_late_incidental_mention(monkeypatch, tmp_path):
    from pipeline import ingest
    from pipeline.matcher import Target

    db_file = tmp_path / "secondary-late-incidental.db"
    events = []

    def unexpected_fetch(*_args, **_kwargs):
        raise AssertionError("late incidental preview match should not need article fetch")

    monkeypatch.setattr(ingest, "fetch_full_article_text", unexpected_fetch)
    monkeypatch.setattr(
        ingest,
        "get_active_targets",
        lambda: [Target(key="shakira", display_name="shakira", keywords=["shakira"], primary=False)],
    )
    late_incidental_context = (
        "Projeto com palestras e orientacao profissional para mulheres maduras. "
        "A iniciativa aborda inteligencia emocional, empreendedorismo, saude e carreira. "
        + ("Contexto institucional sem relacao direta com musica ou espetaculo. " * 10)
        + "A responsavel tambem trabalhou em eventos como Rock in Rio, Madonna, Lady Gaga e Shakira."
    )
    assert late_incidental_context.lower().find("shakira") > 500
    candidate = ingest.CandidateArticle(
        title="Projeto busca orientar mulheres a lidarem com processos de transicao na vida",
        url="https://example.com/projeto-transicao",
        source_name="Diario do Rio",
        source_type="rss",
        published_at="2026-05-05T14:56:48+00:00",
        snippet=late_incidental_context,
        metadata={},
    )

    result = ingest.process_candidates(
        "Diario do Rio",
        "rss",
        [candidate],
        options=ingest.IngestionOptions(
            target_keys=["shakira"],
            date_from="2026-05-05",
            date_to="2026-05-05",
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


def test_process_candidates_prefers_fetched_text_over_misleading_secondary_snippet(monkeypatch, tmp_path):
    from pipeline import ingest
    from pipeline.matcher import Target

    db_file = tmp_path / "secondary-misleading-snippet.db"
    events = []

    def fake_fetch_full_article_text(*_args, **_kwargs):
        full_text = "Texto real da materia sobre empreendedorismo, carreira e inteligencia emocional."
        return (
            "https://example.com/projeto-sem-shakira",
            "<html></html>",
            full_text,
            "Projeto busca orientar mulheres a lidarem com processos de transicao na vida",
            "2026-05-05T14:56:48+00:00",
        )

    monkeypatch.setattr(ingest, "fetch_full_article_text", fake_fetch_full_article_text)
    monkeypatch.setattr(
        ingest,
        "get_active_targets",
        lambda: [Target(key="shakira", display_name="shakira", keywords=["shakira"], primary=False)],
    )
    candidate = ingest.CandidateArticle(
        title="Projeto busca orientar mulheres a lidarem com processos de transicao na vida",
        url="https://example.com/projeto-sem-shakira",
        source_name="Diario do Rio",
        source_type="rss",
        published_at="2026-05-05T14:56:48+00:00",
        snippet="Trecho de busca enganoso cita Shakira em uma lista lateral.",
        metadata={},
    )

    result = ingest.process_candidates(
        "Diario do Rio",
        "rss",
        [candidate],
        options=ingest.IngestionOptions(
            target_keys=["shakira"],
            date_from="2026-05-05",
            date_to="2026-05-05",
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
            candidate_workers=1,
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


def test_rss_parser_recovers_common_malformed_feed_markup():
    from pipeline.collectors import parse_rss_or_atom

    xml = """<?xml version="1.0"?>
    <rss version="2.0">
      <channel>
        <item>
          <title>Shakira & prefeitura do Rio</title>
          <link>https://example.com/shakira</link>
          <description>Show confirmado</description>
          <media:content url="https://example.com/foto.jpg" />
          <pubDate>Tue, 05 May 2026 12:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    rows = parse_rss_or_atom(xml, "Feed Malformado", "rss")

    assert len(rows) == 1
    assert rows[0].title == "Shakira & prefeitura do Rio"
    assert rows[0].url == "https://example.com/shakira"


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
