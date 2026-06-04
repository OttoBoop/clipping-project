from __future__ import annotations

import gzip
import sqlite3
from pathlib import Path
from typing import Any

from web_app.storage_bridge import ArtifactStore, sqlite_snapshot_gzip_file


class FakeResponse:
    status_code = 200


def make_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO sample (name) VALUES ('ok')")


def configured_store() -> ArtifactStore:
    store = ArtifactStore()
    store.url = "https://supabase.example"
    store.key = "service-key"
    store.bucket = "documentos"
    store.prefix = "clipping-project"
    store.enabled = True
    return store


def test_sqlite_snapshot_gzip_file_round_trips(tmp_path: Path) -> None:
    db_path = tmp_path / "clipping.db"
    make_db(db_path)

    gz_path = sqlite_snapshot_gzip_file(db_path)

    assert gz_path is not None
    try:
        restored = tmp_path / "restored.db"
        restored.write_bytes(gzip.decompress(gz_path.read_bytes()))
        with sqlite3.connect(restored) as conn:
            assert conn.execute("SELECT name FROM sample").fetchone()[0] == "ok"
    finally:
        gz_path.unlink(missing_ok=True)


def test_upload_sqlite_snapshot_streams_gzip_file(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "clipping.db"
    make_db(db_path)
    store = configured_store()
    observed: dict[str, Any] = {}

    def fake_post(url: str, *, headers: dict[str, str], data: Any, timeout: int) -> FakeResponse:
        observed["url"] = url
        observed["contentType"] = headers.get("Content-Type")
        observed["timeout"] = timeout
        observed["bytesPayload"] = isinstance(data, (bytes, bytearray))
        payload = data.read()
        restored = tmp_path / "uploaded.db"
        restored.write_bytes(gzip.decompress(payload))
        with sqlite3.connect(restored) as conn:
            observed["row"] = conn.execute("SELECT name FROM sample").fetchone()[0]
        return FakeResponse()

    monkeypatch.setattr("web_app.storage_bridge.requests.post", fake_post)

    assert store.upload_sqlite_snapshot(db_path, "clipping-project/current/data/clipping.db.gz") is True
    assert observed["contentType"] == "application/gzip"
    assert observed["timeout"] == 90
    assert observed["bytesPayload"] is False
    assert observed["row"] == "ok"


def test_upload_file_delegates_db_to_streaming_snapshot(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "clipping.db"
    make_db(db_path)
    store = configured_store()
    calls: list[tuple[Path, str]] = []

    def fake_upload_sqlite_snapshot(local_path: Path, remote_path: str) -> bool:
        calls.append((local_path, remote_path))
        return True

    monkeypatch.setattr(store, "upload_sqlite_snapshot", fake_upload_sqlite_snapshot)

    assert store.upload_file(db_path, "clipping-project/backups/db") is True
    assert calls == [(db_path, "clipping-project/backups/db")]
