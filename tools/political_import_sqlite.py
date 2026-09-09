#!/usr/bin/env python3
"""Import a legacy SQLite snapshot into the configured political PostgreSQL store."""
from __future__ import annotations

import argparse
from contextlib import closing
import gzip
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import shutil
import sys
import tempfile
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web_app.political_corpus import political_corpus


def prepare_snapshot(source: Path, destination: Path) -> dict:
    """Freeze SQLite+WAL consistently and reuse the same verified image on resume."""
    source = source.resolve(strict=True)
    destination = destination.resolve()
    if source == destination:
        raise ValueError("snapshot_must_differ_from_live_database")
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = destination.with_suffix(destination.suffix + ".json")
    if not destination.exists():
        fd, name = tempfile.mkstemp(prefix=".political-import-", suffix=".db", dir=destination.parent)
        os.close(fd)
        temporary = Path(name)
        try:
            with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as original:
                with closing(sqlite3.connect(temporary)) as snapshot:
                    original.backup(snapshot, pages=100)
                    snapshot.execute("PRAGMA journal_mode=DELETE")
                    if snapshot.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                        raise ValueError("snapshot_integrity_failed")
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
    wal = destination.with_name(destination.name + "-wal")
    if wal.exists() and wal.stat().st_size:
        raise ValueError("import_snapshot_changed")
    with closing(sqlite3.connect(destination.as_uri() + "?mode=ro", uri=True)) as snapshot:
        if snapshot.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("snapshot_integrity_failed")
        counts = {table: snapshot.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                  for table in ("articles", "mentions", "stories", "story_articles")}
    with destination.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    manifest = {"source": str(source), "snapshot": str(destination), "sha256": digest,
                "bytes": destination.stat().st_size, "integrity": "ok", "counts": counts}
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if previous.get("sha256") != digest or previous.get("source") != str(source):
            raise ValueError("import_snapshot_changed")
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def persist_snapshot_backup(service, manifest: dict) -> str:
    if not service.store.enabled:
        raise RuntimeError("political_backup_storage_not_configured")
    remote = f"{service.store.prefix}/political/import-backups/{manifest['sha256']}/{uuid.uuid4().hex}/legacy.sqlite.gz"
    # Fresh object generations keep interrupted/repeated uploads from replacing
    # an earlier backup. Compress the already-frozen bytes so the readback hash
    # verifies the exact input imported into PostgreSQL, including classifications.
    with tempfile.TemporaryDirectory(prefix="political-backup-") as temporary:
        compressed, restored = Path(temporary) / "snapshot.gz", Path(temporary) / "restored.db"
        with Path(manifest["snapshot"]).open("rb") as source, gzip.open(compressed, "wb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
        if not service.store.upload_chunked_file(compressed, remote, content_type="application/gzip"):
            raise RuntimeError("political_backup_upload_failed")
        if not service.store.download_gzip_file(remote, restored):
            raise RuntimeError("political_backup_readback_failed")
        with restored.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != manifest["sha256"]:
            raise RuntimeError("political_backup_digest_mismatch")
    if not service.store.upload_bytes(json.dumps(manifest).encode(), remote + ".source.json", "application/json"):
        raise RuntimeError("political_backup_manifest_upload_failed")
    return remote


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", required=True, type=Path)
    parser.add_argument("--target", action="append", help="Explicit target key to import; repeat for each target.")
    parser.add_argument("--all-political-targets", action="store_true", help="Import the roster and four original political targets, including archived records.")
    parser.add_argument("--source-key", default="legacy_clipping")
    parser.add_argument("--snapshot", type=Path, help="Verified backup reused on resume; defaults to data/backups/political_import/<source-key hash>.db.")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    targets = list(args.target or [])
    if args.all_political_targets:
        from web_app.db_admin import load_targets
        targets.extend(str(row["key"]) for row in load_targets() if row.get("political_roster_version") or row.get("key") in {
            "flavio_valle", "pedro_duarte", "pedro_angelito", "bernardo_rubiao"})
    if not targets:
        parser.error("--target or --all-political-targets is required")
    targets = list(dict.fromkeys(targets))
    backup = args.snapshot or Path(__file__).resolve().parents[1] / "data" / "backups" / "political_import" / (hashlib.sha256(args.source_key.encode()).hexdigest()[:16] + ".db")
    manifest = prepare_snapshot(args.sqlite, backup)
    remote = persist_snapshot_backup(political_corpus, manifest)
    print(json.dumps({"backup": manifest, "remoteBackup": remote}, ensure_ascii=False), flush=True)
    while True:
        result = political_corpus.import_sqlite(backup, allowed_target_keys=targets,
                                               source_key=args.source_key, batch_size=args.batch_size,
                                               snapshot_sha256=manifest["sha256"], remote_backup=remote)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if args.once or not result["hasMore"]:
            return 0 if result["hasMore"] or result["validation"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
