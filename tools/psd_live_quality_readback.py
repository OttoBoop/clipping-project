#!/usr/bin/env python3
"""Bounded GET-only PSD production readback using an existing private session.

Reads the scoped API, never logs in, collects, resumes, classifies or imports.
Only public article metadata and at most twenty excerpt words per sampled body
enter the local report. Cookies and server error response bodies are never logged.
Exit 0: bounded readback complete; 1: partial/failed readback; 2: invalid inputs.
Exit 0 does not mean quality gates passed or collection finished.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import fields
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.matcher import CitationMatcher, Target, _normalize_match_text
from pipeline.normalization import canonicalize_url

BASE_URL = "https://clipping-project.onrender.com"
PROFILE = "psd_rj_2026"
DEFAULT_SESSION = Path.home() / ".local/share/clipping-render-auth/rollout/psd-live-session-private.json"
DEFAULT_REFERENCE = ROOT / "data/psd_known_stories_2026.json"
DEFAULT_PROFILE = ROOT / "data/psd_rj_2026_profile.json"
DEFAULT_ROSTER = ROOT / "data/political_targets_v1.json"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class ReadbackError(Exception):
    def __init__(self, kind, *, status=None, route=None):
        self.detail = {"error_type": kind}
        if status is not None:
            self.detail["http_status"] = status
        if route:
            self.detail["route"] = route
        super().__init__(kind)


class ReadOnlyAPI:
    """No arbitrary URL, mutation method, redirects or credential serialization."""

    def __init__(self, session_path, *, interval=1.0):
        saved = json.loads(Path(session_path).read_text())
        if not isinstance(saved.get("cookies"), dict) or not saved["cookies"]:
            raise ValueError("saved_session_has_no_cookies")
        self.session = requests.Session()
        for key, value in saved["cookies"].items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("invalid_saved_cookie")
            self.session.cookies.set(key, value, domain="clipping-project.onrender.com", path="/", secure=True)
        role = saved.get("identity", {}).get("role")
        self.scope_params = {"client": PROFILE} if role == "admin" else {}
        self.interval = max(1.0, interval)
        self.last_request = 0.0
        self.request_count = 0

    def get(self, route, params=None):
        if not re.fullmatch(r"/api/political/(?:meta|status|coverage|articles|articles/[0-9]+/text)", route):
            raise ValueError("read_route_not_allowed")
        time.sleep(max(0, self.interval - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        self.request_count += 1
        try:
            with self.session.get(BASE_URL + route, params={**self.scope_params, **(params or {})},
                                  timeout=(10, 25), allow_redirects=False, stream=True) as response:
                if response.status_code != 200:
                    raise ReadbackError("http_error", status=response.status_code, route=route)
                chunks, size = [], 0
                for chunk in response.iter_content(chunk_size=65536):
                    size += len(chunk)
                    if size > 8 * 1024 * 1024:
                        raise ReadbackError("response_size_limit", route=route)
                    chunks.append(chunk)
                result = json.loads(b"".join(chunks))
                if not isinstance(result, dict):
                    raise ReadbackError("invalid_response_shape", route=route)
                return result
        except requests.RequestException as exc:
            # Never include str(exc): transport diagnostics can contain URLs.
            raise ReadbackError(type(exc).__name__, route=route) from None
        except (json.JSONDecodeError, UnicodeError):
            raise ReadbackError("invalid_json", route=route) from None

    def close(self):
        self.session.close()


def public_article(row):
    return {key: row.get(key) for key in (
        "id", "url", "title", "sourceKey", "sourceName", "publishedAt", "dateStatus",
        "bodyStatus", "bodyChars", "targetKeys", "needsReview", "legacyId",
    )}


def public_job(status):
    row = status.get("current") or {}
    return {key: row.get(key) for key in (
        "id", "kind", "status", "targetKeys", "dateFrom", "dateTo", "createdAt",
        "updatedAt", "finishedAt", "metrics",
    )} if row else None


def read_articles(api, keys, start, end, max_pages):
    articles, seen_cursors, cursor = {}, set(), ""
    for page in range(max_pages):
        response = api.get("/api/political/articles", {
            "target_key": keys, "date_from": start.isoformat(), "date_to": end.isoformat(),
            "page_size": 200, "cursor": cursor,
        })
        items = response.get("items")
        if not isinstance(items, list) or len(items) > 200:
            raise ReadbackError("invalid_article_page", route="/api/political/articles")
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("id"), int):
                raise ReadbackError("invalid_article_metadata", route="/api/political/articles")
            articles[item["id"]] = public_article(item)
        if not response.get("hasMore"):
            return list(articles.values()), {"complete": True, "pages": page + 1, "bounded_at_articles": max_pages * 200}
        cursor = response.get("nextCursor")
        if not cursor or cursor in seen_cursors:
            raise ReadbackError("invalid_or_repeated_cursor", route="/api/political/articles")
        seen_cursors.add(cursor)
    return list(articles.values()), {"complete": False, "pages": max_pages, "reason": "page_limit",
                                    "bounded_at_articles": max_pages * 200}


def index_articles(articles):
    index = {}
    for article in articles:
        index.setdefault(canonicalize_url(article.get("url")), []).append(article)
    return index


def case_observation(case, index):
    found = {}
    for url in [case["canonical_url"], *case.get("aliases", [])]:
        for article in index.get(canonicalize_url(url), []):
            found[article["id"]] = article
    articles = list(found.values())
    expected = set(case["expected_target_keys"])
    assessed = set(case["assessed_target_keys"])
    actual = {key for article in articles for key in (article.get("targetKeys") or [])} & assessed
    return {
        "id": case["id"], "canonical_url": case["canonical_url"], "source_key": case["source_key"],
        "reference_date": case["date"], "date_basis": case["date_basis"],
        "visible_in_scoped_api": bool(articles), "article_ids": sorted(found),
        "expected_target_keys": sorted(expected), "actual_assessed_target_keys": sorted(actual),
        "missing_expected_target_keys": sorted(expected - actual),
        "incorrect_assessed_target_keys": sorted(actual - expected),
        "body_extracted_article_ids": sorted(a["id"] for a in articles if a.get("bodyStatus") == "body_extracted"),
        "stored_publication_values": sorted({a["publishedAt"] for a in articles if a.get("publishedAt")}),
    }


def compare_reference(dataset, articles, start, end, *, listing_complete):
    index = index_articles(articles)
    strict, unverified, outside = [], [], []
    for case in dataset["cases"]:
        observed = case_observation(case, index)
        if not case.get("eligible_for_strict_date_evaluation", False):
            observed["absence_is_evaluated"] = False
            observed["note"] = "Publication date remains unverified; no date-window recall denominator."
            unverified.append(observed)
        elif start <= date.fromisoformat(case["date"]) <= end:
            strict.append(observed)
        else:
            outside.append(case["id"])
    expected = sum(len(row["expected_target_keys"]) for row in strict)
    missing = sum(len(row["missing_expected_target_keys"]) for row in strict)
    wrong = sum(len(row["incorrect_assessed_target_keys"]) for row in strict)
    visible = sum(row["visible_in_scoped_api"] for row in strict)
    can_score = bool(strict) and listing_complete
    return {
        "scope": "profile-visible API articles in selected dates; only annotated assessed people",
        "reference_total_articles": len(dataset["cases"]), "strict_date_articles_in_selected_window": len(strict),
        "reference_articles_outside_window": len(outside), "outside_window_case_ids": outside,
        "unverified_date_articles": len(unverified), "visible_reference_articles": visible,
        "expected_person_associations": expected, "missing_expected_person_associations": missing,
        "incorrect_assessed_person_associations": wrong,
        "rates_measured": can_score,
        "rate_unavailable_reason": None if can_score else ("no_reference_articles_in_selected_window" if not strict else "incomplete_pagination"),
        "visible_reference_fraction": visible / len(strict) if can_score else None,
        "annotated_person_association_recall": (expected - missing) / expected if can_score and expected else None,
        "annotated_assessed_person_precision": (expected - missing) / (expected - missing + wrong)
            if can_score and expected - missing + wrong else None,
        "production_quality_gate_passed": None,
        "cases": strict, "unverified_date_presence_only": unverified,
    }


def sample_articles(articles, keys, comparison, limit):
    selected = {}
    by_id = {row["id"]: row for row in articles}
    # Reference matches are independently annotated; inspect these bodies first.
    for case in comparison["cases"]:
        for article_id in case["article_ids"]:
            if len(selected) < limit:
                selected[article_id] = by_id[article_id]
    # Then request up to two bodies per approved person, sharing multi-person rows.
    for key in keys:
        already = sum(key in (row.get("targetKeys") or []) for row in selected.values())
        for row in articles:
            if already >= 2 or len(selected) >= limit:
                break
            if row["id"] not in selected and key in (row.get("targetKeys") or []):
                selected[row["id"]] = row
                already += 1
    return list(selected.values())


def audit_bodies(api, articles, matcher, keys):
    results = []
    for article in articles:
        result = {"article_id": article["id"], "url": article["url"], "assigned_target_keys": article.get("targetKeys") or []}
        try:
            response = api.get(f"/api/political/articles/{article['id']}/text")
            body = response.get("text")
            if not isinstance(body, str):
                raise ReadbackError("invalid_article_body_shape")
            text = str(article.get("title") or "") + "\n" + body
            hits = matcher.find_hits(text)
            local = {hit.target_key for hit in hits} & set(keys)
            assigned = set(result["assigned_target_keys"])
            result.update({
                "body_status": response.get("bodyStatus"), "body_chars_read": len(body),
                "body_sha256": hashlib.sha256(body.encode()).hexdigest(),
                "local_rule_matches": sorted(local), "assigned_without_local_match": sorted(assigned - local),
                "local_matches_without_assignment": sorted(local - assigned),
                "manual_editorial_review_required": bool(assigned - local or local - assigned),
            })
            if hits:
                normalized = _normalize_match_text(text)
                first = min(hit.position for hit in hits)
                result["evidence_excerpt_normalized_max_20_words"] = " ".join(normalized[first:].split()[:20])
        except ReadbackError as exc:
            result.update({"body_read_failed": True, **exc.detail})
        results.append(result)
    return {"scope": "bounded local matcher consistency audit, not independent editorial truth or corpus precision",
            "requested_articles": len(articles), "body_reads_succeeded": sum(not r.get("body_read_failed") for r in results),
            "disagreement_articles": sum(r.get("manual_editorial_review_required", False) for r in results),
            "articles": results}


def run(args):
    dataset = json.loads(args.dataset.read_text())
    profile = json.loads(DEFAULT_PROFILE.read_text())
    keys = profile["target_keys"]
    if len(keys) != 24 or len(set(keys)) != 24:
        raise ValueError("approved_profile_requires_24_unique_targets")
    for case in dataset["cases"]:
        if not set(case["expected_target_keys"]) <= set(case["assessed_target_keys"]) <= set(keys):
            raise ValueError("reference_target_outside_approved_profile")
    report = {
        "report_version": "psd_live_api_readback_v1", "started_at": utc_now(), "origin": BASE_URL,
        "profile_key": PROFILE, "date_from": args.date_from.isoformat(), "date_to": args.date_to.isoformat(),
        "timezone": "America/Sao_Paulo", "requested_job_id": args.job_id,
        "reference_version": dataset["version"], "reference_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "local_matcher_sha256": hashlib.sha256((ROOT / "pipeline/matcher.py").read_bytes()).hexdigest(),
        "local_roster_sha256": hashlib.sha256(DEFAULT_ROSTER.read_bytes()).hexdigest(),
        "production_readback_complete": False, "production_rollout_verified": False,
        "limitations": [
            "Scoped API lists hide articles with no allowed-person association and filter by stored publication date. A missing URL is not proof that no database row exists.",
            "Only verified URLs and aliases are compared; API does not expose the database alias table. Unresolved canonical aliases remain a possible false absence.",
            "Date-filtered articles are not restricted to a single collection job. Job metrics are reported separately; visible article counts are not newly inserted article counts.",
            "Pagination and body reads occur over time without an atomic database snapshot. Results during active collection are provisional.",
            "Per-person zeros without an annotated reference in this date window are not recall measurements.",
            "Local matcher agreement is an implementation consistency check, not independent editorial accuracy. Only explicit reference labels support reference-quality counts.",
            "Three J3News publication dates remain unverified and never enter strict date-window denominators.",
        ],
    }
    api = None
    try:
        api = ReadOnlyAPI(args.session_file)
        meta = api.get("/api/political/meta")
        visible_targets = meta.get("targets", []) + meta.get("archivedTargets", [])
        available = {row["key"] for row in visible_targets}
        report["account_scope"] = {"configured": meta.get("configured"), "profile": meta.get("clientProfile"),
                                   "approved_targets_visible": sorted(set(keys) & available),
                                   "approved_targets_missing": sorted(set(keys) - available)}
        if meta.get("clientProfile") != PROFILE or not set(keys) <= available:
            raise ReadbackError("incomplete_or_wrong_account_scope")
        if not meta.get("configured"):
            raise ReadbackError("political_corpus_not_configured")
        status_params = {"job_id": args.job_id} if args.job_id else {}
        status = api.get("/api/political/status", status_params)
        report["job_before"] = public_job(status)
        coverage = api.get("/api/political/coverage", status_params)
        report["job_source_coverage"] = {key: coverage.get(key) for key in ("jobId", "status", "sources", "gaps")}
        articles, pagination = read_articles(api, keys, args.date_from, args.date_to, args.max_pages)
        report["pagination"] = pagination
        report["visible_articles"] = articles
        report["visible_article_count"] = len(articles)
        report["by_source"] = dict(Counter(row.get("sourceKey") for row in articles))
        report["by_body_status"] = dict(Counter(row.get("bodyStatus") for row in articles))
        report["by_date_status"] = dict(Counter(row.get("dateStatus") for row in articles))
        comparison = compare_reference(dataset, articles, args.date_from, args.date_to, listing_complete=pagination["complete"])
        report["reference_comparison"] = comparison
        roster = {row["key"]: row for row in json.loads(DEFAULT_ROSTER.read_text())["targets"]}
        for row in visible_targets:
            if row["key"] in roster:
                roster[row["key"]] = {**roster[row["key"]], **row}
        allowed_fields = {f.name for f in fields(Target)}
        matcher = CitationMatcher([Target(**{k: v for k, v in roster[key].items() if k in allowed_fields}) for key in keys])
        selected = sample_articles(articles, keys, comparison, args.max_bodies)
        body_audit = audit_bodies(api, selected, matcher, keys)
        report["body_consistency_audit"] = body_audit
        report["per_target"] = []
        for key in keys:
            expected = [case for case in comparison["cases"] if key in case["expected_target_keys"]]
            matched = sum(key in case["actual_assessed_target_keys"] for case in expected)
            report["per_target"].append({
                "target_key": key, "visible_associated_articles": sum(key in (row.get("targetKeys") or []) for row in articles),
                "strict_date_reference_articles_in_window": len(expected), "reference_associations_visible": matched,
                "reference_association_recall": matched / len(expected) if expected and pagination["complete"] else None,
                "reference_reason": "annotated_cases_only" if expected else "no_reference_for_this_person_in_selected_window",
                "body_sample_articles": sum(key in row["assigned_target_keys"] for row in body_audit["articles"]),
            })
        report["job_after"] = public_job(api.get("/api/political/status", status_params))
        report["job_window_matches_readback"] = bool(report["job_after"] and
            report["job_after"].get("dateFrom") == args.date_from.isoformat() and
            report["job_after"].get("dateTo") == args.date_to.isoformat())
        report["collection_status"] = (report["job_after"] or {}).get("status")
        report["provisional_during_active_collection"] = report["collection_status"] in {"queued", "running", "retryable"}
        report["production_readback_complete"] = pagination["complete"] and all(not row.get("body_read_failed") for row in body_audit["articles"])
    except ReadbackError as exc:
        report["error"] = exc.detail
    finally:
        if api:
            report["http_get_requests"] = api.request_count
            api.close()
        report["finished_at"] = utc_now()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-file", type=Path, default=DEFAULT_SESSION)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--date-from", type=date.fromisoformat, required=True)
    parser.add_argument("--date-to", type=date.fromisoformat, required=True)
    parser.add_argument("--job-id", default="")
    parser.add_argument("--max-pages", type=int, default=50, help="200 articles per page, default at most 10,000 metadata rows")
    parser.add_argument("--max-bodies", type=int, default=48, help="at most this many individual article bodies")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.date_from < date(2026, 6, 1) or args.date_from > args.date_to:
        parser.error("invalid collection date window")
    if not 1 <= args.max_pages <= 100 or not 0 <= args.max_bodies <= 200:
        parser.error("max-pages must be 1..100 and max-bodies 0..200")
    if args.output.resolve() in {p.resolve() for p in (args.session_file, args.dataset, DEFAULT_PROFILE, DEFAULT_ROSTER)}:
        parser.error("output must not overwrite credentials or source inputs")
    try:
        report = run(args)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        # Configuration failures also stay free of private paths/file contents.
        print(json.dumps({"production_readback_complete": False, "error_type": type(exc).__name__}))
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "output": str(args.output), "production_readback_complete": report["production_readback_complete"],
        "visible_article_count": report.get("visible_article_count"), "collection_status": report.get("collection_status"),
        "strict_date_reference_articles_in_selected_window": report.get("reference_comparison", {}).get("strict_date_articles_in_selected_window"),
        "error": report.get("error"),
    }, ensure_ascii=False))
    return 0 if report["production_readback_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
