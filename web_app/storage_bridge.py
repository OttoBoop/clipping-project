from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import gzip
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from .config import ASSETS_DIR, DATA_DIR, db_path, local_writes_allowed


RUNTIME_FILES = (
    ("data/clipping.db", lambda: db_path()),
    ("data/targets.json", lambda: DATA_DIR / "targets.json"),
    ("data/clipping_credentials.json", lambda: DATA_DIR / "clipping_credentials.json"),
    ("data/viewer_profiles.json", lambda: DATA_DIR / "viewer_profiles.json"),
    ("assets/clipping-data.json", lambda: ASSETS_DIR / "clipping-data.json"),
    ("assets/clipping-raw-texts.json", lambda: ASSETS_DIR / "clipping-raw-texts.json"),
)
CURRENT_FILES = RUNTIME_FILES
DEFAULT_SQLITE_UPLOAD_CHUNK_BYTES = 20 * 1024 * 1024


class ArtifactStore:
    """Small Supabase Storage bridge for clipping runtime artifacts."""

    def __init__(self) -> None:
        self.url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        self.key = os.environ.get("SUPABASE_SERVICE_KEY", "")
        self.bucket = os.environ.get("SUPABASE_BUCKET", "documentos").strip() or "documentos"
        self.prefix = os.environ.get("CLIPPING_STORAGE_PREFIX", "clipping-project").strip().strip("/")
        self.enabled = bool(self.url and self.key and self.bucket and self.prefix)

    @property
    def writes_available(self) -> bool:
        return self.enabled or local_writes_allowed()

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "bucket": self.bucket if self.enabled else "",
            "prefix": self.prefix,
            "localWritesAllowed": local_writes_allowed(),
        }

    def _headers(self, content_type: str | None = None) -> dict[str, str]:
        headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}"}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _object_url(self, remote_path: str) -> str:
        safe_bucket = quote(self.bucket, safe="")
        safe_path = quote(remote_path.strip("/"), safe="/")
        return f"{self.url}/storage/v1/object/{safe_bucket}/{safe_path}"

    def _remote(self, relative_path: str) -> str:
        return f"{self.prefix}/current/{relative_path.strip('/')}"

    def download_current_artifacts(self) -> list[str]:
        if not self.enabled:
            return []
        downloaded: list[str] = []
        for relative, local_factory in RUNTIME_FILES:
            local_path = local_factory()
            if relative == "data/clipping.db":
                if self.download_gzip_file(self._remote(relative) + ".gz", local_path):
                    downloaded.append(relative)
                    continue
            if self.download_file(self._remote(relative), local_path):
                downloaded.append(relative)
        return downloaded

    def download_file(self, remote_path: str, local_path: Path) -> bool:
        if not self.enabled:
            return False
        try:
            response = requests.get(self._object_url(remote_path), headers=self._headers(), timeout=45)
        except requests.RequestException:
            return False
        if response.status_code == 404:
            return False
        if not response.ok:
            return False
        return write_artifact_payload(response.content, local_path)

    def upload_current_artifacts(self, *, manifest: dict[str, Any] | None = None, job_id: str | None = None) -> list[str]:
        uploaded: list[str] = []
        for relative, local_factory in RUNTIME_FILES:
            local_path = local_factory()
            if not local_path.is_file():
                continue
            if relative == "data/clipping.db":
                if self.upload_sqlite_snapshot(local_path, self._remote(relative) + ".gz"):
                    uploaded.append(relative + ".gz")
            elif self.upload_file(local_path, self._remote(relative)):
                uploaded.append(relative)
        if manifest and job_id:
            remote = f"{self.prefix}/runs/{job_id}.json"
            payload = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
            if self.upload_bytes(payload, remote, "application/json"):
                uploaded.append(f"runs/{job_id}.json")
        return uploaded

    def upload_database_checkpoint(
        self,
        *,
        manifest: dict[str, Any] | None = None,
        job_id: str | None = None,
    ) -> list[str]:
        uploaded: list[str] = []
        local_path = db_path()
        if local_path.is_file() and self.upload_sqlite_snapshot(local_path, self._remote("data/clipping.db") + ".gz"):
            uploaded.append("data/clipping.db.gz")
        if manifest and job_id:
            remote = f"{self.prefix}/runs/{job_id}.json"
            payload = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
            if self.upload_bytes(payload, remote, "application/json"):
                uploaded.append(f"runs/{job_id}.json")
        return uploaded

    def download_gzip_file(self, remote_path: str, local_path: Path) -> bool:
        if not self.enabled:
            return False
        manifest = self.download_json(self._sqlite_manifest_remote(remote_path))
        if manifest:
            mode = str(manifest.get("mode") or "").strip()
            if mode == "chunks":
                return self.download_chunked_gzip_file(manifest, local_path)
            if mode == "single":
                return self.download_single_gzip_file(remote_path, local_path)
            return False
        return self.download_single_gzip_file(remote_path, local_path)

    def download_single_gzip_file(self, remote_path: str, local_path: Path) -> bool:
        if not self.enabled:
            return False
        try:
            response = requests.get(self._object_url(remote_path), headers=self._headers(), timeout=45)
        except requests.RequestException:
            return False
        if response.status_code == 404:
            return False
        if not response.ok:
            return False
        return self.write_gzip_payload(response.content, local_path)

    def download_json(self, remote_path: str) -> dict[str, Any]:
        if not self.enabled:
            return {}
        try:
            response = requests.get(self._object_url(remote_path), headers=self._headers(), timeout=30)
        except requests.RequestException:
            return {}
        if response.status_code == 404 or not response.ok:
            return {}
        try:
            payload = response.json()
        except ValueError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def list_objects(self, path_prefix: str, *, limit: int = 1000, offset: int = 0) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        endpoint = f"{self.url}/storage/v1/object/list/{quote(self.bucket, safe='')}"
        body = {
            "prefix": path_prefix.strip("/"),
            "limit": max(1, min(limit, 1000)),
            "offset": max(0, offset),
            "sortBy": {"column": "updated_at", "order": "desc"},
        }
        try:
            response = requests.post(endpoint, headers=self._headers("application/json"), json=body, timeout=45)
        except requests.RequestException:
            return []
        if not response.ok:
            return []
        try:
            payload = response.json()
        except ValueError:
            return []
        return [row for row in payload if isinstance(row, dict)] if isinstance(payload, list) else []

    def list_objects_recursive(self, path_prefix: str, *, limit: int = 1000, max_depth: int = 6) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        objects: list[dict[str, Any]] = []
        queue: list[tuple[str, int]] = [(path_prefix.strip("/"), 0)]
        seen_prefixes: set[str] = set()
        seen_objects: set[str] = set()
        while queue and len(objects) < limit:
            prefix, depth = queue.pop(0)
            if prefix in seen_prefixes:
                continue
            seen_prefixes.add(prefix)
            offset = 0
            while len(objects) < limit:
                rows = self.list_objects(prefix, limit=min(1000, limit - len(objects)), offset=offset)
                if not rows:
                    break
                for row in rows:
                    remote_path = self._remote_from_list_row(prefix, row)
                    if not remote_path:
                        continue
                    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
                    is_file = bool(metadata) or bool(row.get("id")) or bool(row.get("updated_at") or row.get("updatedAt"))
                    if is_file:
                        if remote_path in seen_objects:
                            continue
                        seen_objects.add(remote_path)
                        objects.append(
                            {
                                "remotePath": remote_path,
                                "name": row.get("name"),
                                "updatedAt": row.get("updated_at") or row.get("updatedAt"),
                                "createdAt": row.get("created_at") or row.get("createdAt"),
                                "size": metadata.get("size") or row.get("size"),
                            }
                        )
                    elif depth < max_depth:
                        queue.append(remote_path)
                if len(rows) < 1000:
                    break
                offset += len(rows)
        return objects

    def _remote_from_list_row(self, prefix: str, row: dict[str, Any]) -> str:
        name = str(row.get("name") or "").strip("/")
        if not name:
            return ""
        clean_prefix = prefix.strip("/")
        if name == clean_prefix or name.startswith(clean_prefix + "/"):
            return name
        return f"{clean_prefix}/{name}"

    def remote_storage_report(self, *, limit: int = 100) -> dict[str, Any]:
        if not self.enabled:
            return {"enabled": False, "prefix": self.prefix, "bucket": ""}
        current = self.list_objects_recursive(f"{self.prefix}/current", limit=limit, max_depth=3)
        backups = self.list_objects_recursive(f"{self.prefix}/backups", limit=limit, max_depth=6)
        runs = self.list_objects_recursive(f"{self.prefix}/runs", limit=limit, max_depth=2)
        return {
            "enabled": True,
            "bucket": self.bucket,
            "prefix": self.prefix,
            "current": {"count": len(current), "objects": current[:limit]},
            "backups": {"count": len(backups), "objects": backups[:limit]},
            "runs": {"count": len(runs), "objects": runs[:limit]},
            "sqliteBackupCandidates": self.remote_sqlite_backup_candidates(objects=backups)[:limit],
        }

    def remote_sqlite_backup_candidates(self, *, objects: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        rows = objects if objects is not None else self.list_objects_recursive(f"{self.prefix}/backups", limit=1000, max_depth=6)
        candidates: dict[str, dict[str, Any]] = {}
        for row in rows:
            remote_path = str(row.get("remotePath") or "")
            if not remote_path or ".part" in remote_path:
                continue
            base = ""
            if remote_path.endswith("/data/clipping.db") or remote_path.endswith("/data/clipping.db.gz"):
                base = remote_path
            elif remote_path.endswith("/data/clipping.db.manifest.json"):
                base = remote_path[: -len(".manifest.json")]
            elif remote_path.endswith("/data/clipping.db.gz.manifest.json"):
                base = remote_path[: -len(".manifest.json")]
            if not base:
                continue
            current = candidates.get(base, {})
            updated = str(row.get("updatedAt") or current.get("updatedAt") or "")
            candidates[base] = {
                "remotePath": base,
                "updatedAt": updated,
                "size": row.get("size") or current.get("size"),
                "listedPath": remote_path,
            }
        return sorted(candidates.values(), key=lambda item: str(item.get("updatedAt") or ""), reverse=True)

    def restore_latest_remote_sqlite_backup(self, local_path: Path, *, limit: int = 1000) -> dict[str, Any]:
        checked: list[dict[str, Any]] = []
        candidates = self.remote_sqlite_backup_candidates()[:limit]
        for candidate in candidates:
            remote_path = str(candidate.get("remotePath") or "")
            if not remote_path:
                continue
            temp_name = ""
            try:
                local_path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(suffix=".db", dir=local_path.parent, delete=False) as temp:
                    temp_name = temp.name
                temp_path = Path(temp_name)
                ok = self.download_gzip_file(remote_path, temp_path)
                mode = "gzip"
                if not ok and not remote_path.endswith(".gz"):
                    ok = self.download_file(remote_path, temp_path)
                    mode = "raw"
                summary = sqlite_file_summary(temp_path) if ok else {"ok": False, "error": "download_failed"}
                item = {**candidate, "downloadMode": mode, "summary": summary}
                checked.append(item)
                if summary.get("ok") and int(summary.get("contentRows") or 0) > 0:
                    os.replace(temp_path, local_path)
                    temp_name = ""
                    remove_sqlite_sidecars(local_path)
                    return {"ok": True, "restored": item, "checked": checked}
            finally:
                if temp_name:
                    try:
                        Path(temp_name).unlink()
                    except OSError:
                        pass
        return {"ok": False, "checked": checked, "candidateCount": len(candidates)}

    def download_chunked_gzip_file(self, manifest: dict[str, Any], local_path: Path) -> bool:
        chunks = manifest.get("chunks")
        if not isinstance(chunks, list) or not chunks:
            return False
        gzip_name = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".db.gz", delete=False) as gzipped:
                gzip_name = gzipped.name
                for item in chunks:
                    chunk_path = str(item.get("path") or "") if isinstance(item, dict) else ""
                    if not chunk_path:
                        return False
                    response = requests.get(self._object_url(chunk_path), headers=self._headers(), timeout=60)
                    if response.status_code == 404 or not response.ok:
                        return False
                    gzipped.write(response.content)
            return self.write_gzip_file(Path(gzip_name), local_path)
        except (OSError, requests.RequestException):
            return False
        finally:
            if gzip_name:
                try:
                    Path(gzip_name).unlink()
                except OSError:
                    pass

    def write_gzip_payload(self, payload: bytes, local_path: Path) -> bool:
        gzip_name = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".db.gz", delete=False) as gzipped:
                gzip_name = gzipped.name
                gzipped.write(payload)
            return self.write_gzip_file(Path(gzip_name), local_path)
        except OSError:
            return False
        finally:
            if gzip_name:
                try:
                    Path(gzip_name).unlink()
                except OSError:
                    pass

    def write_gzip_file(self, gzip_path: Path, local_path: Path) -> bool:
        tmp_name = ""
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(suffix=local_path.suffix or ".tmp", dir=local_path.parent, delete=False) as tmp:
                tmp_name = tmp.name
            with gzip.open(gzip_path, "rb") as source, Path(tmp_name).open("wb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
            if local_path.suffix.lower() == ".db" and not sqlite_file_is_valid(Path(tmp_name)):
                return False
            os.replace(tmp_name, local_path)
            tmp_name = ""
            if local_path.suffix.lower() == ".db":
                remove_sqlite_sidecars(local_path)
        except (OSError, EOFError, zlib.error):
            return False
        finally:
            if tmp_name:
                try:
                    Path(tmp_name).unlink()
                except OSError:
                    pass
        return True

    def _sqlite_manifest_remote(self, remote_path: str) -> str:
        return remote_path.rstrip("/") + ".manifest.json"

    def sqlite_upload_chunk_bytes(self) -> int:
        raw = os.environ.get("CLIPPING_SQLITE_UPLOAD_CHUNK_BYTES", "").strip()
        try:
            value = int(raw) if raw else DEFAULT_SQLITE_UPLOAD_CHUNK_BYTES
        except ValueError:
            value = DEFAULT_SQLITE_UPLOAD_CHUNK_BYTES
        return max(1024 * 1024, value)

    def upload_sqlite_manifest(self, remote_path: str, manifest: dict[str, Any]) -> bool:
        payload = json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                **manifest,
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
        return self.upload_bytes(payload, self._sqlite_manifest_remote(remote_path), "application/json")

    def upload_chunked_file(self, local_path: Path, remote_path: str, *, content_type: str = "application/octet-stream") -> bool:
        if not self.enabled or not local_path.is_file():
            return False
        chunk_size = self.sqlite_upload_chunk_bytes()
        chunks: list[dict[str, Any]] = []
        try:
            with local_path.open("rb") as source:
                index = 0
                while True:
                    payload = source.read(chunk_size)
                    if not payload:
                        break
                    chunk_remote = f"{remote_path}.part{index:04d}"
                    if not self.upload_bytes(payload, chunk_remote, content_type):
                        return False
                    chunks.append({"path": chunk_remote, "size": len(payload)})
                    index += 1
        except OSError:
            return False
        if not chunks:
            return False
        return self.upload_sqlite_manifest(
            remote_path,
            {
                "mode": "chunks",
                "remote_path": remote_path,
                "size": local_path.stat().st_size,
                "chunk_size": chunk_size,
                "chunk_count": len(chunks),
                "chunks": chunks,
            },
        )

    def upload_sqlite_snapshot(self, local_path: Path, remote_path: str) -> bool:
        gz_path = sqlite_snapshot_gzip_file(local_path)
        if gz_path is None:
            return False
        try:
            if gz_path.stat().st_size <= self.sqlite_upload_chunk_bytes() and self.upload_path(gz_path, remote_path, "application/gzip", timeout=90):
                return self.upload_sqlite_manifest(
                    remote_path,
                    {
                        "mode": "single",
                        "remote_path": remote_path,
                        "size": gz_path.stat().st_size,
                    },
                )
            return self.upload_chunked_file(gz_path, remote_path, content_type="application/gzip")
        finally:
            try:
                gz_path.unlink()
            except OSError:
                pass

    def backup_current_artifacts(self, label: str) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe_label = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in label)[:48] or "backup"
        backup_dir = DATA_DIR / "backups" / f"{stamp}-{safe_label}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        for relative, local_factory in RUNTIME_FILES:
            local_path = local_factory()
            if local_path.is_file():
                target = backup_dir / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(local_path, target)

        if self.enabled:
            for path in backup_dir.rglob("*"):
                if path.is_file():
                    rel = path.relative_to(backup_dir).as_posix()
                    self.upload_file(path, f"{self.prefix}/backups/{backup_dir.name}/{rel}")
        return backup_dir

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        if not self.enabled:
            return False
        if local_path.suffix.lower() == ".db":
            return self.upload_sqlite_snapshot(local_path, remote_path)
        payload = local_path.read_bytes()
        content_type = _content_type(local_path)
        try:
            response = requests.post(
                self._object_url(remote_path),
                headers={**self._headers(content_type), "x-upsert": "true"},
                data=payload,
                timeout=60,
            )
        except requests.RequestException:
            return False
        return response.status_code in {200, 201}

    def upload_path(self, local_path: Path, remote_path: str, content_type: str, *, timeout: int = 60) -> bool:
        if not self.enabled:
            return False
        try:
            with local_path.open("rb") as handle:
                response = requests.post(
                    self._object_url(remote_path),
                    headers={**self._headers(content_type), "x-upsert": "true"},
                    data=handle,
                    timeout=timeout,
                )
        except (OSError, requests.RequestException):
            return False
        return response.status_code in {200, 201}

    def upload_bytes(self, payload: bytes, remote_path: str, content_type: str) -> bool:
        if not self.enabled:
            return False
        try:
            response = requests.post(
                self._object_url(remote_path),
                headers={**self._headers(content_type), "x-upsert": "true"},
                data=payload,
                timeout=30,
            )
        except requests.RequestException:
            return False
        return response.status_code in {200, 201}


def _content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".html":
        return "text/html; charset=utf-8"
    if suffix == ".css":
        return "text/css; charset=utf-8"
    if suffix == ".js":
        return "application/javascript; charset=utf-8"
    if suffix == ".json":
        return "application/json; charset=utf-8"
    if suffix == ".db":
        return "application/octet-stream"
    return "application/octet-stream"


def write_artifact_payload(payload: bytes, local_path: Path) -> bool:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if local_path.suffix.lower() != ".db":
        try:
            local_path.write_bytes(payload)
        except OSError:
            return False
        return True

    tmp_name = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", dir=local_path.parent, delete=False) as tmp:
            tmp_name = tmp.name
            tmp.write(payload)
        tmp_path = Path(tmp_name)
        if not sqlite_file_is_valid(tmp_path):
            return False
        os.replace(tmp_path, local_path)
        tmp_name = ""
        remove_sqlite_sidecars(local_path)
        return True
    except OSError:
        return False
    finally:
        if tmp_name:
            try:
                Path(tmp_name).unlink()
            except OSError:
                pass


def sqlite_file_is_valid(path: Path) -> bool:
    return bool(sqlite_file_summary(path).get("ok"))


def sqlite_file_summary(path: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {"ok": False}
    if not path.is_file():
        summary["error"] = "not_found"
        return summary
    try:
        with sqlite3.connect(path) as conn:
            summary["size_bytes"] = path.stat().st_size
            row = conn.execute("PRAGMA quick_check").fetchone()
            check = str(row[0]) if row else ""
            summary["quickCheck"] = check
            if check.lower() != "ok":
                summary["error"] = "quick_check_failed"
                return summary
            tables = {
                str(item[0])
                for item in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            }
            summary["tablesCount"] = len(tables)
            content_rows = 0
            for table in ("articles", "jobs", "job_events", "mentions", "stories"):
                if table not in tables:
                    continue
                count = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                summary[f"{table}Count"] = count
                content_rows += count
            summary["contentRows"] = content_rows
    except sqlite3.Error:
        summary["error"] = "sqlite_error"
        return summary
    except OSError:
        summary["error"] = "stat_error"
        return summary
    summary["ok"] = True
    return summary


def remove_sqlite_sidecars(path: Path) -> None:
    for suffix in ("-wal", "-shm"):
        try:
            Path(str(path) + suffix).unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass


def sqlite_snapshot_bytes(path: Path) -> bytes:
    """Return a consistent SQLite backup image, including uncheckpointed WAL."""
    if not path.is_file():
        return b""
    tmp_name = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_name = tmp.name
        with sqlite3.connect(path) as source, sqlite3.connect(tmp_name) as dest:
            source.execute("PRAGMA busy_timeout = 5000")
            source.backup(dest)
        return Path(tmp_name).read_bytes()
    except sqlite3.Error:
        return b""
    finally:
        if tmp_name:
            try:
                Path(tmp_name).unlink()
            except OSError:
                pass


def sqlite_snapshot_gzip_file(path: Path) -> Path | None:
    """Write a consistent gzipped SQLite snapshot to disk without large buffers."""
    if not path.is_file():
        return None
    snapshot_name = ""
    gzip_name = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as snapshot:
            snapshot_name = snapshot.name
        with sqlite3.connect(path) as source, sqlite3.connect(snapshot_name) as dest:
            source.execute("PRAGMA busy_timeout = 5000")
            source.backup(dest)
        with tempfile.NamedTemporaryFile(suffix=".db.gz", delete=False) as gzipped:
            gzip_name = gzipped.name
        with Path(snapshot_name).open("rb") as source_file, gzip.open(gzip_name, "wb", compresslevel=6) as gzip_file:
            shutil.copyfileobj(source_file, gzip_file, length=1024 * 1024)
        return Path(gzip_name)
    except (OSError, sqlite3.Error):
        if gzip_name:
            try:
                Path(gzip_name).unlink()
            except OSError:
                pass
        return None
    finally:
        if snapshot_name:
            try:
                Path(snapshot_name).unlink()
            except OSError:
                pass


artifact_store = ArtifactStore()
