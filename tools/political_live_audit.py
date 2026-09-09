#!/usr/bin/env python3
"""Bounded, read-only audit of the actual legacy SQLite political archive.

Standard library only. No application imports, schema initialization, collection,
object-storage access, fixture data, or file output. Run with python -B. Supply the
versioned roster as a JSON path or --roster-json - for stdin. Article bodies and
classification contents never appear in the JSON report.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
from datetime import date, datetime, timezone
import hashlib
from itertools import groupby
import json
from pathlib import Path
import re
import sqlite3
import sys
import time
import unicodedata
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from zoneinfo import ZoneInfo


ZONE = ZoneInfo("America/Sao_Paulo")
BODY_SCAN_LIMIT = 2 * 1024 * 1024
ROSTER_LIMIT = 2 * 1024 * 1024
GROUP_LIMIT = 500
TRACKING = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "fbclid", "gclid", "gclsrc", "dclid", "msclkid", "ref", "ref_src",
            "ref_url", "_ga", "mc_cid", "mc_eid"}


def rj_day(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if not parsed.tzinfo:
            parsed = parsed.replace(tzinfo=ZONE)
        return parsed.astimezone(ZONE).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def normalize_url(value):
    """Same tracking/query normalization used by the pipeline, without imports."""
    value = re.sub(r"^(https?:)/([^/])", r"\1//\2", str(value or "").strip(), flags=re.I)
    if not value:
        return ""
    try:
        parsed = urlparse(value)
        query = {key: vals for key, vals in parse_qs(parsed.query, keep_blank_values=False).items()
                 if key.lower() not in TRACKING}
        return urlunparse((parsed.scheme.lower(), (parsed.hostname or "").lower(),
                          parsed.path.rstrip("/") or "/", "", urlencode(sorted(query.items()), doseq=True), ""))
    except ValueError:
        return value.lower()


def hostname(value):
    try:
        host = (urlparse(str(value or "")).hostname or "").lower().rstrip(".")
        return host[4:] if host.startswith("www.") else host
    except ValueError:
        return ""


def normalized_text(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join("".join(char for char in value if not unicodedata.combining(char)).casefold().split())


def load_roster(argument):
    if argument == "-":
        raw = sys.stdin.buffer.read(ROSTER_LIMIT + 1)
    else:
        with Path(argument).open("rb") as stream:
            raw = stream.read(ROSTER_LIMIT + 1)
    if len(raw) > ROSTER_LIMIT:
        raise ValueError("roster_too_large")
    value = json.loads(raw)
    rows = value.get("targets") if isinstance(value, dict) else value
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError("roster_requires_1_to_100_people")
    result = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("roster_requires_key_and_label_objects")
        key = str(row.get("key") or "").strip()
        label = str(row.get("display_name") or row.get("label") or "").strip()
        if not re.fullmatch(r"[a-z0-9_]{1,100}", key) or not 2 <= len(label) <= 200:
            raise ValueError("invalid_roster_person")
        result.append({"key": key, "label": label})
    if len({row["key"] for row in result}) != len(result):
        raise ValueError("duplicate_roster_key")
    return result


def sample_append(values, article_id, limit):
    if len(values) < limit:
        values.append(article_id)


def new_counts():
    return {"uniqueArticles": 0, "bodyCharsAtLeast200_UNVERIFIED": 0,
            "noStoredBody": 0, "shortStoredBody": 0, "bodyEqualsSnippet": 0,
            "googleWrapperUrls": 0, "articleIdSample": []}


def count_article(counts, row, sample_limit):
    counts["uniqueArticles"] += 1
    chars = int(row["body_chars"] or 0)
    counts["bodyCharsAtLeast200_UNVERIFIED"] += int(chars >= 200)
    counts["noStoredBody"] += int(chars == 0)
    counts["shortStoredBody"] += int(0 < chars < 200)
    counts["bodyEqualsSnippet"] += int(row["body_equals_snippet"] or 0)
    counts["googleWrapperUrls"] += int(hostname(row["url"]) == "news.google.com")
    sample_append(counts["articleIdSample"], row["id"], sample_limit)


def finalize_counts(counts):
    counts["articleIdSampleTruncated"] = counts["uniqueArticles"] > len(counts["articleIdSample"])
    return counts


def hash_record(digest, table, row):
    def binary(value):
        if isinstance(value, bytes):
            return {"sqliteBlobHex": value.hex()}
        raise TypeError("unsupported_sqlite_value")
    payload = json.dumps({"table": table, "row": row}, ensure_ascii=False,
                         sort_keys=True, separators=(",", ":"), default=binary)
    digest.update(payload.encode("utf-8") + b"\n")


def audit(args, roster):
    path = args.sqlite.expanduser().resolve(strict=True)
    if not path.is_file():
        raise ValueError("sqlite_path_is_not_a_file")
    start, end = args.date_from.isoformat(), args.date_to.isoformat()
    keys = [row["key"] for row in roster]
    placeholders = ",".join("?" for _ in keys)
    deadline = time.monotonic() + args.max_seconds
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=15)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        conn.create_function("rj_day", 1, rj_day, deterministic=True)
        conn.create_function("canonical_url", 1, normalize_url, deterministic=True)
        conn.set_progress_handler(lambda: int(time.monotonic() >= deadline), 10000)
        conn.execute("BEGIN")
        tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"articles", "mentions"} <= tables:
            raise ValueError("required_legacy_tables_missing")
        columns = {table: {row["name"] for row in conn.execute(f'PRAGMA table_info("{table}")')}
                   for table in ("articles", "mentions", "classifications", "categories", "classification_categories",
                                 "jobs", "job_source_runs", "job_candidate_audit") if table in tables}
        if not {"id", "url", "title", "source_name", "published_at", "full_text", "snippet"} <= columns["articles"]:
            raise ValueError("required_article_columns_missing")
        if not {"id", "article_id", "target_key"} <= columns["mentions"]:
            raise ValueError("required_mention_columns_missing")
        report = {"ok": True, "recordedAt": datetime.now(timezone.utc).isoformat(),
                  "database": str(path), "dateFrom": start, "dateTo": end, "timezone": str(ZONE),
                  "readOnly": True, "consistentReadTransaction": True,
                  "journalMode": conn.execute("PRAGMA journal_mode").fetchone()[0],
                  "rosterCount": len(roster), "sampleLimit": args.sample_limit,
                  "publicationDatesNeverReplacedByDiscoveryDates": True,
                  "bodyLengthDoesNotVerifyArticleExtraction": True,
                  "tableCounts": {}, "archiveInDateWindow": new_counts(),
                  "archiveUnknownPublicationDate": new_counts(), "selectedScopeAllTime": new_counts(),
                  "selectedScopeInDateWindow": new_counts(), "selectedScopeUnknownPublicationDate": new_counts()}
        for table in ("articles", "mentions", "stories", "story_articles", "classifications", "categories", "classification_categories"):
            report["tableCounts"][table] = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] if table in tables else None
        people = {row["key"]: {**row, "allTime": new_counts(), "inDateWindow": new_counts(), "unknownPublicationDate": new_counts(),
                  "storedMentionRowsAllTime": 0, "storedMentionRowsInDateWindow": 0,
                  "newLabelMatchCandidates": {"inDateWindow": 0, "unknownPublicationDate": 0,
                      "bodyMatch": 0, "titleOnlyMatch": 0, "articleIdSample": []},
                  "dailySavedArticles": {}} for row in roster}
        patterns = {row["key"]: re.compile(r"(?<!\w)" + re.escape(normalized_text(row["label"])) + r"(?!\w)") for row in roster}
        publishers = {}
        publisher_overflow = new_counts()
        daily_overflow = 0
        body_scan_truncated = 0
        mentions = conn.execute(f"SELECT article_id,target_key FROM mentions WHERE target_key IN ({placeholders}) ORDER BY article_id,id", keys)
        grouped_mentions = ((article_id, Counter(row["target_key"] for row in rows))
                            for article_id, rows in groupby(mentions, key=lambda row: row["article_id"]))
        current_mentions = next(grouped_mentions, None)
        for row in conn.execute("""SELECT id,url,title,source_name,published_at,
            length(trim(coalesce(full_text,''))) AS body_chars,
            CASE WHEN trim(coalesce(full_text,''))<>'' AND trim(full_text)=trim(coalesce(snippet,'')) THEN 1 ELSE 0 END AS body_equals_snippet,
            substr(full_text,1,?) AS body_for_inspection FROM articles ORDER BY id""", (BODY_SCAN_LIMIT,)):
            if time.monotonic() >= deadline:
                raise TimeoutError("audit_deadline_exceeded")
            while current_mentions and current_mentions[0] < row["id"]:
                current_mentions = next(grouped_mentions, None)
            associated = current_mentions[1] if current_mentions and current_mentions[0] == row["id"] else {}
            day = rj_day(row["published_at"])
            in_window = day is not None and start <= day <= end
            if in_window:
                count_article(report["archiveInDateWindow"], row, args.sample_limit)
            elif day is None:
                count_article(report["archiveUnknownPublicationDate"], row, args.sample_limit)
            if associated:
                count_article(report["selectedScopeAllTime"], row, args.sample_limit)
                if in_window:
                    count_article(report["selectedScopeInDateWindow"], row, args.sample_limit)
                elif day is None:
                    count_article(report["selectedScopeUnknownPublicationDate"], row, args.sample_limit)
                for key, mention_count in associated.items():
                    person = people[key]
                    count_article(person["allTime"], row, args.sample_limit)
                    person["storedMentionRowsAllTime"] += mention_count
                    if in_window:
                        count_article(person["inDateWindow"], row, args.sample_limit)
                        person["storedMentionRowsInDateWindow"] += mention_count
                        if day in person["dailySavedArticles"] or len(person["dailySavedArticles"]) < GROUP_LIMIT:
                            person["dailySavedArticles"][day] = person["dailySavedArticles"].get(day, 0) + 1
                        else:
                            daily_overflow += 1
                    elif day is None:
                        count_article(person["unknownPublicationDate"], row, args.sample_limit)
                if in_window or day is None:
                    publisher_key = (hostname(row["url"]), str(row["source_name"] or "")[:200])
                    if publisher_key not in publishers and len(publishers) < GROUP_LIMIT:
                        publishers[publisher_key] = {"hostname": publisher_key[0], "storedSource": publisher_key[1],
                            "inDateWindow": new_counts(), "unknownPublicationDate": new_counts()}
                    if publisher_key in publishers:
                        count_article(publishers[publisher_key]["inDateWindow" if in_window else "unknownPublicationDate"], row, args.sample_limit)
                    else:
                        count_article(publisher_overflow, row, args.sample_limit)
            if in_window or day is None:
                body_scan_truncated += int(row["body_chars"] > BODY_SCAN_LIMIT)
                body = normalized_text(row["body_for_inspection"])
                title = normalized_text(str(row["title"] or "")[:20000])
                for key, pattern in patterns.items():
                    if key in associated:
                        continue
                    body_match = bool(pattern.search(body))
                    title_match = bool(pattern.search(title))
                    if body_match or title_match:
                        finding = people[key]["newLabelMatchCandidates"]
                        finding["inDateWindow" if in_window else "unknownPublicationDate"] += 1
                        finding["bodyMatch" if body_match else "titleOnlyMatch"] += 1
                        sample_append(finding["articleIdSample"], row["id"], args.sample_limit)
        report["perPerson"] = list(people.values())
        report["perPublisher"] = sorted(publishers.values(), key=lambda row: (row["hostname"], row["storedSource"]))
        report["publisherGroupsOverflow"] = finalize_counts(publisher_overflow)
        report["dailyGroupsOverflowAssociations"] = daily_overflow
        report["missingAssociationInspection"] = {
            "method": "accent_insensitive_whole_phrase_roster_label_only",
            "requiresHumanReview": True, "doesNotVerifyEditorialBodyOrResolveAmbiguousNames": True,
            "includesUnknownPublicationDatesSeparately": True, "bodyScanLimitChars": BODY_SCAN_LIMIT,
            "articlesWithTruncatedBodyInspection": body_scan_truncated,
            "note": "Candidates have no existing mention for that roster key. Aliases and broader context rules are not applied."}
        for person in report["perPerson"]:
            for field in ("allTime", "inDateWindow", "unknownPublicationDate"):
                finalize_counts(person[field])
            candidate = person["newLabelMatchCandidates"]
            candidate["articleIdSampleTruncated"] = candidate["bodyMatch"] + candidate["titleOnlyMatch"] > len(candidate["articleIdSample"])
        for publisher in report["perPublisher"]:
            finalize_counts(publisher["inDateWindow"])
            finalize_counts(publisher["unknownPublicationDate"])
        for field in ("archiveInDateWindow", "archiveUnknownPublicationDate", "selectedScopeAllTime", "selectedScopeInDateWindow", "selectedScopeUnknownPublicationDate"):
            finalize_counts(report[field])
        report["associations"] = {
            "storedMentionRowsAllTime": sum(person["storedMentionRowsAllTime"] for person in people.values()),
            "storedMentionRowsInDateWindow": sum(person["storedMentionRowsInDateWindow"] for person in people.values()),
            "uniqueArticlePersonPairsAllTime": sum(person["allTime"]["uniqueArticles"] for person in people.values()),
            "uniqueArticlePersonPairsInDateWindow": sum(person["inDateWindow"]["uniqueArticles"] for person in people.values())}
        report["integrity"] = relationship_checks(conn, tables, placeholders, keys)
        scoped = f"EXISTS (SELECT 1 FROM mentions m WHERE m.article_id=a.id AND m.target_key IN ({placeholders}))"
        duplicate_where = f"{scoped} AND rj_day(a.published_at) BETWEEN ? AND ?"
        duplicates = f"SELECT canonical_url(a.url) AS canonicalUrl,COUNT(*) AS n,MIN(a.id) AS firstId,MAX(a.id) AS lastId FROM articles a WHERE {duplicate_where} GROUP BY canonical_url(a.url) HAVING COUNT(*)>1"
        params = keys + [start, end]
        totals = conn.execute(f"SELECT COUNT(*) AS groups,coalesce(SUM(n-1),0) AS extraRows FROM ({duplicates})", params).fetchone()
        duplicate_samples = []
        for row in conn.execute(f"{duplicates} ORDER BY n DESC,firstId LIMIT ?", params + [args.sample_limit]):
            duplicate_samples.append({"canonicalUrlSha256": hashlib.sha256(row["canonicalUrl"].encode()).hexdigest(),
                                      "hostname": hostname(row["canonicalUrl"]), "n": row["n"],
                                      "firstId": row["firstId"], "lastId": row["lastId"]})
        report["canonicalUrlDuplicatesInSelectedDateWindow"] = {**dict(totals), "samples": duplicate_samples,
            "samplesTruncated": totals["groups"] > len(duplicate_samples),
            "doesNotResolveGoogleWrappersOrMergeSyndicatedArticles": True}
        report["humanClassifications"] = classification_digest(conn, tables, columns, placeholders, keys, start, end)
        report["latestJobs"] = latest_jobs(conn, tables, columns, placeholders, keys)
        report["completedAt"] = datetime.now(timezone.utc).isoformat()
        conn.rollback()
    return report


def relationship_checks(conn, tables, placeholders, keys):
    checks = {}
    relations = [("mentionsWithoutArticle", "mentions", "article_id", "articles", "id"),
                 ("storyLinksWithoutArticle", "story_articles", "article_id", "articles", "id"),
                 ("storyLinksWithoutStory", "story_articles", "story_id", "stories", "id"),
                 ("classificationsWithoutMention", "classifications", "mention_id", "mentions", "id"),
                 ("categoryLinksWithoutClassification", "classification_categories", "classification_id", "classifications", "id"),
                 ("categoryLinksWithoutCategory", "classification_categories", "category_id", "categories", "id"),
                 ("storyTargetsWithoutStory", "story_targets", "story_id", "stories", "id")]
    for label, child, child_key, parent, parent_key in relations:
        checks[label] = conn.execute(f"SELECT COUNT(*) FROM {child} c LEFT JOIN {parent} p ON p.{parent_key}=c.{child_key} WHERE p.{parent_key} IS NULL").fetchone()[0] if {child, parent} <= tables else None
    checks["duplicateSelectedMentionPairs"] = conn.execute(f"""SELECT COUNT(*) FROM
        (SELECT article_id,target_key FROM mentions WHERE target_key IN ({placeholders})
         GROUP BY article_id,target_key HAVING COUNT(*)>1)""", keys).fetchone()[0]
    if "story_articles" in tables:
        checks["selectedArticlesWithoutStory"] = conn.execute(f"""SELECT COUNT(*) FROM articles a WHERE
            EXISTS(SELECT 1 FROM mentions m WHERE m.article_id=a.id AND m.target_key IN ({placeholders})) AND
            NOT EXISTS(SELECT 1 FROM story_articles sa WHERE sa.article_id=a.id)""", keys).fetchone()[0]
    return {"scope": "orphan checks cover the whole archive; duplicate mentions and missing stories cover selected people", **checks}


def classification_digest(conn, tables, columns, placeholders, keys, start, end):
    if "classifications" not in tables:
        return {"available": False}
    human = "coalesce(c.ai_generated,0)=0" if "ai_generated" in columns["classifications"] else "1=1"
    clause = f"m.target_key IN ({placeholders}) AND {human}"
    all_digest, window_digest = hashlib.sha256(), hashlib.sha256()
    counts = {"classificationsAllTime": 0, "classificationsInDateWindow": 0,
              "categoryLinksAllTime": 0, "categoryLinksInDateWindow": 0,
              "categoriesAllTime": 0, "categoriesInDateWindow": 0}
    for row in conn.execute(f"""SELECT c.*,m.target_key AS audit_target_key,m.article_id AS audit_article_id,
        a.published_at AS audit_published_at FROM classifications c JOIN mentions m ON m.id=c.mention_id
        LEFT JOIN articles a ON a.id=m.article_id WHERE {clause} ORDER BY c.id""", keys):
        original = dict(row)
        day = rj_day(original.pop("audit_published_at"))
        hash_record(all_digest, "classifications_with_target_and_article", original)
        counts["classificationsAllTime"] += 1
        if day is not None and start <= day <= end:
            hash_record(window_digest, "classifications_with_target_and_article", original)
            counts["classificationsInDateWindow"] += 1
    if "classification_categories" in tables:
        for row in conn.execute(f"""SELECT cc.*,a.published_at AS audit_published_at FROM classification_categories cc
            JOIN classifications c ON c.id=cc.classification_id JOIN mentions m ON m.id=c.mention_id
            LEFT JOIN articles a ON a.id=m.article_id WHERE {clause} ORDER BY cc.classification_id,cc.category_id""", keys):
            original = dict(row)
            day = rj_day(original.pop("audit_published_at"))
            hash_record(all_digest, "classification_categories", original)
            counts["categoryLinksAllTime"] += 1
            if day is not None and start <= day <= end:
                hash_record(window_digest, "classification_categories", original)
                counts["categoryLinksInDateWindow"] += 1
        if "categories" in tables:
            category_scope = f"""SELECT cc.category_id FROM classification_categories cc JOIN classifications c ON c.id=cc.classification_id
                JOIN mentions m ON m.id=c.mention_id LEFT JOIN articles a ON a.id=m.article_id WHERE {clause}"""
            for suffix, digest, field, params in [("", all_digest, "categoriesAllTime", keys),
                (" AND rj_day(a.published_at) BETWEEN ? AND ?", window_digest, "categoriesInDateWindow", keys + [start, end])]:
                for row in conn.execute(f"SELECT * FROM categories WHERE id IN ({category_scope}{suffix}) ORDER BY id", params):
                    hash_record(digest, "categories", dict(row))
                    counts[field] += 1
    return {"available": True, "definition": "ai_generated=0 or NULL; original classification rows, article/target bindings, category links and category records",
            "digestFormat": "sha256 of sorted-key compact UTF-8 JSON records plus newline; ordered by original IDs; tables in classification/link/category order",
            "allTimeSha256": all_digest.hexdigest(), "dateWindowSha256": window_digest.hexdigest(), **counts}


def latest_jobs(conn, tables, columns, placeholders, keys):
    result = {"jobs": None, "sourceRuns": None, "sourceRunLimit": 100}
    if "jobs" in tables:
        fields = [name for name in ("id", "kind", "status", "date_from", "date_to", "started_at", "finished_at", "articles_inserted", "mentions_inserted", "stories_touched") if name in columns["jobs"]]
        order = "started_at DESC,id" if "started_at" in fields else "id"
        result["jobs"] = [dict(row) for row in conn.execute(f"SELECT {','.join(fields)} FROM jobs ORDER BY {order} LIMIT 10")]
        result["activeJobStatusRows"] = conn.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('queued','running','exporting','cancel_requested')").fetchone()[0]
        result["statusDoesNotProveBackgroundThreadsHaveExited"] = True
    if "job_source_runs" in tables and "target_key" in columns["job_source_runs"]:
        fields = [name for name in ("id", "job_id", "target_key", "source_key", "source_name", "status", "candidates_seen", "candidates_total", "articles_inserted", "mentions_inserted", "attempts", "updated_at", "finished_at") if name in columns["job_source_runs"]]
        if "last_error" in columns["job_source_runs"]:
            fields.append("CASE WHEN coalesce(last_error,'')<>'' THEN 1 ELSE 0 END AS has_error")
        order = "updated_at DESC,id" if "updated_at" in columns["job_source_runs"] else "id"
        rows = conn.execute(f"SELECT {','.join(fields)} FROM job_source_runs WHERE target_key IN ({placeholders}) ORDER BY {order} LIMIT 101", keys).fetchall()
        result["sourceRuns"] = [dict(row) for row in rows[:100]]
        result["sourceRunsTruncated"] = len(rows) > 100
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", required=True, type=Path)
    parser.add_argument("--roster-json", required=True, help="Roster JSON path or - for stdin; array of key/label objects or a targets manifest.")
    parser.add_argument("--date-from", type=date.fromisoformat, default=date(2026, 6, 1))
    parser.add_argument("--date-to", type=date.fromisoformat, default=datetime.now(ZONE).date())
    parser.add_argument("--sample-limit", type=int, default=20)
    parser.add_argument("--max-seconds", type=int, default=180)
    args = parser.parse_args()
    try:
        if args.date_from > args.date_to or not 0 <= args.sample_limit <= 100 or not 1 <= args.max_seconds <= 1800:
            raise ValueError("invalid_audit_bounds")
        result = audit(args, load_roster(args.roster_json))
    except (OSError, ValueError, sqlite3.Error, TimeoutError) as exc:
        # Do not expose exception messages: paths or database values may contain
        # sensitive strings. A failed/partial audit must never resemble zero data.
        result = {"ok": False, "recordedAt": datetime.now(timezone.utc).isoformat(),
                  "errorType": type(exc).__name__, "countsAvailable": False,
                  "note": "Audit failed or reached its bound; no production counts are asserted."}
        print(json.dumps(result, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
