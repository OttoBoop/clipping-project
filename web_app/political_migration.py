"""Read-only SQLite import with bounded batches and preserved legacy identifiers."""
from __future__ import annotations

from collections import defaultdict
import hashlib
from pathlib import Path
import sqlite3

from datetime import datetime, timezone
from .political_corpus import _json, _scope, parse_date

MIGRATION_VERSION = 2


def _identities(rows):
    """Count and hash ordered identities without loading the archive into memory."""
    digest = hashlib.sha256()
    count = 0
    for row in rows:
        values = list(row.values()) if isinstance(row, dict) else list(row)
        digest.update((_json(values) + "\n").encode())
        count += 1
    return count, digest.hexdigest()


def _checkpoint(progress):
    return int(progress["last_article_id"]) if progress and progress["validation"].get("migrationVersion") == MIGRATION_VERSION else 0


def _validate_source(progress, allowed, snapshot_sha256):
    validation = progress["validation"] if progress else {}
    prior_scope = validation.get("targetKeys")
    if prior_scope is not None and sorted(prior_scope) != sorted(allowed):
        raise ValueError("legacy_import_scope_changed_use_new_source_key")
    prior_digest = validation.get("snapshotSha256")
    if prior_digest and snapshot_sha256 and prior_digest != snapshot_sha256:
        raise ValueError("legacy_import_snapshot_changed_use_new_source_key")


def import_batch(service, sqlite_path, *, allowed_target_keys: list[str], source_key="legacy_clipping", batch_size=100,
                 snapshot_sha256="", remote_backup="") -> dict:
    allowed = _scope(allowed_target_keys)
    size = max(1, min(int(batch_size), 100))
    path = Path(sqlite_path).resolve(strict=True)
    service.ensure_schema()
    with service._connect() as conn:
        progress = conn.execute("SELECT * FROM political_import_progress WHERE source_key=%s", (source_key,)).fetchone()
    _validate_source(progress, allowed, snapshot_sha256)
    after = _checkpoint(progress)
    source = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    prepared = []
    try:
        tables = {row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"articles", "mentions", "stories", "story_articles"}.issubset(tables):
            raise ValueError("invalid_legacy_schema")
        rows = source.execute("SELECT * FROM articles WHERE id>? ORDER BY id LIMIT ?", (after, size)).fetchall()
        ceiling = source.execute("SELECT COALESCE(MAX(id),0) FROM articles").fetchone()[0]
        for row in rows:
            article = dict(row)
            mentions = [dict(item) for item in source.execute("SELECT * FROM mentions WHERE article_id=? ORDER BY id", (article["id"],))
                        if item["target_key"] in allowed]
            if not mentions:
                continue
            stories = [dict(item) for item in source.execute("""SELECT s.* FROM stories s JOIN story_articles sa ON sa.story_id=s.id
                WHERE sa.article_id=? ORDER BY s.id""", (article["id"],))]
            story_links = [dict(item) for item in source.execute("SELECT * FROM story_articles WHERE article_id=? ORDER BY story_id", (article["id"],))]
            classifications = defaultdict(list)
            for mention in mentions:
                if "classifications" not in tables:
                    continue
                classification = source.execute("SELECT * FROM classifications WHERE mention_id=?", (mention["id"],)).fetchone()
                if classification:
                    item = dict(classification)
                    if {"classification_categories", "categories"}.issubset(tables):
                        item["categories"] = [dict(category) for category in source.execute("""SELECT c.* FROM categories c
                            JOIN classification_categories cc ON cc.category_id=c.id WHERE cc.classification_id=? ORDER BY c.id""", (item["id"],))]
                    classifications[mention["target_key"]].append(item)
            body = str(article.get("full_text") or "")
            digest, key = service._store_text(body)
            prepared.append((article, mentions, stories, story_links, dict(classifications), digest, key, len(body)))
        last = rows[-1]["id"] if rows else after
        finished = last >= ceiling
        placeholders = ",".join("?" for _ in allowed)
        expected_articles = source.execute(f"SELECT COUNT(DISTINCT article_id) FROM mentions WHERE target_key IN ({placeholders})", allowed).fetchone()[0]
        expected_mentions = source.execute(f"SELECT COUNT(*) FROM mentions WHERE target_key IN ({placeholders})", allowed).fetchone()[0]
        expected_classifications = source.execute(f"""SELECT COUNT(*) FROM classifications c JOIN mentions m ON m.id=c.mention_id
            WHERE m.target_key IN ({placeholders})""", allowed).fetchone()[0] if "classifications" in tables else 0
        scoped_links = f"""FROM story_articles sa WHERE EXISTS
            (SELECT 1 FROM mentions m WHERE m.article_id=sa.article_id AND m.target_key IN ({placeholders}))"""
        expected_stories, expected_story_hash = _identities(source.execute(
            f"SELECT DISTINCT sa.story_id {scoped_links} ORDER BY sa.story_id", allowed))
        expected_links, expected_link_hash = _identities(source.execute(
            f"SELECT sa.story_id,sa.article_id {scoped_links} ORDER BY sa.story_id,sa.article_id", allowed))
    finally:
        source.close()
    imported = 0
    with service._connect() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("political-import:" + source_key,))
        existing = conn.execute("SELECT * FROM political_import_progress WHERE source_key=%s", (source_key,)).fetchone()
        _validate_source(existing, allowed, snapshot_sha256)
        # Preparation uploads immutable objects outside the database transaction.
        # Another importer may commit that batch meanwhile; never replay stale work
        # or replace a newer checkpoint/validation with the older prepared batch.
        if _checkpoint(existing) != after:
            return {"sourceKey": source_key, "cursor": existing["last_article_id"], "scanned": 0,
                    "imported": 0, "hasMore": not existing["completed"], "validation": existing["validation"]}
        for article, mentions, stories, story_links, classifications, digest, key, body_chars in prepared:
            original_article = {k: v for k, v in article.items() if k not in {"full_text", "raw_html"}}
            original_article.update({"text_object_key": key, "content_hash": digest,
                                     "raw_html_in_immutable_sqlite_snapshot": bool(article.get("raw_html"))})
            originals_to_keep = [("article", article["id"], original_article)]
            originals_to_keep.extend(("mention", item["id"], item) for item in mentions)
            originals_to_keep.extend(("story", item["id"], item) for item in stories)
            for values in classifications.values():
                originals_to_keep.extend(("classification", item["id"], item) for item in values)
            for entity, legacy_id, original in originals_to_keep:
                conn.execute("""INSERT INTO political_legacy_records(source_key,entity_type,legacy_id,payload)
                    VALUES (%s,%s,%s,%s::jsonb) ON CONFLICT DO NOTHING""", (source_key, entity, legacy_id, _json(original)))
            hits = [{"target_key": mention["target_key"], "target_name": mention["target_name"],
                     "keyword_matched": mention["keyword_matched"], "legacy_id": mention["id"]} for mention in mentions]
            url = str(article["url"] or "")
            if not url:
                raise ValueError("legacy_article_missing_url")
            story = stories[0] if stories else {}
            article_id = service._persist_article(conn, {"url": url, "title": article["title"],
                "source_key": "legacy:" + str(article.get("source_name") or "unknown"),
                "source_name": article.get("source_name") or "", "snippet": article.get("snippet") or "",
                "discovered_at": article.get("discovered_at"),
                "metadata": {"legacy_source": source_key, "legacy_metadata": article.get("metadata"),
                             "legacy_raw_html_retained_in_sqlite": bool(article.get("raw_html"))}}, hits,
                published=parse_date(article.get("published_at")), date_status="legacy_unverified",
                body_chars=body_chars, digest=digest, object_key=key, legacy_id=article["id"], summary=str(article.get("summary") or ""),
                story_key=f"legacy:{source_key}:{story['id']}" if story else "", story_title=str(story.get("title") or ""),
                story_summary=str(story.get("summary") or ""), legacy_story_id=story.get("id"))
            conn.execute("""UPDATE political_articles SET body_status=CASE WHEN body_chars>0 AND date_status='legacy_unverified'
                            THEN 'legacy_body' ELSE body_status END WHERE id=%s""", (article_id,))
            conn.execute("""INSERT INTO political_legacy_ids(source_key,entity_type,legacy_id,new_id) VALUES (%s,'article',%s,%s)
                            ON CONFLICT DO NOTHING""", (source_key, article["id"], article_id))
            for mention in mentions:
                conn.execute("""INSERT INTO political_legacy_ids(source_key,entity_type,legacy_id,new_id) VALUES (%s,'mention',%s,%s)
                                ON CONFLICT DO NOTHING""", (source_key, mention["id"], article_id))
            for story in stories:
                new_story = conn.execute("""INSERT INTO political_stories(story_key,title,summary,legacy_id,created_at,updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(story_key) DO UPDATE SET legacy_id=COALESCE(political_stories.legacy_id,EXCLUDED.legacy_id)
                    RETURNING id""", (f"legacy:{source_key}:{story['id']}", story["title"], story.get("summary") or "", story["id"],
                        parse_date(story.get("created_at")) or datetime.now(timezone.utc),
                        parse_date(story.get("updated_at")) or datetime.now(timezone.utc))).fetchone()
                conn.execute("INSERT INTO political_story_articles(article_id,story_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (article_id, new_story["id"]))
                conn.execute("""INSERT INTO political_legacy_ids(source_key,entity_type,legacy_id,new_id) VALUES (%s,'story',%s,%s)
                                ON CONFLICT DO NOTHING""", (source_key, story["id"], new_story["id"]))
                original_link = next(item for item in story_links if item["story_id"] == story["id"])
                conn.execute("""INSERT INTO political_legacy_story_articles(source_key,legacy_story_id,legacy_article_id,story_id,article_id,payload)
                    VALUES (%s,%s,%s,%s,%s,%s::jsonb) ON CONFLICT DO NOTHING""",
                    (source_key, story["id"], article["id"], new_story["id"], article_id, _json(original_link)))
            for target_key, originals in classifications.items():
                # All original records survive even if legacy duplicate mentions share one target.
                content = {**originals[-1], "categories": [item["name"] for item in originals[-1].get("categories", [])], "legacy_records": originals}
                latest = originals[-1]
                existing_classification = conn.execute("SELECT * FROM political_classifications WHERE article_id=%s AND target_key=%s", (article_id, target_key)).fetchone()
                if existing_classification and existing_classification["legacy_id"] != latest["id"]:
                    conn.execute("INSERT INTO political_classification_revisions(article_id,target_key,previous,updated_by) VALUES (%s,%s,%s::jsonb,'legacy_import')",
                                 (article_id, target_key, _json({"payload": content, "legacy_id": latest["id"]})))
                conn.execute("""INSERT INTO political_classifications(article_id,target_key,payload,updated_by,updated_at,legacy_id)
                    VALUES (%s,%s,%s::jsonb,%s,%s,%s) ON CONFLICT(article_id,target_key) DO NOTHING""",
                    (article_id, target_key, _json(content), latest.get("classified_by") or "legacy",
                     parse_date(latest.get("classified_at")) or datetime.now(timezone.utc), latest["id"]))
                for original in originals:
                    conn.execute("""INSERT INTO political_legacy_ids(source_key,entity_type,legacy_id,new_id) VALUES (%s,'classification',%s,%s)
                                    ON CONFLICT DO NOTHING""", (source_key, original["id"], article_id))
            imported += 1
        counts = {row["entity_type"]: int(row["n"]) for row in conn.execute("""SELECT entity_type,COUNT(*) AS n FROM political_legacy_ids
            WHERE source_key=%s GROUP BY entity_type""", (source_key,)).fetchall()}
        dangling = conn.execute("""SELECT COUNT(*) AS n FROM political_legacy_ids l LEFT JOIN political_articles a ON a.id=l.new_id
            WHERE l.source_key=%s AND l.entity_type='article' AND a.id IS NULL""", (source_key,)).fetchone()["n"]
        dangling_mentions = conn.execute("""SELECT COUNT(*) AS n FROM political_legacy_ids l
            LEFT JOIN political_legacy_records r ON (r.source_key,r.entity_type,r.legacy_id)=(l.source_key,l.entity_type,l.legacy_id)
            LEFT JOIN political_legacy_ids a ON a.source_key=l.source_key AND a.entity_type='article' AND a.legacy_id=(r.payload->>'article_id')::bigint
            LEFT JOIN political_mentions m ON m.article_id=l.new_id AND m.target_key=r.payload->>'target_key'
            WHERE l.source_key=%s AND l.entity_type='mention' AND (m.article_id IS NULL OR a.new_id IS DISTINCT FROM l.new_id)""", (source_key,)).fetchone()["n"]
        dangling_classifications = conn.execute("""SELECT COUNT(*) AS n FROM political_legacy_ids l
            LEFT JOIN political_legacy_records r ON (r.source_key,r.entity_type,r.legacy_id)=(l.source_key,l.entity_type,l.legacy_id)
            LEFT JOIN political_legacy_records mr ON mr.source_key=l.source_key AND mr.entity_type='mention' AND mr.legacy_id=(r.payload->>'mention_id')::bigint
            LEFT JOIN political_legacy_ids m ON (m.source_key,m.entity_type,m.legacy_id)=(mr.source_key,mr.entity_type,mr.legacy_id)
            LEFT JOIN political_classifications c ON c.article_id=l.new_id AND c.target_key=mr.payload->>'target_key'
            WHERE l.source_key=%s AND l.entity_type='classification' AND (c.article_id IS NULL OR m.new_id IS DISTINCT FROM l.new_id)""", (source_key,)).fetchone()["n"]
        dangling_stories = conn.execute("""SELECT COUNT(*) AS n FROM political_legacy_ids l LEFT JOIN political_stories s ON s.id=l.new_id
            WHERE l.source_key=%s AND l.entity_type='story' AND s.id IS NULL""", (source_key,)).fetchone()["n"]
        dangling_links = conn.execute("""SELECT COUNT(*) AS n FROM political_legacy_story_articles l
            LEFT JOIN political_legacy_ids a ON a.source_key=l.source_key AND a.entity_type='article' AND a.legacy_id=l.legacy_article_id
            LEFT JOIN political_legacy_ids s ON s.source_key=l.source_key AND s.entity_type='story' AND s.legacy_id=l.legacy_story_id
            LEFT JOIN political_story_articles sa ON sa.article_id=l.article_id AND sa.story_id=l.story_id
            WHERE l.source_key=%s AND (sa.article_id IS NULL OR a.new_id IS DISTINCT FROM l.article_id OR s.new_id IS DISTINCT FROM l.story_id
                OR (l.payload->>'article_id')::bigint IS DISTINCT FROM l.legacy_article_id
                OR (l.payload->>'story_id')::bigint IS DISTINCT FROM l.legacy_story_id)""", (source_key,)).fetchone()["n"]
        with conn.cursor(name="legacy_story_validation") as cursor:
            cursor.execute("SELECT legacy_id FROM political_legacy_ids WHERE source_key=%s AND entity_type='story' ORDER BY legacy_id", (source_key,))
            _, actual_story_hash = _identities(cursor)
        with conn.cursor(name="legacy_link_validation") as cursor:
            cursor.execute("SELECT legacy_story_id,legacy_article_id FROM political_legacy_story_articles WHERE source_key=%s ORDER BY legacy_story_id,legacy_article_id", (source_key,))
            counts["story_article"], actual_link_hash = _identities(cursor)
        prior_validation = existing["validation"] if existing else {}
        validation = {"migrationVersion": MIGRATION_VERSION, "targetKeys": sorted(allowed),
            "snapshotSha256": snapshot_sha256 or prior_validation.get("snapshotSha256", ""),
            "remoteBackup": remote_backup or prior_validation.get("remoteBackup", ""),
            "expectedArticles": expected_articles, "expectedMentions": expected_mentions,
            "expectedClassifications": expected_classifications, "expectedStories": expected_stories, "expectedStoryArticles": expected_links,
            "expectedStoryIdsHash": expected_story_hash, "actualStoryIdsHash": actual_story_hash,
            "expectedStoryLinksHash": expected_link_hash, "actualStoryLinksHash": actual_link_hash,
            "counts": counts, "danglingArticles": int(dangling), "danglingMentions": int(dangling_mentions),
            "danglingClassifications": int(dangling_classifications), "danglingStories": int(dangling_stories), "danglingStoryArticles": int(dangling_links),
            "ok": bool(finished and not any([dangling, dangling_mentions, dangling_classifications, dangling_stories, dangling_links]) and
                       counts.get("article", 0) == expected_articles and counts.get("mention", 0) == expected_mentions and
                       counts.get("classification", 0) == expected_classifications and counts.get("story", 0) == expected_stories and
                       counts["story_article"] == expected_links and actual_story_hash == expected_story_hash and actual_link_hash == expected_link_hash)}
        conn.execute("""INSERT INTO political_import_progress(source_key,last_article_id,completed,validation) VALUES (%s,%s,%s,%s::jsonb)
            ON CONFLICT(source_key) DO UPDATE SET last_article_id=EXCLUDED.last_article_id,
            completed=EXCLUDED.completed,validation=EXCLUDED.validation,updated_at=NOW()""", (source_key, last, finished, _json(validation)))
    return {"sourceKey": source_key, "cursor": last, "scanned": len(rows), "imported": imported,
            "hasMore": not finished, "validation": validation}
