#!/usr/bin/env python3
"""Authenticated operator for Rio topic jobs.

The script starts or resumes `rio_economico` topic jobs and polls the
same production endpoints an operator uses in the browser. It writes JSONL to
stdout so long backfills can be tailed or archived.
"""

from __future__ import annotations

import argparse
import calendar
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from http.cookiejar import CookieJar
from typing import Any


DEFAULT_BASE_URL = "https://clipping-project.onrender.com"


class Client:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.cookies = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))
        self.csrf = ""

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        csrf: bool = False,
        timeout: int = 30,
    ) -> tuple[int, Any]:
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if csrf:
            if not self.csrf:
                self.refresh_csrf()
            headers["X-CSRF-Token"] = self.csrf
        req = urllib.request.Request(
            urllib.parse.urljoin(self.base_url + "/", path.lstrip("/")),
            data=data,
            method=method,
            headers=headers,
        )
        try:
            with self.opener.open(req, timeout=timeout) as response:
                raw = response.read().decode("utf-8", errors="replace")
                return response.status, parse_body(raw, response.headers.get("content-type", ""))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            return exc.code, parse_body(raw, exc.headers.get("content-type", ""))
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
            return 0, {"error": "request_failed", "detail": str(exc)}

    def login(self, password: str) -> dict[str, Any]:
        status, body = self.request("POST", "/api/login", {"password": password})
        if status != 200:
            raise RuntimeError(f"login_failed:{status}:{safe_detail(body)}")
        self.refresh_csrf()
        return body if isinstance(body, dict) else {"ok": True}

    def refresh_csrf(self) -> str:
        status, body = self.request("GET", "/api/csrf")
        if status != 200 or not isinstance(body, dict) or not body.get("csrf"):
            raise RuntimeError(f"csrf_failed:{status}:{safe_detail(body)}")
        self.csrf = str(body["csrf"])
        return self.csrf


def parse_body(raw: str, content_type: str) -> Any:
    if "json" not in content_type:
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def safe_detail(body: Any) -> str:
    if isinstance(body, dict):
        return str(body.get("detail") or body.get("error") or body)[:160]
    return str(body)[:160]


def emit(event: str, payload: dict[str, Any]) -> None:
    print(json.dumps({"event": event, **payload}, ensure_ascii=False), flush=True)


def default_canary_window() -> tuple[str, str]:
    today = date.today()
    return (today - timedelta(days=30)).isoformat(), today.isoformat()


def year_window(year: int) -> tuple[str, str]:
    today = date.today()
    start = date(int(year), 1, 1)
    end = date(int(year), 12, 31)
    if end > today:
        end = today
    if start > end:
        raise ValueError(f"backfill_year_in_future:{year}")
    return start.isoformat(), end.isoformat()


def month_window(year: int, month: int, *, today: date | None = None) -> tuple[str, str]:
    today = today or date.today()
    start = date(int(year), int(month), 1)
    last_day = calendar.monthrange(start.year, start.month)[1]
    end = date(start.year, start.month, last_day)
    if end > today:
        end = today
    if start > end:
        raise ValueError(f"backfill_month_in_future:{year}-{month:02d}")
    return start.isoformat(), end.isoformat()


def backfill_windows(
    start_year: int,
    end_year: int,
    *,
    mode: str,
    today: date | None = None,
) -> list[tuple[str, str, str]]:
    if start_year > end_year:
        start_year, end_year = end_year, start_year
    if mode == "year":
        return [(str(year), *year_window(year)) for year in range(start_year, end_year + 1)]
    if mode != "month":
        raise ValueError(f"invalid_backfill_window:{mode}")
    today = today or date.today()
    windows: list[tuple[str, str, str]] = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            try:
                date_from, date_to = month_window(year, month, today=today)
            except ValueError:
                continue
            windows.append((f"{year}-{month:02d}", date_from, date_to))
    return windows


def start_topic_job(client: Client, args: argparse.Namespace) -> dict[str, Any]:
    date_from, date_to = args.date_from, args.date_to
    if not date_from or not date_to:
        date_from, date_to = default_canary_window()
    payload = {
        "scope": args.scope,
        "topic": args.topic,
        "preset": args.preset or args.topic,
        "date_from": date_from,
        "date_to": date_to,
        "collector": args.collector,
        "export": not args.no_export,
    }
    status, body = client.request("POST", "/api/update/start", payload, csrf=True, timeout=60)
    if status == 409 and args.resume_on_conflict:
        emit("start_conflict_resume_attempt", {"status": status, "detail": safe_detail(body)})
        return resume_topic_job(client, "")
    if status != 200:
        raise RuntimeError(f"start_failed:{status}:{safe_detail(body)}")
    return body if isinstance(body, dict) else {"status": status}


def resume_topic_job(client: Client, job_id: str) -> dict[str, Any]:
    payload = {"job_id": job_id} if job_id else {}
    status, body = client.request("POST", "/api/update/resume", payload, csrf=True, timeout=60)
    if status != 200:
        raise RuntimeError(f"resume_failed:{status}:{safe_detail(body)}")
    return body if isinstance(body, dict) else {"status": status}


def poll_once(client: Client, job_id: str = "") -> dict[str, Any]:
    endpoints: dict[str, tuple[str, str]] = {
        "status": ("GET", "/api/update/status?scope=rio_economico" + (f"&job_id={urllib.parse.quote(job_id)}" if job_id else "")),
        "memory": ("GET", "/api/admin/debug/memory"),
        "disk": ("GET", "/api/admin/debug/disk"),
        "corpus": ("GET", "/api/rio/corpus?page=1&page_size=20"),
        "sources": ("GET", "/api/rio/sources"),
        "coverage": ("GET", "/api/rio/coverage?page=1&page_size=80" + (f"&job_id={urllib.parse.quote(job_id)}" if job_id else "")),
        "audit": ("GET", "/api/rio/audit?limit=20" + (f"&job_id={urllib.parse.quote(job_id)}" if job_id else "")),
    }
    if job_id:
        endpoints["source_runs"] = ("GET", f"/api/admin/jobs/{urllib.parse.quote(job_id)}/source-run-events?limit=80")
    payload: dict[str, Any] = {}
    for name, (method, path) in endpoints.items():
        status, body = client.request(method, path)
        payload[name] = summarize_endpoint(status, body)
    return payload


def summarize_endpoint(status: int, body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        return {"status": status, "body": safe_detail(body)}
    if status != 200:
        return {"status": status, "detail": safe_detail(body)}
    summary = {"status": status}
    if isinstance(body.get("current"), dict):
        summary["current"] = summarize_current_job(body["current"])
    for key in (
        "count",
        "funnel",
        "candidates_observed",
        "urls_resolved",
        "text_extracted",
        "canonical_dates_ok",
        "articles_saved",
        "skipped_by_reason",
        "sourceRunCounts",
        "sourceRunCount",
        "sourceRunSourceTypeCounts",
        "failedSources",
        "uploadedArtifacts",
        "uploadedArtifactCount",
        "limit_mib",
        "vm_rss_mib",
        "vm_hwm_mib",
        "filesystem",
        "db_files",
        "rssMiB",
        "diskFreeBytes",
        "disk_free_bytes",
        "jobId",
        "live",
        "meta",
        "metrics",
        "throughputPerHour",
        "etaSeconds",
        "lastActivity",
        "staleAlert",
        "total",
        "page",
        "pageSize",
    ):
        if key in body:
            summary[key] = body[key]
    if "items" in body:
        summary["itemCount"] = len(body.get("items") or [])
        summary["latestItems"] = [
            {
                "title": str(item.get("title") or "")[:120],
                "sourceName": item.get("sourceName"),
                "publishedAt": item.get("publishedAt"),
            }
            for item in list(body.get("items") or [])[:5]
            if isinstance(item, dict)
        ]
    if "events" in body:
        summary["eventCount"] = len(body.get("events") or [])
        summary["latestEvents"] = [
            {"event": item.get("event"), "created_at": item.get("created_at"), "payload": item.get("payload")}
            for item in list(body.get("events") or [])[:8]
            if isinstance(item, dict)
        ]
    return summary


def summarize_current_job(current: dict[str, Any]) -> dict[str, Any]:
    keep = (
        "id",
        "kind",
        "status",
        "coverageState",
        "preset",
        "target_keys",
        "collector",
        "date_from",
        "date_to",
        "started_at",
        "finished_at",
        "articles_inserted",
        "mentions_inserted",
        "stories_touched",
        "sourceRunCount",
        "sourceRunCounts",
        "sourceRunSourceTypeCounts",
        "failedSources",
        "resumeAvailable",
        "uploadedArtifactCount",
        "uploadedArtifacts",
        "publishedAt",
        "candidates_observed",
        "urls_resolved",
        "text_extracted",
        "canonical_dates_ok",
        "articles_saved",
        "skipped_by_reason",
        "funnel",
        "batchId",
        "jobId",
        "dateFrom",
        "dateTo",
        "lastActivity",
        "throughputPerHour",
        "etaSeconds",
        "staleAlert",
        "metrics",
    )
    return {key: current.get(key) for key in keep if key in current}


def current_job_id(payload: dict[str, Any]) -> str:
    current = payload.get("current") if isinstance(payload.get("current"), dict) else {}
    return str(current.get("id") or payload.get("id") or "")


def resource_barriers(snapshot: dict[str, Any], args: argparse.Namespace) -> list[str]:
    barriers: list[str] = []
    memory = snapshot.get("memory") if isinstance(snapshot.get("memory"), dict) else {}
    disk = snapshot.get("disk") if isinstance(snapshot.get("disk"), dict) else {}
    max_rss = float(getattr(args, "memory_rss_max_mib", 0) or 0)
    min_disk = float(getattr(args, "disk_free_min_mib", 0) or 0)
    if max_rss:
        rss = float(memory.get("vm_rss_mib") or 0)
        if rss and rss > max_rss:
            barriers.append(f"memory_rss_mib:{rss:.2f}>{max_rss:.2f}")
    if min_disk:
        fs = disk.get("filesystem") if isinstance(disk.get("filesystem"), dict) else {}
        free = float(fs.get("free_mib") or 0)
        if free and free < min_disk:
            barriers.append(f"disk_free_mib:{free:.2f}<{min_disk:.2f}")
    return barriers


def guard_resources_before_start(client: Client, args: argparse.Namespace, label: str) -> int:
    snapshot = poll_once(client, "")
    barriers = resource_barriers(snapshot, args)
    emit("preflight", {"label": label, "barriers": barriers, "snapshot": snapshot})
    if barriers and not getattr(args, "ignore_resource_guards", False):
        emit("preflight_blocked", {"label": label, "barriers": barriers})
        return 3
    return 0


def poll_until_done(client: Client, job_id: str, args: argparse.Namespace) -> int:
    cycles = 0
    while True:
        cycles += 1
        snapshot = poll_once(client, job_id)
        barriers = resource_barriers(snapshot, args)
        emit("poll", {"cycle": cycles, "job_id": job_id, "barriers": barriers, "snapshot": snapshot})
        current = snapshot.get("status", {}).get("current", {})
        current_status = str(current.get("status") or "")
        if current_status in {"succeeded", "completed_with_gaps", "failed", "failed_needs_fix", "cancelled", "interrupted_resumable"}:
            return 0 if current_status == "succeeded" else 2
        if args.max_cycles and cycles >= args.max_cycles:
            return 0
        time.sleep(max(5, int(args.interval)))


def run_backfill_years(client: Client, args: argparse.Namespace) -> int:
    start_year = int(args.backfill_start_year)
    end_year = int(args.backfill_end_year or args.backfill_start_year)
    windows = backfill_windows(start_year, end_year, mode=str(args.backfill_window))
    emit("backfill_plan", {"window": args.backfill_window, "windows": len(windows), "start_year": start_year, "end_year": end_year})
    for label, date_from, date_to in windows:
        guard = guard_resources_before_start(client, args, label)
        if guard:
            return guard
        args.date_from, args.date_to = date_from, date_to
        emit("backfill_window_start", {"label": label, "date_from": args.date_from, "date_to": args.date_to})
        started = start_topic_job(client, args)
        job_id = current_job_id(started)
        emit("start_ok", {"job_id": job_id, "status": started.get("status"), "label": label})
        result = poll_until_done(client, job_id, args)
        emit("backfill_window_done", {"label": label, "job_id": job_id, "exit_code": result})
        if result != 0:
            return result
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--password-env", default="CLIPPING_ADMIN_PASSWORD")
    parser.add_argument("--scope", default="rio_economico")
    parser.add_argument("--topic", default="rio_city_corpus")
    parser.add_argument("--preset", default="")
    parser.add_argument("--date-from", default="")
    parser.add_argument("--date-to", default="")
    parser.add_argument("--backfill-start-year", type=int, default=0)
    parser.add_argument("--backfill-end-year", type=int, default=0)
    parser.add_argument("--backfill-window", choices=["year", "month"], default="year")
    parser.add_argument("--collector", default="all")
    parser.add_argument("--no-export", action="store_true")
    parser.add_argument("--resume-job-id", default="")
    parser.add_argument("--resume-on-conflict", action="store_true")
    parser.add_argument("--no-start", action="store_true")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--max-cycles", type=int, default=0)
    parser.add_argument("--memory-rss-max-mib", type=float, default=0)
    parser.add_argument("--disk-free-min-mib", type=float, default=0)
    parser.add_argument("--ignore-resource-guards", action="store_true")
    args = parser.parse_args(argv)

    password = os.environ.get(args.password_env, "").strip()
    if not password:
        raise SystemExit(f"missing password env: {args.password_env}")

    client = Client(args.base_url)
    identity = client.login(password)
    emit("login_ok", {"role": identity.get("role"), "profile": identity.get("profile")})

    if args.backfill_start_year and not args.resume_job_id:
        return run_backfill_years(client, args)

    job_id = args.resume_job_id
    if args.resume_job_id:
        resumed = resume_topic_job(client, args.resume_job_id)
        job_id = current_job_id(resumed) or args.resume_job_id
        emit("resume_started", {"job_id": job_id, "status": resumed.get("status")})
    elif not args.no_start:
        started = start_topic_job(client, args)
        job_id = current_job_id(started)
        emit("start_ok", {"job_id": job_id, "status": started.get("status")})

    return poll_until_done(client, job_id, args)


if __name__ == "__main__":
    sys.exit(main())
