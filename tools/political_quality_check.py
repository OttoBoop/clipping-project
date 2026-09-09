#!/usr/bin/env python3
"""Read-only acceptance check against annotated public articles, never a crawler.

Run --validate-only to validate annotations and synthetic controls without a DB.
Otherwise POLITICAL_DATABASE_URL / RIO_CORPUS_DATABASE_URL selects the service's
database. The checker never creates a schema, enqueues collection or writes data.
Exit codes: 0 = annotated gates passed (or validation-only succeeded), 1 = gates
failed, 2 = corpus could not be measured. A fixture pass is not a rollout approval.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.normalization import canonicalize_url
from web_app.political_corpus import PoliticalCorpusService, match_targets

DEFAULT_DATASET = ROOT / "data/political_known_stories_v1.json"
DEFAULT_ROSTER = ROOT / "data/political_targets_v1.json"
ZONE = ZoneInfo("America/Sao_Paulo")


def _public_url(value):
    parsed = urlparse(str(value))
    return parsed.scheme in {"https", "http"} and bool(parsed.hostname) and not parsed.username


def load_dataset(path=DEFAULT_DATASET, *, roster_path=DEFAULT_ROSTER):
    dataset = json.loads(Path(path).read_text(encoding="utf-8"))
    targets = json.loads(Path(roster_path).read_text(encoding="utf-8"))["targets"]
    target_keys = {row["key"] for row in targets}
    cases = dataset.get("cases")
    if not isinstance(cases, list) or not cases or len(cases) > 1000:
        raise ValueError("fixture requires between 1 and 1000 annotated articles")
    ids, urls = set(), set()
    for row in cases:
        case_id = row.get("id")
        canonical = canonicalize_url(row.get("canonical_url"))
        if not case_id or case_id in ids or not _public_url(canonical) or canonical in urls:
            raise ValueError("article identifiers and URLs must be valid and unique")
        ids.add(case_id)
        urls.add(canonical)
        if row.get("kind") != "public_article" or not row.get("publisher"):
            raise ValueError("public article annotation requires kind and publisher")
        if date.fromisoformat(row["date"]) < date(2026, 6, 1):
            raise ValueError("fixture article predates the political collection window")
        if row.get("date_basis") not in {"published", "visible_article_timestamp", "updated"}:
            raise ValueError("explicit article date provenance required")
        assessed = set(row.get("assessed_target_keys", []))
        expected = set(row.get("expected_target_keys", []))
        if not expected or not expected <= assessed or not assessed <= target_keys:
            raise ValueError("expected and assessed targets must belong to the roster")
        if not row.get("annotation_scope") or not row.get("evidence"):
            raise ValueError("article body annotations require evidence and scope")
        for evidence in row["evidence"]:
            if not _public_url(evidence.get("url")) or not evidence.get("note"):
                raise ValueError("source evidence requires a public URL and note")
            date.fromisoformat(evidence["verified_at"])
        aliases = row.get("aliases", [])
        if len(aliases) > 20 or not all(_public_url(url) for url in aliases):
            raise ValueError("article aliases require at most 20 verified public URLs")
    for row in dataset.get("synthetic_cases", []):
        if row.get("kind") != "synthetic_disambiguation" or not row.get("text"):
            raise ValueError("synthetic controls must be separately labeled")
        if row.get("id") in ids or not row.get("id"):
            raise ValueError("synthetic identifiers must be unique")
        ids.add(row["id"])
        if not set(row.get("expected_target_keys", [])) <= target_keys:
            raise ValueError("synthetic expected targets must belong to the roster")
    return dataset, targets


def synthetic_results(dataset, targets):
    results = []
    for row in dataset.get("synthetic_cases", []):
        actual = {hit["target_key"] for hit in match_targets(targets, "", row["text"])}
        expected = set(row["expected_target_keys"])
        results.append({"id": row["id"], "expected": sorted(expected), "actual": sorted(actual),
                        "passed": actual == expected})
    return {"measured_against": "synthetic text only; excluded from corpus metrics",
            "passed": all(row["passed"] for row in results) if results else None, "cases": results}


def lookup_articles(service, cases):
    """Inspect the service's configured database in one read-only snapshot.

    Direct bounded lookups intentionally find articles with no person association:
    browsing endpoints filter them out, which would conceal missing associations.
    The transaction also prevents incidental future changes from writing here.
    """
    observations = {}
    with service._connect() as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        conn.execute("SET LOCAL statement_timeout = '15s'")
        for row in cases:
            urls = sorted({canonicalize_url(url) for url in [row["canonical_url"], *row.get("aliases", [])]})
            articles = conn.execute("""
                SELECT a.id,a.canonical_url,a.published_at,a.date_status,a.body_status,a.text_object_key,
                       ARRAY(SELECT m.target_key FROM political_mentions m
                             WHERE m.article_id=a.id ORDER BY m.target_key) AS target_keys
                FROM political_articles a
                WHERE a.canonical_url=ANY(%s) OR EXISTS(
                    SELECT 1 FROM political_url_aliases u
                    WHERE u.article_id=a.id AND u.url=ANY(%s))
                ORDER BY a.id
            """, (urls, urls)).fetchall()
            observations[row["id"]] = [dict(article) for article in articles]
    return observations


def _local_day(value):
    if not value:
        return None
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if not parsed.tzinfo:
            parsed = parsed.replace(tzinfo=ZONE)
        return parsed.astimezone(ZONE).date().isoformat()
    except (TypeError, ValueError):
        return None


def score_cases(dataset, observations):
    """Score only explicit labels. Unassessed targets never become false positives."""
    cases = dataset["cases"]
    details = []
    found = full_text = true_positive = false_positive = false_negative = 0
    for row in cases:
        articles = observations.get(row["id"], [])
        expected, assessed = set(row["expected_target_keys"]), set(row["assessed_target_keys"])
        actual = {key for article in articles for key in article.get("target_keys", [])} & assessed
        correct, unexpected, missing = actual & expected, actual - expected, expected - actual
        found += bool(articles)
        available = any(article.get("body_status") == "body_extracted" and article.get("text_object_key")
                        for article in articles)
        full_text += available
        true_positive += len(correct)
        false_positive += len(unexpected)
        false_negative += len(missing)
        dates = sorted({day for article in articles if (day := _local_day(article.get("published_at")))})
        details.append({"id": row["id"], "canonical_url": row["canonical_url"], "found": bool(articles),
                        "article_ids": [article["id"] for article in articles], "full_text_available": available,
                        "duplicate_record_count": max(0, len(articles) - 1),
                        "expected_target_keys": sorted(expected), "actual_assessed_target_keys": sorted(actual),
                        "missing_target_keys": sorted(missing), "incorrect_target_keys": sorted(unexpected),
                        "expected_date": row["date"], "date_basis": row["date_basis"], "stored_local_dates": dates,
                        "publication_date_needs_review": bool(articles) and (not dates or (
                            row["date_basis"] == "published" and row["date"] not in dates))})
    article_recall = found / len(cases) if cases else None
    person_recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else None
    incorrect_rate = false_positive / (true_positive + false_positive) if true_positive + false_positive else None
    # Acceptance values are the requested gates, never silently weakened by a fixture.
    gates = {"article_recall_at_least_90_percent": article_recall is not None and article_recall >= .9,
             "person_recall_at_least_90_percent": person_recall is not None and person_recall >= .9,
             "incorrect_person_matches_at_most_5_percent": incorrect_rate is not None and incorrect_rate <= .05}
    return {"measured": bool(cases), "scope": "annotated article cases and assessed target keys only",
            "article_count": len(cases), "found_articles": found, "full_text_available_articles": full_text,
            "article_recall": article_recall, "person_recall": person_recall,
            "person_precision": 1 - incorrect_rate if incorrect_rate is not None else None,
            "incorrect_person_match_rate": incorrect_rate, "true_positive_person_associations": true_positive,
            "false_positive_person_associations": false_positive, "missing_person_associations": false_negative,
            "gates": gates, "annotated_case_gates_passed": all(gates.values()), "cases": details}


def build_report(dataset, targets, *, observations=None, pending_reason="collection_not_measured"):
    measured = score_cases(dataset, observations) if observations is not None else {
        "measured": False, "reason": pending_reason, "scope": "annotated article cases only",
        "article_count": len(dataset["cases"]), "article_recall": None, "person_recall": None,
        "person_precision": None, "incorrect_person_match_rate": None,
        "gates": None, "annotated_case_gates_passed": None}
    return {"dataset_version": dataset["version"], "checked_at": datetime.now(timezone.utc).isoformat(),
            "limitations": dataset.get("limitations", []), "production_rollout_verified": False,
            "corpus": measured, "synthetic_controls": synthetic_results(dataset, targets)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--database-url", default="", help="defaults to the political service environment")
    parser.add_argument("--validate-only", action="store_true", help="no database access; does not pass corpus gates")
    parser.add_argument("--date-from", type=date.fromisoformat)
    parser.add_argument("--date-to", type=date.fromisoformat)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    dataset, targets = load_dataset(args.dataset)
    if args.date_from and args.date_to and args.date_from > args.date_to:
        parser.error("date-from must not exceed date-to")
    dataset = {**dataset, "cases": [row for row in dataset["cases"]
               if (not args.date_from or date.fromisoformat(row["date"]) >= args.date_from)
               and (not args.date_to or date.fromisoformat(row["date"]) <= args.date_to)]}
    report = build_report(dataset, targets, pending_reason="validation_only" if args.validate_only else "database_not_configured")
    exit_code = 0 if args.validate_only else 2
    if not dataset["cases"]:
        report["corpus"]["reason"] = "no_annotated_articles_in_selected_period"
        exit_code = 2
    elif not args.validate_only:
        service = PoliticalCorpusService(database_url=args.database_url)
        try:
            if service.configured:
                report = build_report(dataset, targets, observations=lookup_articles(service, dataset["cases"]))
                exit_code = 0 if report["corpus"]["annotated_case_gates_passed"] else 1
        except Exception as exc:
            # Connection URLs and driver messages can contain credentials.
            report = build_report(dataset, targets, pending_reason="database_unavailable")
            report["corpus"]["error_type"] = type(exc).__name__
            exit_code = 2
        finally:
            service.close()
    if report["synthetic_controls"]["passed"] is False and exit_code == 0:
        exit_code = 1
    encoded = json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
