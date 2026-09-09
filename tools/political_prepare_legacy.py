#!/usr/bin/env python3
"""Append political associations to a distinct staging copy of a verified snapshot.

Never opens the live database for writing, changes the web write fence, starts the
application, downloads articles, or imports PostgreSQL. A default invocation does
one batch of at most 100 articles; --drain explicitly continues to the checkpoint
ceiling. Full stored bodies are streamed one article at a time through the existing
CitationMatcher and its alias/context rules. Stored extraction quality is not
re-verified here; live publisher re-extraction remains a subsequent step.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from dataclasses import asdict, fields, replace
from datetime import date, datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import time
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.matcher import CitationMatcher, Target, target_metadata

VERSION = "political_prepare_editorial_body_v2"
ZONE = ZoneInfo("America/Sao_Paulo")
PRESERVED_TABLES = ("articles", "mentions", "stories", "story_articles", "story_targets",
                    "classifications", "categories", "classification_categories")
REQUIRED_TABLES = {"articles", "mentions", "stories", "story_articles", "story_targets"}
FOOTER_MARKERS = {
    "temporealrj.com": [r"\bVoc[eê] pode gostar tamb[eé]m\b", r"\bCompartilhe este artigo\b",
                        r"\bArtigo Anterior\b", r"\bPr[oó]ximo artigo\b"],
    "agendadopoder.com.br": [r"\bCompartilhe isso:\s*Compartilhar no WhatsApp",
                              r"\bCurtir isso:\s*Curtir\s*Carregando"],
    "diariodorio.com": [r"\bReceba not[ií]cias no WhatsApp e e-mail\b"],
}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      default=lambda item: {"blobHex": item.hex()} if isinstance(item, bytes) else str(item))


def file_sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def local_day(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if not parsed.tzinfo:
            parsed = parsed.replace(tzinfo=ZONE)
        return parsed.astimezone(ZONE).date().isoformat()
    except (ValueError, TypeError, OverflowError):
        return None


def readonly(path):
    conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    return conn


def load_targets(path):
    raw = path.read_bytes()
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("roster_too_large")
    payload = json.loads(raw)
    rows = payload.get("targets") if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError("roster_requires_1_to_100_explicit_targets")
    allowed = {field.name for field in fields(Target)}
    targets = []
    for row in rows:
        if not isinstance(row, dict) or not re.fullmatch(r"[a-z0-9_]{1,100}", str(row.get("key") or "")):
            raise ValueError("invalid_target_key")
        if not (row.get("display_name") or row.get("label")):
            raise ValueError("target_name_required")
        target = {key: value for key, value in row.items() if key in allowed}
        target.update(target_metadata(row))
        targets.append(Target(**target))
    if len({target.key for target in targets}) != len(targets):
        raise ValueError("duplicate_target_key")
    return sorted(targets, key=lambda target: target.key)


def original_records(conn, bounds=None):
    """Stream hashes of original business rows, including all classifications."""
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not REQUIRED_TABLES <= tables:
        raise ValueError("legacy_schema_incomplete")
    result = {}
    for table in PRESERVED_TABLES:
        if table not in tables:
            continue
        maximum = (bounds[table]["maxRowid"] if bounds is not None
                   else conn.execute(f'SELECT COALESCE(MAX(rowid),0) FROM "{table}"').fetchone()[0])
        digest, count = hashlib.sha256(), 0
        for row in conn.execute(f'SELECT rowid AS __prepare_rowid,* FROM "{table}" WHERE rowid<=? ORDER BY rowid', (maximum,)):
            digest.update(encoded(dict(row)).encode() + b"\n")
            count += 1
        result[table] = {"maxRowid": maximum, "rows": count, "sha256": digest.hexdigest()}
    return result


def verify_originals(stage, expected):
    with closing(readonly(stage)) as conn:
        if original_records(conn, expected) != expected:
            raise ValueError("original_records_changed_in_staging_copy")


def prepare_stage(source, stage, expected_sha, recipe):
    if file_sha(source) != expected_sha:
        raise ValueError("source_snapshot_sha256_mismatch")
    wal = source.with_name(source.name + "-wal")
    if wal.exists() and wal.stat().st_size:
        raise ValueError("source_must_be_frozen_snapshot_without_live_wal")
    meta_path = stage.with_suffix(stage.suffix + ".prepare.json")
    if stage.exists():
        if not meta_path.is_file():
            raise ValueError("existing_staging_file_has_no_prepare_manifest")
        manifest = json.loads(meta_path.read_text())
        if manifest.get("recipe") != recipe or manifest.get("sourceSha256") != expected_sha or manifest.get("source") != str(source):
            raise ValueError("staging_recipe_or_source_changed_use_new_staging_path")
        verify_originals(stage, manifest["originalRecords"])
        return manifest
    if meta_path.exists():
        raise ValueError("staging_manifest_exists_without_database")
    with closing(readonly(source)) as conn:
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("source_snapshot_integrity_failed")
        originals = original_records(conn)
    stage.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation never overwrites an existing archive, including a racing
    # invocation. A partial copy after a crash cannot pass the manifest checks.
    descriptor = os.open(stage, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as target, source.open("rb") as origin:
        shutil.copyfileobj(origin, target, length=1024 * 1024)
        target.flush()
        os.fsync(target.fileno())
    if file_sha(stage) != expected_sha:
        raise ValueError("staging_initial_copy_sha256_mismatch")
    manifest = {"version": VERSION, "source": str(source), "sourceSha256": expected_sha,
                "staging": str(stage), "recipe": recipe, "originalRecords": originals,
                "createdAt": datetime.now(timezone.utc).isoformat()}
    with meta_path.open("x", encoding="utf-8") as output:
        output.write(encoded(manifest) + "\n")
        output.flush()
        os.fsync(output.fileno())
    return manifest


def clean_text(value):
    return html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))


def matching_fields(row):
    """Select match-only text; never rewrite the original stored article.

    Domain-specific footer literals were observed in the verified real archive.
    Generic words such as 'relacionados' are not used as article cut points.
    Without an editorial boundary, body-only claims require re-extraction.
    """
    title, snippet = clean_text(row["title"]), clean_text(row["snippet"])
    stored = clean_text(row["full_text"])
    raw_html = row["raw_html"] if "raw_html" in row.keys() else ""
    body, basis, boundary, trusted = stored, "stored_body_unconfirmed", "", False
    if raw_html:
        from web_app.political_discovery import extract_article
        extracted = extract_article(raw_html)
        if extracted["extraction_state"] == "full_text":
            body, basis, trusted = clean_text(extracted["full_text"]), "stored_html_article_container", True
    domain = (urlparse(row["url"]).hostname or "").lower().removeprefix("www.")
    markers = [match for pattern in FOOTER_MARKERS.get(domain, []) if (match := re.search(pattern, body, re.I))]
    if markers:
        marker = min(markers, key=lambda match: match.start())
        body, boundary, trusted = body[:marker.start()], marker.group(0), True
        basis += "+verified_template_footer"
    return {"metadata": title + " " + snippet, "body": title + " " + body,
            "raw": title + " " + stored, "trustedBoundary": trusted,
            "basis": basis, "boundary": boundary}


def assess_mentions(row, matcher, lexical_matcher):
    fields = matching_fields(row)
    by_key = lambda hits: {hit.target_key: hit for hit in hits}
    metadata = by_key(matcher.find_hits(fields["metadata"]))
    body = by_key(matcher.find_hits(fields["body"]))
    editorial_hints = by_key(lexical_matcher.find_hits(fields["body"]))
    raw_hints = by_key(lexical_matcher.find_hits(fields["raw"]))
    accepted = {**metadata, **body} if fields["trustedBoundary"] else metadata
    quarantined = []
    for key, hit in raw_hints.items():
        if key in accepted:
            continue
        if fields["trustedBoundary"] and key not in editorial_hints:
            reason = "outside_editorial_boundary"
        elif key not in body:
            reason = "matcher_context_not_satisfied"
        else:
            reason = "editorial_boundary_unconfirmed"
        quarantined.append({"targetKey": key, "keywordMatched": hit.keyword_matched,
                            "reason": reason, "basis": fields["basis"], "boundary": fields["boundary"]})
    return accepted, quarantined


def match_text(row):
    """Inspection helper: full editorial candidate text, without truncation."""
    return matching_fields(row)["body"]


def append_only_authorizer(action, table, column, database, trigger):
    if action == sqlite3.SQLITE_INSERT:
        return sqlite3.SQLITE_OK if table in {"mentions", "stories", "story_articles", "story_targets", "political_prepare_progress", "political_prepare_quarantine"} else sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_UPDATE:
        return sqlite3.SQLITE_OK if table == "political_prepare_progress" else sqlite3.SQLITE_DENY
    if action in {sqlite3.SQLITE_DELETE, sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_DROP_TABLE,
                  sqlite3.SQLITE_DROP_INDEX, sqlite3.SQLITE_DROP_TRIGGER, sqlite3.SQLITE_ATTACH,
                  sqlite3.SQLITE_DETACH, sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_CREATE_TRIGGER,
                  sqlite3.SQLITE_CREATE_INDEX}:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def review_batch(conn, matcher, lexical_matcher, checkpoint, recipe, *, batch_size, sample_limit):
    conn.execute("BEGIN IMMEDIATE")
    try:
        progress = conn.execute("SELECT * FROM political_prepare_progress WHERE checkpoint_key=?", (checkpoint,)).fetchone()
        cursor = int(progress["cursor"]) if progress else 0
        ceiling = int(progress["ceiling"]) if progress else int(conn.execute("SELECT COALESCE(MAX(id),0) FROM articles").fetchone()[0])
        ids = [row[0] for row in conn.execute("SELECT id FROM articles WHERE id>? AND id<=? ORDER BY id LIMIT ?", (cursor, ceiling, batch_size))]
        inserted = eligible = unknown = outside = quarantined_count = 0
        sample = []
        for article_id in ids:
            row = conn.execute("SELECT id,title,url,summary,snippet,full_text,raw_html,published_at FROM articles WHERE id=?", (article_id,)).fetchone()
            day = local_day(row["published_at"])
            if not recipe["allDates"]:
                if day is None:
                    unknown += 1
                    continue
                if not recipe["dateFrom"] <= day <= recipe["dateTo"]:
                    outside += 1
                    continue
            eligible += 1
            hits, quarantined = assess_mentions(row, matcher, lexical_matcher)
            for item in quarantined:
                if conn.execute("SELECT 1 FROM mentions WHERE article_id=? AND target_key=? LIMIT 1", (article_id, item["targetKey"])).fetchone():
                    continue
                changed = conn.execute("""INSERT OR IGNORE INTO political_prepare_quarantine
                    (checkpoint_key,article_id,target_key,url,reason,keyword_matched,basis,boundary)
                    VALUES (?,?,?,?,?,?,?,?)""", (checkpoint, article_id, item["targetKey"], row["url"], item["reason"],
                        item["keywordMatched"], item["basis"], item["boundary"]))
                quarantined_count += max(0, changed.rowcount)
            for key, hit in hits.items():
                if conn.execute("SELECT 1 FROM mentions WHERE article_id=? AND target_key=? LIMIT 1", (article_id, key)).fetchone():
                    continue
                conn.execute("""INSERT INTO mentions(article_id,target_key,target_name,keyword_matched,sentiment,sentiment_reason,context)
                    VALUES (?,?,?,?,'neutral','political_staging_full_body_review','')""", (article_id, key, hit.target_name, hit.keyword_matched))
                story_ids = [item[0] for item in conn.execute("SELECT story_id FROM story_articles WHERE article_id=? ORDER BY story_id", (article_id,))]
                if not story_ids:
                    now = datetime.now(timezone.utc).isoformat()
                    created = conn.execute("""INSERT INTO stories(title,summary,temperature,created_at,updated_at)
                        VALUES (?,?,34,?,?)""", (str(row["title"] or "Nova história")[:220], str(row["summary"] or row["snippet"] or row["title"] or "")[:800], now, now))
                    story_ids = [created.lastrowid]
                    conn.execute("INSERT INTO story_articles(story_id,article_id) VALUES (?,?)", (story_ids[0], article_id))
                for story_id in story_ids:
                    conn.execute("INSERT OR IGNORE INTO story_targets(story_id,target_key) VALUES (?,?)", (story_id, key))
                inserted += 1
                if len(sample) < sample_limit:
                    sample.append({"articleId": article_id, "targetKey": key, "keywordMatched": hit.keyword_matched, "publishedDay": day})
            cursor = article_id
        # Skipped date rows still advance the cursor, including a batch composed
        # entirely of older articles. The immutable source fixes the upper bound.
        cursor = ids[-1] if ids else cursor
        conn.execute("""INSERT INTO political_prepare_progress(checkpoint_key,cursor,ceiling,scanned,eligible,inserted,quarantined,unknown_dates,outside_window,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(checkpoint_key) DO UPDATE SET cursor=excluded.cursor,
            scanned=scanned+excluded.scanned,eligible=eligible+excluded.eligible,inserted=inserted+excluded.inserted,
            quarantined=quarantined+excluded.quarantined,
            unknown_dates=unknown_dates+excluded.unknown_dates,outside_window=outside_window+excluded.outside_window,updated_at=excluded.updated_at""",
            (checkpoint, cursor, ceiling, len(ids), eligible, inserted, quarantined_count, unknown, outside, datetime.now(timezone.utc).isoformat()))
        totals = dict(conn.execute("SELECT * FROM political_prepare_progress WHERE checkpoint_key=?", (checkpoint,)).fetchone())
        conn.commit()
        return {"checkpointKey": checkpoint, "cursor": cursor, "hasMore": cursor < ceiling,
                "scannedCount": len(ids), "eligibleCount": eligible, "mentionsInserted": inserted,
                "quarantinedAssociations": quarantined_count,
                "unknownPublicationDates": unknown, "outsideWindow": outside, "sample": sample,
                "sampleTruncated": inserted > len(sample), "totals": totals}
    except Exception:
        conn.rollback()
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", required=True, type=Path, help="Distinct staging database to create or resume; never the live archive.")
    parser.add_argument("--source-snapshot", required=True, type=Path, help="Previously verified frozen SQLite backup, read-only.")
    parser.add_argument("--source-sha256", required=True, help="Expected SHA-256 from the verified source backup.")
    parser.add_argument("--roster-json", required=True, type=Path)
    parser.add_argument("--date-from", type=date.fromisoformat, default=date(2026, 6, 1))
    parser.add_argument("--date-to", type=date.fromisoformat, default=datetime.now(ZONE).date())
    parser.add_argument("--all-dates", action="store_true", help="Explicitly review older/unknown-date articles too; originals always survive.")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--sample-limit", type=int, default=20)
    parser.add_argument("--drain", action="store_true", help="Continue 100-article transactions until this frozen snapshot is fully reviewed.")
    args = parser.parse_args(argv)
    if not 1 <= args.batch_size <= 100 or not 0 <= args.sample_limit <= 100:
        parser.error("batch-size must be 1..100 and sample-limit 0..100")
    if args.date_from > args.date_to or not re.fullmatch(r"[a-fA-F0-9]{64}", args.source_sha256):
        parser.error("valid date window and source-sha256 are required")
    source = args.source_snapshot.expanduser().resolve(strict=True)
    stage = args.sqlite.expanduser().resolve()
    configured_live = Path(os.environ.get("CLIPPING_DB_PATH") or ROOT / "data/clipping.db").expanduser().resolve()
    if stage in {source, configured_live, (ROOT / "data/clipping.db").resolve()}:
        parser.error("sqlite must be distinct from the source snapshot and configured live database")
    targets = load_targets(args.roster_json.expanduser().resolve(strict=True))
    recipe = {"version": VERSION, "targets": [asdict(target) for target in targets], "allDates": args.all_dates,
              "dateFrom": args.date_from.isoformat(), "dateTo": args.date_to.isoformat(), "timezone": str(ZONE)}
    checkpoint = hashlib.sha256(encoded(recipe).encode()).hexdigest()
    started = time.monotonic()
    manifest = prepare_stage(source, stage, args.source_sha256.lower(), recipe)
    print(encoded({"kind": "staging_prepared", "source": str(source), "sourceSha256": manifest["sourceSha256"],
                   "staging": str(stage), "targetCount": len(targets), "checkpointKey": checkpoint,
                   "liveWriteFenceUnchanged": True, "fullStoredBodyMatching": True,
                   "originalsVerifiedBeforeRun": True}), flush=True)
    matcher = CitationMatcher(targets, exact_names_only=True)
    lexical_matcher = CitationMatcher([replace(target, match_context={}) for target in targets], exact_names_only=True)
    with closing(sqlite3.connect(stage, timeout=15)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("""CREATE TABLE IF NOT EXISTS political_prepare_progress(
            checkpoint_key TEXT PRIMARY KEY,cursor INTEGER NOT NULL,ceiling INTEGER NOT NULL,
            scanned INTEGER NOT NULL,eligible INTEGER NOT NULL,inserted INTEGER NOT NULL,quarantined INTEGER NOT NULL,
            unknown_dates INTEGER NOT NULL,outside_window INTEGER NOT NULL,updated_at TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS political_prepare_quarantine(
            checkpoint_key TEXT NOT NULL,article_id INTEGER NOT NULL,target_key TEXT NOT NULL,url TEXT NOT NULL,
            reason TEXT NOT NULL,keyword_matched TEXT NOT NULL,basis TEXT NOT NULL,boundary TEXT NOT NULL,
            PRIMARY KEY(checkpoint_key,article_id,target_key))""")
        conn.commit()
        conn.set_authorizer(append_only_authorizer)
        while True:
            result = review_batch(conn, matcher, lexical_matcher, checkpoint, recipe, batch_size=args.batch_size, sample_limit=args.sample_limit)
            print(encoded({"kind": "batch", **result}), flush=True)
            if not args.drain or not result["hasMore"]:
                break
    verify_originals(stage, manifest["originalRecords"])
    quarantine_path = stage.with_suffix(stage.suffix + ".reextract.jsonl")
    with closing(readonly(stage)) as conn, quarantine_path.open("w", encoding="utf-8") as output:
        for row in conn.execute("SELECT * FROM political_prepare_quarantine WHERE checkpoint_key=? ORDER BY article_id,target_key", (checkpoint,)):
            output.write(encoded(dict(row)) + "\n")
    if file_sha(source) != manifest["sourceSha256"]:
        raise ValueError("source_snapshot_changed_during_review")
    print(encoded({"kind": "verification", "originalRecordsPreserved": True, "sourceSnapshotUnchanged": True,
                   "hasMore": result["hasMore"], "complete": not result["hasMore"], "totals": result["totals"],
                   "seconds": round(time.monotonic() - started, 3), "requiresFinalFrozenSnapshotAndVerifiedBackup": True,
                   "quarantineReport": str(quarantine_path), "quarantinedAssociations": result["totals"]["quarantined"],
                   "limitations": ["Stored article extraction and publication dates are not re-verified against publishers.",
                                   "Known template footers are excluded; uncertain body-only/context matches are quarantined for re-extraction.",
                                   "This staging review performs no live collection or PostgreSQL import."]}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
