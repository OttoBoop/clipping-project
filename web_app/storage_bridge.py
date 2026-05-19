from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import gzip
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
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(response.content)
        return True

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
        try:
            response = requests.get(self._object_url(remote_path), headers=self._headers(), timeout=45)
        except requests.RequestException:
            return False
        if response.status_code == 404:
            return False
        if not response.ok:
            return False
        try:
            payload = gzip.decompress(response.content)
        except OSError:
            return False
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(payload)
        return True

    def upload_sqlite_snapshot(self, local_path: Path, remote_path: str) -> bool:
        payload = sqlite_snapshot_bytes(local_path)
        if not payload:
            return False
        return self.upload_bytes(gzip.compress(payload, compresslevel=6), remote_path, "application/gzip")

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
        payload = local_path.read_bytes()
        if local_path.suffix.lower() == ".db":
            payload = sqlite_snapshot_bytes(local_path)
            if not payload:
                return False
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


artifact_store = ArtifactStore()
