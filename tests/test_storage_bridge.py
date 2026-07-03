from __future__ import annotations

import gzip
import json
import sqlite3
from pathlib import Path
from typing import Any

from web_app.storage_bridge import ArtifactStore, sqlite_snapshot_gzip_file, write_artifact_payload


class FakeResponse:
    status_code = 200
    content = b""

    @property
    def ok(self) -> bool:
        return self.status_code in {200, 201}

    def json(self) -> Any:
        return json.loads(self.content.decode("utf-8"))


def make_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO sample (name) VALUES ('ok')")


def make_marker_db(path: Path, value: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE marker(value TEXT)")
        conn.execute("INSERT INTO marker(value) VALUES (?)", (value,))


def read_marker(path: Path) -> str:
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT value FROM marker").fetchone()
    return str(row[0])


def gzip_file(source: Path, target: Path) -> None:
    with source.open("rb") as source_file, gzip.open(target, "wb") as gzip_file:
        gzip_file.write(source_file.read())


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
    calls: list[dict[str, Any]] = []

    def fake_post(url: str, *, headers: dict[str, str], data: Any, timeout: int) -> FakeResponse:
        call = {
            "url": url,
            "contentType": headers.get("Content-Type"),
            "timeout": timeout,
            "bytesPayload": isinstance(data, (bytes, bytearray)),
        }
        calls.append(call)
        if hasattr(data, "read"):
            payload = data.read()
            restored = tmp_path / "uploaded.db"
            restored.write_bytes(gzip.decompress(payload))
            with sqlite3.connect(restored) as conn:
                observed["row"] = conn.execute("SELECT name FROM sample").fetchone()[0]
        return FakeResponse()

    monkeypatch.setattr("web_app.storage_bridge.requests.post", fake_post)

    assert store.upload_sqlite_snapshot(db_path, "clipping-project/current/data/clipping.db.gz") is True
    gzip_call = next(call for call in calls if call["contentType"] == "application/gzip")
    manifest_call = next(call for call in calls if call["contentType"] == "application/json")
    assert gzip_call["timeout"] == 90
    assert gzip_call["bytesPayload"] is False
    assert manifest_call["bytesPayload"] is True
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


def test_upload_sqlite_snapshot_falls_back_to_chunk_manifest(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "clipping.db"
    make_db(db_path)
    store = configured_store()
    uploaded_bytes: dict[str, bytes] = {}

    monkeypatch.setenv("CLIPPING_SQLITE_UPLOAD_CHUNK_BYTES", "1048576")
    monkeypatch.setattr(store, "upload_path", lambda *_args, **_kwargs: False)

    def fake_upload_bytes(payload: bytes, remote_path: str, content_type: str) -> bool:
        uploaded_bytes[remote_path] = payload
        return True

    monkeypatch.setattr(store, "upload_bytes", fake_upload_bytes)

    assert store.upload_sqlite_snapshot(db_path, "clipping-project/current/data/clipping.db.gz") is True

    manifest = json.loads(uploaded_bytes["clipping-project/current/data/clipping.db.gz.manifest.json"].decode("utf-8"))
    assert manifest["mode"] == "chunks"
    assert manifest["chunk_count"] >= 1
    combined = b"".join(uploaded_bytes[item["path"]] for item in manifest["chunks"])
    restored = tmp_path / "chunked.db"
    restored.write_bytes(gzip.decompress(combined))
    with sqlite3.connect(restored) as conn:
        assert conn.execute("SELECT name FROM sample").fetchone()[0] == "ok"


def test_download_gzip_file_prefers_chunk_manifest(monkeypatch, tmp_path: Path) -> None:
    source_db = tmp_path / "source.db"
    make_db(source_db)
    gz_path = sqlite_snapshot_gzip_file(source_db)
    assert gz_path is not None
    try:
        payload = gz_path.read_bytes()
    finally:
        gz_path.unlink(missing_ok=True)
    midpoint = max(1, len(payload) // 2)
    remote = "clipping-project/current/data/clipping.db.gz"
    manifest = {
        "mode": "chunks",
        "chunks": [
            {"path": f"{remote}.part0000", "size": midpoint},
            {"path": f"{remote}.part0001", "size": len(payload) - midpoint},
        ],
    }
    objects = {
        f"{remote}.manifest.json": json.dumps(manifest).encode("utf-8"),
        f"{remote}.part0000": payload[:midpoint],
        f"{remote}.part0001": payload[midpoint:],
    }
    store = configured_store()

    def fake_get(url: str, *, headers: dict[str, str], timeout: int) -> FakeResponse:
        path = url.split("/object/documentos/", 1)[1]
        response = FakeResponse()
        response.content = objects[path]
        return response

    monkeypatch.setattr("web_app.storage_bridge.requests.get", fake_get)

    restored = tmp_path / "restored.db"
    assert store.download_gzip_file(remote, restored) is True
    with sqlite3.connect(restored) as conn:
        assert conn.execute("SELECT name FROM sample").fetchone()[0] == "ok"


def test_write_gzip_file_restores_valid_sqlite_atomically_and_removes_sidecars(tmp_path: Path) -> None:
    current = tmp_path / "clipping.db"
    replacement = tmp_path / "replacement.db"
    gzipped = tmp_path / "replacement.db.gz"
    make_marker_db(current, "old")
    make_marker_db(replacement, "new")
    Path(str(current) + "-wal").write_bytes(b"stale wal")
    Path(str(current) + "-shm").write_bytes(b"stale shm")
    gzip_file(replacement, gzipped)

    assert ArtifactStore().write_gzip_file(gzipped, current) is True

    assert read_marker(current) == "new"
    assert not Path(str(current) + "-wal").exists()
    assert not Path(str(current) + "-shm").exists()


def test_write_gzip_file_rejects_corrupt_gzip_without_clobbering_db(tmp_path: Path) -> None:
    current = tmp_path / "clipping.db"
    gzipped = tmp_path / "broken.db.gz"
    make_marker_db(current, "old")
    gzipped.write_bytes(b"not a gzip")

    assert ArtifactStore().write_gzip_file(gzipped, current) is False

    assert read_marker(current) == "old"


def test_write_gzip_file_rejects_invalid_sqlite_without_clobbering_db(tmp_path: Path) -> None:
    current = tmp_path / "clipping.db"
    gzipped = tmp_path / "invalid.db.gz"
    make_marker_db(current, "old")
    with gzip.open(gzipped, "wb") as gzip_file_handle:
        gzip_file_handle.write(b"not a sqlite database")

    assert ArtifactStore().write_gzip_file(gzipped, current) is False

    assert read_marker(current) == "old"


def test_raw_sqlite_artifact_rejects_invalid_payload_without_clobbering_db(tmp_path: Path) -> None:
    current = tmp_path / "clipping.db"
    make_marker_db(current, "old")

    assert write_artifact_payload(b"not a sqlite database", current) is False

    assert read_marker(current) == "old"
