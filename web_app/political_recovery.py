"""Bounded recovery of recorded failures; never an archive review."""
from __future__ import annotations

from .political_source_catalog import source_aliases

RECOVERY_FAILURES = {"http_400", "istoe_deferred_dates","body_missing", "http_401", "http_403", "http_404", "http_429",
                     "google_url_unresolved", "google_access_challenge", "publisher_access_challenge", "storage",
                     "metadata_only", "network", "partial_text"}


def recovery_filters(payload: dict) -> list[str]:
    raw = payload.get("recovery_gap_types", ["body_missing", "metadata_only"])
    if not isinstance(raw, list) or not raw or any(not isinstance(k, str) or k not in RECOVERY_FAILURES for k in raw):
        raise ValueError("invalid_recovery_gap_types")
    return sorted(set(raw))


class PoliticalRecoveryMixin:
    def _recover_discovery(self, task: dict, source: dict) -> dict:
        cursor = task["cursor"]
        with self._connect() as conn:
            job = self._lock_task(conn, task)
            meta = job["metadata"]
            failures = meta["recovery_gap_types"]
            aliases = source_aliases(source["key"], meta["source_snapshots"])
            domains = list({d.removeprefix("www.") for d in [source.get("domain", ""), *source.get("domains", [])] if d})
        if failures == ["istoe_deferred_dates"]:
            if source["key"] != "istoe":
                raise ValueError("istoe_recovery_source_required")
            after = int(cursor.get("after_id", 0))
            with self._connect() as conn:
                rows = conn.execute("""SELECT o.id,o.observed_url,o.title,o.metadata FROM political_observations o
                    JOIN political_jobs j ON j.id=o.job_id
                    WHERE o.id>%s AND o.id<=%s AND o.source_key='istoe' AND o.disposition='deferred_date'
                    AND j.target_keys <@ %s AND j.date_from<=%s AND j.date_to>=%s
                    ORDER BY o.id LIMIT 101""", (after,meta['recovery_max_observation_id'],job['target_keys'],job['date_to'],job['date_from'])).fetchall()
            more, rows = len(rows)>100,rows[:100]
            admitted = int(cursor.get('admitted',0))+len(rows)
            capped = more and admitted % 500 == 0
            return {'candidates':[{'url':r['observed_url'],'title':r['title'],'source_key':'istoe',
                    'source_name':source['name'],'metadata':{**r['metadata'],'body_deferred':False,'recovery_observation_id':r['id']}} for r in rows],
                    'raw_count':len(rows),'child_tasks':[], 'outcome':'gap' if capped else 'continue' if more else 'complete',
                    'gap_reason':'istoe_date_recovery_batch_limit' if capped else '',
                    'next_cursor':{'after_id':rows[-1]['id'] if rows else after,'admitted':admitted}}
        # Selection is read-only and bounded by the frozen observation ceiling.
        # Release the job/lease row locks before scanning historical failures so
        # fetch commits and lease renewal can proceed. _discover fences the
        # lease again before admitting any selected candidates.
        with self._connect() as conn:
            # Failed pages without articles are included. The publisher may have
            # been resolved from Google after the original observation was made.
            rows = conn.execute("""SELECT o.id,o.observed_url,o.title,o.snippet,o.metadata,
                a.id AS article_id,a.canonical_url,a.published_at,a.date_status,
                a.html_hash AS article_html_hash,a.html_object_key AS article_html_key,
                f.payload AS fetch_payload,f.cursor AS fetch_cursor,f.error_type,
                a.text_object_key,a.metadata->>'text_extent' AS text_extent
                FROM political_observations o JOIN political_jobs j ON j.id=o.job_id
                JOIN political_tasks f ON f.job_id=o.job_id AND f.kind='fetch' AND f.dedupe_key=o.observed_url
                LEFT JOIN political_articles a ON a.id=o.article_id
                WHERE o.id>%s AND o.id<=%s AND j.target_keys <@ %s
                AND j.date_from<=%s AND j.date_to>=%s
                AND (o.source_key=ANY(%s) OR a.source_key=ANY(%s)
                    OR regexp_replace(lower(substring(COALESCE(f.cursor->>'resolved_url',a.canonical_url,o.observed_url)
                        FROM '^https?://([^/]+)')),'^www[.]','')=ANY(%s))
                AND (f.error_type=ANY(%s)
                    OR (%s AND a.text_object_key='')
                    OR (%s AND a.text_object_key<>'' AND a.metadata->>'text_extent'='partial')
                    OR (%s AND f.error_type ~ '(storage|object)')
                    OR (%s AND f.error_type ~ '(timeout|Timeout|connection|Connection|SSL|DNS)'))
                ORDER BY o.id LIMIT 101""",
                (int(cursor.get("after_id", 0)), meta["recovery_max_observation_id"], job["target_keys"],
                 job["date_to"], job["date_from"], aliases, aliases, domains, failures,
                 "metadata_only" in failures, "partial_text" in failures,
                 "storage" in failures, "network" in failures)).fetchall()
        more, rows = len(rows) > 100, rows[:100]
        candidates = []
        for row in rows:
            original = row["fetch_payload"] or {}
            metadata = row["metadata"] or {}
            resolved = (row["fetch_cursor"] or {}).get("resolved_url")
            url = resolved or row["canonical_url"] or row["observed_url"]
            evidence_key = metadata.get("html_object_key") or row["article_html_key"]
            evidence_hash = metadata.get("html_hash") or row["article_html_hash"]
            candidate = {**original, "url": url, "source_key": source["key"], "source_name": source["name"],
                "title": row["title"], "snippet": row["snippet"],
                "published_at": str(row["published_at"] or original.get("published_at") or ""),
                "metadata": {**(original.get("metadata") or {}),
                    "recovery": {"observation_id": row["id"], "observed_url": row["observed_url"],
                                 "article_id": row["article_id"], "failure": row["error_type"]}}}
            candidate.pop("force_refresh", None)
            candidate.pop("recover_partial_text", None)
            # Only an explicit partial marker authorizes this narrow repair.
            # "unknown" is not evidence of missing editorial text.
            if "partial_text" in failures and row["text_object_key"] and row["text_extent"] == "partial":
                candidate["recover_partial_text"] = True
            if evidence_key and evidence_hash:
                candidate["recovery_html"] = {"key": evidence_key, "hash": evidence_hash, "url": url}
            candidates.append(candidate)
        return {"candidates": candidates, "raw_count": len(rows), "child_tasks": [], "gap_reason": "",
                "outcome": "continue" if more else "complete",
                "next_cursor": {"after_id": rows[-1]["id"] if rows else cursor.get("after_id", 0)}}
