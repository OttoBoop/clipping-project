from __future__ import annotations

import sqlite3
import gzip
import hashlib
from types import SimpleNamespace

import pytest

from tools.political_import_sqlite import prepare_snapshot, persist_snapshot_backup


def source_database(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA wal_autocheckpoint=0")
    for name in ("articles", "mentions", "stories", "story_articles"):
        conn.execute(f"CREATE TABLE {name} (id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute(f"INSERT INTO {name} VALUES (1, 'preserved')")
    conn.commit()
    return conn


def test_import_snapshot_includes_wal_and_resume_keeps_original_snapshot(tmp_path):
    source, snapshot = tmp_path / "live.db", tmp_path / "backup" / "frozen.db"
    with source_database(source) as live:
        manifest = prepare_snapshot(source, snapshot)
        assert manifest["integrity"] == "ok"
        assert manifest["counts"] == {name: 1 for name in ("articles", "mentions", "stories", "story_articles")}
        live.execute("INSERT INTO articles VALUES (2, 'new during migration')")
        live.commit()
        resumed = prepare_snapshot(source, snapshot)
        assert resumed["sha256"] == manifest["sha256"]
        with sqlite3.connect(snapshot) as backup:
            assert backup.execute("SELECT value FROM articles").fetchall() == [("preserved",)]
        assert live.execute("SELECT COUNT(*) FROM articles").fetchone()[0] == 2


def test_import_rejects_changed_snapshot_and_never_overwrites_source(tmp_path):
    source, snapshot = tmp_path / "live.db", tmp_path / "snapshot.db"
    with source_database(source):
        with pytest.raises(ValueError, match="differ"):
            prepare_snapshot(source, source)
        prepare_snapshot(source, snapshot)
        with sqlite3.connect(snapshot) as changed:
            changed.execute("UPDATE articles SET value='changed'")
        with pytest.raises(ValueError, match="snapshot_changed"):
            prepare_snapshot(source, snapshot)


class BackupStore:
    enabled = True
    prefix = "test"

    def __init__(self, failure=None):
        self.failure = failure
        self.generations = {}
        self.manifests = {}

    def upload_chunked_file(self, path, remote, **kwargs):
        self.generations[remote] = path.read_bytes()
        return self.failure != "upload"

    def download_gzip_file(self, remote, path):
        if self.failure == "readback":
            return False
        path.write_bytes(b"corrupt" if self.failure == "corrupt" else gzip.decompress(self.generations[remote]))
        return True

    def upload_bytes(self, data, remote, content_type):
        self.manifests[remote] = data
        return self.failure != "manifest"


def backup_fixture(tmp_path, failure=None):
    source = tmp_path / "frozen.db"
    source.write_bytes(b"immutable snapshot bytes")
    manifest = {"snapshot": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    return SimpleNamespace(store=BackupStore(failure)), manifest


def test_remote_backup_verifies_exact_bytes_and_never_reuses_generation(tmp_path):
    service, manifest = backup_fixture(tmp_path)
    first = persist_snapshot_backup(service, manifest)
    second = persist_snapshot_backup(service, manifest)
    assert first != second
    assert len(service.store.generations) == len(service.store.manifests) == 2


@pytest.mark.parametrize("failure,reason", [("upload", "upload_failed"), ("readback", "readback_failed"),
                                           ("corrupt", "digest_mismatch"), ("manifest", "manifest_upload_failed")])
def test_remote_backup_failure_blocks_import(tmp_path, failure, reason):
    service, manifest = backup_fixture(tmp_path, failure)
    with pytest.raises(RuntimeError, match=reason):
        persist_snapshot_backup(service, manifest)
    if failure != "manifest":
        assert not service.store.manifests
