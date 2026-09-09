#!/usr/bin/env python3
"""Controlled local benchmark of real political queue and legacy ingestion.

Creates an isolated, disposable schema only in a localhost test/bench database.
Network article retrieval is replaced by the same fixed-latency fixture in both
paths. PostgreSQL operations, parsing, matching, immutable object writes, legacy
SQLite ingestion, scoped browsing and HTTP route serialization remain real.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import re
import resource
import sys
import tempfile
import threading
import time
from unittest.mock import patch
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def guarded_database_url(value: str) -> str:
    parsed = urlparse(value)
    name = parsed.path.strip("/")
    if parsed.scheme not in {"postgres", "postgresql"} or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("benchmark requires a localhost PostgreSQL URL")
    if not re.search(r"(?:^|_)(?:test|bench|benchmark)(?:_|$)", name, re.I):
        raise ValueError("database name must contain a test/bench component")
    if not name:
        raise ValueError("benchmark database name is required")
    return value


class FileStore:
    enabled = True
    prefix = "scale-benchmark"

    def __init__(self, root: Path):
        self.root = root

    def upload_bytes(self, data, key, content_type):
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        # Immutable same-hash retries can share one object safely.
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return path.read_bytes() == data
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        return True

    def read_political_object(self, key):
        return (self.root / key).read_bytes()


def current_rss_mib():
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return float(line.split()[1]) / 1024
    except OSError:
        pass
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, int(len(ordered) * fraction) - 1))]


def seed(service, snapshots, rows):
    body = "Texto sintético para medir a navegação em um acervo político de grande porte. " * 15
    digest, key = service._store_text(body)
    keys = [row["key"] for row in snapshots]
    names = [row["display_name"] for row in snapshots]
    with service._connect() as conn:
        conn.execute("""INSERT INTO political_articles(canonical_url,title,source_key,source_name,published_at,date_status,
            snippet,body_status,content_hash,text_object_key,body_chars,metadata)
            SELECT 'https://seed.example.test/reportagem-'||n,'Reportagem sintética de escala '||n,
                   'benchmark_seed','Fixture de escala',TIMESTAMPTZ '2026-06-01 12:00:00+00'+((n%%7)*INTERVAL '1 day'),
                   'page_verified','Metadados sintéticos para teste de paginação.','body_extracted',%s,%s,%s,
                   '{"benchmark":true}'::jsonb FROM generate_series(1,%s) n""", (digest, key, len(body), rows))
        conn.execute("""INSERT INTO political_mentions(article_id,target_key,target_name,keyword_matched)
            SELECT id,(%s::text[])[((id-1)%%25)+1],(%s::text[])[((id-1)%%25)+1],'benchmark'
            FROM political_articles""", (keys, names))
        conn.execute("""INSERT INTO political_stories(id,story_key,title)
            SELECT id,'benchmark-seed:'||id,title FROM political_articles""")
        conn.execute("""SELECT setval(pg_get_serial_sequence('political_stories','id'),%s)""", (rows,))
        conn.execute("INSERT INTO political_story_articles(article_id,story_id) SELECT id,id FROM political_articles")
        conn.execute("INSERT INTO political_url_aliases(url,article_id) SELECT canonical_url,id FROM political_articles")
    with service._connect() as conn:
        conn.execute("ANALYZE political_articles")
        conn.execute("ANALYZE political_mentions")
        conn.execute("ANALYZE political_stories")
        conn.execute("ANALYZE political_story_articles")
        return conn.execute("""SELECT (SELECT COUNT(*) FROM political_articles) AS articles,
            (SELECT COUNT(*) FROM political_mentions) AS mentions,
            (SELECT COUNT(DISTINCT target_key) FROM political_mentions) AS targets""").fetchone()


def fixture(snapshots, count):
    from pipeline.collectors import CandidateArticle
    prefix = uuid.uuid4().hex[:10]
    candidates, content = [], {}
    for index in range(count):
        row = snapshots[index % len(snapshots)]
        name = row["display_name"]
        url = f"https://fixture.example.test/{prefix}/reportagem-politica-{index}"
        title = f"{name} debate propostas para o Rio de Janeiro, documento {index}"
        body = (f"{name} participou de um debate político no Rio de Janeiro sobre propostas do PSD e a eleição de governador. "
                f"O documento {index} discute investimentos públicos, educação, transporte e o trabalho de vereadores, deputados, prefeitos e senadores. "
                "A Câmara Municipal do Rio e representantes estaduais apresentaram propostas para a população fluminense. "
                "Os participantes detalharam prazos de execução, critérios de transparência, recursos disponíveis e formas de acompanhar os resultados. "
                "A reunião terminou com a publicação de um calendário de novas audiências e consultas à sociedade.")
        published = "2026-06-15T12:00:00+00:00"
        raw = '<html><head><meta property="og:title" content="' + html.escape(title) + '"><meta property="article:published_time" content="' + published + '"></head><body><article><p>' + html.escape(body) + '</p></article></body></html>'
        candidates.append(CandidateArticle(title, url, "Benchmark fixture", "rss", published,
                                          "Uma reportagem sintética usada exclusivamente para medir o sistema.",
                                          {"force_full_fetch": True, "exact_body_only": True}))
        content[url] = (url, raw, body, title, published)
    return candidates, content


def run_benchmark(args):
    import psycopg
    from psycopg import sql
    import requests
    from pipeline import ingest
    from web_app.political_corpus import PoliticalCorpusService
    from web_app import political_routes
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    database_url = guarded_database_url(args.database_url)
    schema = "political_benchmark_" + uuid.uuid4().hex
    parsed = urlparse(database_url)
    query = dict(parse_qsl(parsed.query))
    # A task-owned schema keeps unrelated test records untouched.
    query["options"] = "-csearch_path=" + schema
    scoped_url = urlunparse(parsed._replace(query=urlencode(query)))
    raw = json.loads((ROOT / "data" / "targets.json").read_text())
    raw = raw.get("targets", []) if isinstance(raw, dict) else raw
    snapshots = [row for row in raw if row.get("political_roster_version")]
    if len(snapshots) != 25:
        raise ValueError(f"benchmark requires the 25-person roster; found {len(snapshots)}")
    target_keys = [row["key"] for row in snapshots]
    with psycopg.connect(database_url, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    service = None
    rss_stop = threading.Event()
    rss_samples = []
    def sample_rss():
        while not rss_stop.wait(0.02):
            rss_samples.append(current_rss_mib())
    sampler = threading.Thread(target=sample_rss, daemon=True)
    sampler.start()
    try:
        with tempfile.TemporaryDirectory(prefix="political-scale-") as temp:
            directory = Path(temp)
            service = PoliticalCorpusService(database_url=scoped_url, store=FileStore(directory / "objects"))
            service.ensure_schema()
            seed_started = time.perf_counter()
            seed_counts = dict(seed(service, snapshots, args.articles))
            seed_seconds = time.perf_counter() - seed_started
            candidates, content = fixture(snapshots, args.fixture_articles)
            def legacy_fetch(url, request_timeout=10):
                time.sleep(args.latency_ms / 1000)
                return content[url]
            legacy_started = time.perf_counter()
            with patch.object(ingest, "fetch_full_article_text", legacy_fetch):
                legacy = ingest.process_candidates("Benchmark fixture", "rss", candidates,
                    options=ingest.IngestionOptions(target_keys=target_keys, target_snapshots=snapshots,
                        date_from="2026-06-01", date_to="2026-06-30", db_path=str(directory / "legacy.db"),
                        candidate_workers=1, max_process_seconds=600, archive_full_text=True, archive_raw_html=False))
            legacy_seconds = time.perf_counter() - legacy_started
            if legacy.articles_inserted != args.fixture_articles:
                raise RuntimeError(f"legacy fixture saved {legacy.articles_inserted}/{args.fixture_articles}; cannot compare throughput")
            job = service.start_job({"date_from": "2026-06-01", "date_to": "2026-06-30", "kind": "review",
                "target_keys": target_keys, "target_snapshots": snapshots}, started_by="local-scale-benchmark", allowed_target_keys=target_keys)
            job_id = job["id"]
            with service._connect() as conn:
                conn.execute("UPDATE political_tasks SET status='complete' WHERE job_id=%s", (job_id,))
                for candidate in candidates:
                    payload = {**asdict(candidate), "source_key": "benchmark_fixture"}
                    service._insert_task(conn, job_id, "fetch", payload)
            def fetch(url, **kwargs):
                time.sleep(args.latency_ms / 1000)
                final_url, raw_html, *_ = content[url]
                response = requests.Response()
                response.status_code = 200
                response.url = final_url
                response._content = raw_html.encode()
                response.encoding = "utf-8"
                return response
            service.fetch = fetch
            browser_stop = threading.Event()
            request_latencies, service_latencies, browser_errors, results, visible_while_running = [], [], [], [], []
            allowed = target_keys[:5]
            def browser(client):
                index, cursor = 0, ""
                while not browser_stop.is_set():
                    started = time.perf_counter()
                    try:
                        endpoint = "stories" if index % 5 == 4 else "articles"
                        response = client.get("/api/political/" + endpoint, params={"page_size": 50, "cursor": cursor if endpoint == "articles" else ""})
                        request_latencies.append(time.perf_counter() - started)
                        if response.status_code != 200:
                            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:100]}")
                        payload = response.json()
                        if len(payload["items"]) > 50:
                            raise RuntimeError("unbounded HTTP page")
                        if endpoint == "articles":
                            if any(set(row["targetKeys"]) - set(allowed) for row in payload["items"]):
                                raise RuntimeError("target scope escaped HTTP page")
                            if any(row["sourceKey"] == "benchmark_fixture" for row in payload["items"]):
                                visible_while_running.append(True)
                            cursor = payload.get("nextCursor") if index % 4 else ""
                        started = time.perf_counter()
                        page = service.list_articles(allowed_target_keys=allowed, page_size=50)
                        service_latencies.append(time.perf_counter() - started)
                        if len(page["items"]) > 50:
                            raise RuntimeError("unbounded service page")
                    except Exception as exc:
                        browser_errors.append(f"{type(exc).__name__}: {str(exc)[:200]}")
                    index += 1
                    browser_stop.wait(0.01)
            def worker(index):
                while True:
                    task = service.claim_task("fetch", worker_id=f"benchmark-fetch-{index}")
                    if task is None:
                        return
                    results.append(service.process_task(task))
            app = FastAPI()
            app.include_router(political_routes.router)
            # Test fixture authentication only; real route filtering,
            # PostgreSQL authorization, pagination and serialization execute.
            fixed_access = lambda request, **kwargs: ({"sub": "benchmark", "role": "viewer"}, allowed, snapshots[:5])
            with patch.object(political_routes, "political_corpus", service), patch.object(political_routes, "access", fixed_access):
                with TestClient(app) as client:
                    # Warm route/threadpool outside timing.
                    if client.get("/api/political/articles").status_code != 200:
                        raise RuntimeError("HTTP benchmark route failed warmup")
                    browser_thread = threading.Thread(target=browser, args=(client,), daemon=True)
                    browser_thread.start()
                    new_started = time.perf_counter()
                    with ThreadPoolExecutor(max_workers=4) as pool:
                        list(pool.map(worker, range(4)))
                    new_seconds = time.perf_counter() - new_started
                    browser_stop.set()
                    browser_thread.join(timeout=15)
                    if browser_thread.is_alive():
                        raise RuntimeError("browser did not stop")
            with service._connect() as conn:
                saved = conn.execute("SELECT COUNT(*) AS n FROM political_articles WHERE source_key='benchmark_fixture'").fetchone()["n"]
                total = conn.execute("SELECT COUNT(*) AS n FROM political_articles").fetchone()["n"]
                bad_tasks = conn.execute("SELECT COUNT(*) AS n FROM political_tasks WHERE job_id=%s AND kind='fetch' AND status<>'complete'", (job_id,)).fetchone()["n"]
                missing_links = conn.execute("""SELECT COUNT(*) AS n FROM political_articles a WHERE source_key='benchmark_fixture'
                    AND (NOT EXISTS(SELECT 1 FROM political_mentions m WHERE m.article_id=a.id)
                         OR NOT EXISTS(SELECT 1 FROM political_story_articles s WHERE s.article_id=a.id))""").fetchone()["n"]
            speedup = legacy_seconds / new_seconds
            rss_samples.append(current_rss_mib())
            peak = max(rss_samples)
            evidence = {
                "benchmarkVersion": 1, "createdAt": datetime.now(timezone.utc).isoformat(),
                "fixture": {"storedArticles": seed_counts["articles"], "storedMentions": seed_counts["mentions"],
                            "targetCount": seed_counts["targets"], "incomingArticles": args.fixture_articles,
                            "networkLatencyMsPerFetch": args.latency_ms, "seedSeconds": round(seed_seconds, 3)},
                "legacy": {"implementation": "pipeline.ingest.process_candidates", "candidateWorkers": 1,
                           "seconds": round(legacy_seconds, 3), "saved": legacy.articles_inserted,
                           "articlesPerSecond": round(legacy.articles_inserted / legacy_seconds, 3), "errors": legacy.errors},
                "durable": {"implementation": "PoliticalCorpusService.claim_task/process_task", "fetchWorkers": 4,
                            "seconds": round(new_seconds, 3), "saved": saved, "totalStored": total,
                            "articlesPerSecond": round(saved / new_seconds, 3), "nonCompleteFetchTasks": bad_tasks,
                            "missingMentionOrStoryRelations": missing_links, "visibleBeforeCompletion": bool(visible_while_running)},
                "browsing": {"httpRequests": len(request_latencies), "httpP95Ms": round(percentile(request_latencies, .95) * 1000, 3) if request_latencies else None,
                             "serviceRequests": len(service_latencies), "serviceP95Ms": round(percentile(service_latencies, .95) * 1000, 3) if service_latencies else None,
                             "errors": browser_errors, "scopeTargetCount": len(allowed), "pageSize": 50},
                "memory": {"peakRssMiB": round(peak, 3), "configuredCapacityMiB": args.memory_mib,
                           "peakPercent": round(100 * peak / args.memory_mib, 3), "sampleCount": len(rss_samples)},
                "speedup": round(speedup, 3),
                "acceptance": {"atLeast100000Stored": seed_counts["articles"] >= 100000,
                               "all25Targets": seed_counts["targets"] == 25, "atLeast2xThroughput": speedup >= 2,
                               "memoryBelow70Percent": peak < .7 * args.memory_mib,
                               "noLostArticles": saved == args.fixture_articles and total == seed_counts["articles"] + saved,
                               "noIncompleteFetches": bad_tasks == 0, "allRelationships": missing_links == 0,
                               "noWebErrors": bool(request_latencies) and not browser_errors,
                               "committedResultsVisible": bool(visible_while_running)},
                "limitations": ["Controlled article network fixtures; external publisher latency, rate limits and coverage recall are not measured.",
                                "Legacy SQLite starts empty, while durable PostgreSQL starts with the requested large corpus.",
                                "HTTP uses the actual political router through ASGI TestClient with fixture authentication; production deployment is not exercised.",
                                "Immutable compressed object storage is local file-backed; remote object-storage latency is not measured.",
                                "RSS memory covers this Python process including browser and workers, excluding the PostgreSQL server process."],
            }
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
            return evidence
    finally:
        rss_stop.set()
        sampler.join(timeout=2)
        if service:
            service.close()
        with psycopg.connect(database_url, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--articles", type=int, default=100000)
    parser.add_argument("--fixture-articles", type=int, default=120)
    parser.add_argument("--latency-ms", type=float, default=150)
    parser.add_argument("--memory-mib", type=float, default=512)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.articles < 1 or args.fixture_articles < 1 or args.latency_ms < 0 or args.memory_mib <= 0:
        parser.error("counts/capacity must be positive and latency nonnegative")
    result = run_benchmark(args)
    print(json.dumps({"output": str(args.output), "speedup": result["speedup"], "memory": result["memory"],
                      "browsing": result["browsing"], "acceptance": result["acceptance"]}, ensure_ascii=False))
    return 0 if all(result["acceptance"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
