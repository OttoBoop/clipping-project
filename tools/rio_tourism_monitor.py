#!/usr/bin/env python3
"""Authenticated operator for Rio tourism topic jobs.

The script starts or resumes `rio_economico/tourism_events` jobs and polls the
same production endpoints an operator uses in the browser. It writes JSONL to
stdout so long backfills can be tailed or archived.
"""

from __future__ import annotations

import argparse
import json
import os
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


def start_topic_job(client: Client, args: argparse.Namespace) -> dict[str, Any]:
    date_from, date_to = args.date_from, args.date_to
    if not date_from or not date_to:
        date_from, date_to = default_canary_window()
    payload = {
        "scope": "rio_economico",
        "topic": "tourism_events",
        "date_from": date_from,
        "date_to": date_to,
        "collector": args.collector,
        "export": True,
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
        "status": ("GET", "/api/update/status"),
        "memory": ("GET", "/api/admin/debug/memory"),
        "disk": ("GET", "/api/admin/debug/disk"),
        "live": ("GET", "/api/update/live-results?scope=base&target_key=rio_economico&limit=20"),
        "rio_report": ("GET", "/api/reports/rio-economic-topic"),
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
    for key in (
        "current",
        "count",
        "sourceRunCounts",
        "sourceRunCount",
        "rssMiB",
        "diskFreeBytes",
        "disk_free_bytes",
        "jobId",
        "live",
        "meta",
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


def current_job_id(payload: dict[str, Any]) -> str:
    current = payload.get("current") if isinstance(payload.get("current"), dict) else {}
    return str(current.get("id") or payload.get("id") or "")


def poll_until_done(client: Client, job_id: str, args: argparse.Namespace) -> int:
    cycles = 0
    while True:
        cycles += 1
        snapshot = poll_once(client, job_id)
        emit("poll", {"cycle": cycles, "job_id": job_id, "snapshot": snapshot})
        current = snapshot.get("status", {}).get("current", {})
        current_status = str(current.get("status") or "")
        if current_status in {"succeeded", "failed_needs_fix", "cancelled", "interrupted_resumable"}:
            return 0 if current_status == "succeeded" else 2
        if args.max_cycles and cycles >= args.max_cycles:
            return 0
        time.sleep(max(5, int(args.interval)))


def run_backfill_years(client: Client, args: argparse.Namespace) -> int:
    start_year = int(args.backfill_start_year)
    end_year = int(args.backfill_end_year or args.backfill_start_year)
    if start_year > end_year:
        start_year, end_year = end_year, start_year
    for year in range(start_year, end_year + 1):
        args.date_from, args.date_to = year_window(year)
        emit("backfill_window_start", {"year": year, "date_from": args.date_from, "date_to": args.date_to})
        started = start_topic_job(client, args)
        job_id = current_job_id(started)
        emit("start_ok", {"job_id": job_id, "status": started.get("status"), "year": year})
        result = poll_until_done(client, job_id, args)
        emit("backfill_window_done", {"year": year, "job_id": job_id, "exit_code": result})
        if result != 0:
            return result
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--password-env", default="CLIPPING_ADMIN_PASSWORD")
    parser.add_argument("--date-from", default="")
    parser.add_argument("--date-to", default="")
    parser.add_argument("--backfill-start-year", type=int, default=0)
    parser.add_argument("--backfill-end-year", type=int, default=0)
    parser.add_argument("--collector", default="all")
    parser.add_argument("--resume-job-id", default="")
    parser.add_argument("--resume-on-conflict", action="store_true")
    parser.add_argument("--no-start", action="store_true")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--max-cycles", type=int, default=0)
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
