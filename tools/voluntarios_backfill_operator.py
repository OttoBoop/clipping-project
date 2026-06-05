#!/usr/bin/env python3
"""Production operator loop for the Voluntarios Lab backfill.

The script reads credentials from the local password note but never prints
passwords. It intentionally operates on the existing production job only.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://clipping-project.onrender.com"
JOB_ID = "0b36e332911a"
PROFILE_KEY = "voluntarios_lab_politicas"
PROFILE_LABEL = "Voluntários-Lab-Políticas-Públicas"
PASSWORD_NOTE = Path("/home/otavio/Documents/clipping-project senhas.md")
LOG_PATH = Path("md documents/voluntarios-lab-politicas-publicas-2026-06-02/LOGS.md")

EXPECTED_TARGET_KEYS = [
    "seguranca_presente",
    "programa_seguranca_presente",
    "operacao_seguranca_presente",
    "seguranca",
    "inseguranca",
    "crime",
    "criminalidade",
    "violencia",
    "assalto",
    "roubo",
    "furto",
    "medo",
    "policiamento",
    "patrulhamento",
    "percepcao_de_seguranca",
    "sensacao_de_seguranca",
    "reforco_no_policiamento",
    "ordem_publica",
]

DANGER_STATUSES = {"failed_needs_fix", "interrupted_resumable"}


@dataclass
class Response:
    status: int
    body: Any
    elapsed: float


class ProductionClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.cookies = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        csrf: str = "",
        timeout: int = 45,
        retries_on_5xx: int = 1,
    ) -> Response:
        url = urllib.parse.urljoin(self.base_url + "/", path.lstrip("/"))
        data = None
        headers = {"Accept": "application/json", "User-Agent": "voluntarios-backfill-operator/2026-06-04"}
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if csrf:
            headers["X-CSRF-Token"] = csrf

        attempts = retries_on_5xx + 1
        payload = ""
        status = 0
        content_type = ""
        started = time.time()
        for attempt in range(1, attempts + 1):
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with self.opener.open(req, timeout=timeout) as resp:
                    payload = resp.read().decode("utf-8", errors="replace")
                    status = resp.status
                    content_type = resp.headers.get("content-type", "")
            except urllib.error.HTTPError as exc:
                payload = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
                status = exc.code
                content_type = exc.headers.get("content-type", "") if exc.headers else ""
            except Exception as exc:  # noqa: BLE001 - operator diagnostics need type names.
                return Response(0, {"error": type(exc).__name__, "message": str(exc)}, round(time.time() - started, 2))
            if status < 500:
                break
            if attempt < attempts:
                time.sleep(3)

        parsed: Any
        if "json" in content_type:
            try:
                parsed = json.loads(payload) if payload else {}
            except json.JSONDecodeError:
                parsed = payload
        else:
            try:
                parsed = json.loads(payload) if payload else {}
            except json.JSONDecodeError:
                parsed = payload
        return Response(status, parsed, round(time.time() - started, 2))


def now_label() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def parse_target_keys(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item or "").strip()]
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return [item.strip() for item in text.split(",") if item.strip()]
        return parse_target_keys(parsed)
    return []


def parse_spec_json(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def normalize_targets_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    rows = payload.get("targets")
    if isinstance(rows, dict):
        rows = rows.get("targets")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    return []


def target_contract(targets_payload: Any) -> dict[str, Any]:
    rows = normalize_targets_payload(targets_payload)
    keys = [str(row.get("key") or "") for row in rows if row.get("key")]
    primary = [
        str(row.get("key") or "")
        for row in rows
        if row.get("key") and row.get("primary") is True and str(row.get("className") or "") == "primary"
    ]
    return {
        "count": len(keys),
        "missing": [key for key in EXPECTED_TARGET_KEYS if key not in keys],
        "extra": [key for key in keys if key not in EXPECTED_TARGET_KEYS],
        "primaryExact": primary == EXPECTED_TARGET_KEYS,
    }


def parse_password_note(text: str) -> dict[str, Any]:
    candidates: list[str] = []
    candidates.extend(re.findall(r"`([^`]{3,})`", text))
    for line in text.splitlines():
        low = line.lower()
        if any(marker in low for marker in ("senha", "password", "admin", PROFILE_KEY.lower())):
            if ":" in line:
                candidates.append(line.split(":", 1)[1].strip().strip("`").strip())
            cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
            candidates.extend(cells)
    cleaned: list[str] = []
    seen: set[str] = set()
    rejected = {
        "senha",
        "password",
        "role",
        "profile",
        "admin",
        "viewer",
        "produção",
        "producao",
        "viewer password",
        "production viewer password",
    }
    for value in candidates:
        clean = str(value or "").strip()
        low = clean.lower()
        if not clean or clean in seen or clean.startswith("["):
            continue
        if low in rejected or low.startswith(("http", "site", "estado", "o que")):
            continue
        if PROFILE_LABEL.lower() in low or PROFILE_KEY.lower() in low:
            continue
        cleaned.append(clean)
        seen.add(clean)

    viewer_password = ""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if PROFILE_KEY in line or PROFILE_LABEL in line:
            for follow in lines[index + 1 : index + 8]:
                if "password" in follow.lower() or "senha" in follow.lower():
                    if ":" in follow:
                        viewer_password = follow.split(":", 1)[1].strip().strip("`").strip()
                        break
            if viewer_password:
                break
    return {"candidates": cleaned, "viewerPassword": viewer_password}


def load_password_note() -> dict[str, Any]:
    return parse_password_note(PASSWORD_NOTE.read_text(encoding="utf-8"))


def login_with_candidates(
    base_url: str,
    *,
    role: str,
    profile: str = "",
    candidates: list[str],
) -> tuple[ProductionClient | None, dict[str, Any]]:
    successes: list[dict[str, str]] = []
    for password in candidates:
        client = ProductionClient(base_url)
        response = client.request("POST", "/api/login", body={"password": password}, timeout=25, retries_on_5xx=2)
        if response.status == 200 and isinstance(response.body, dict):
            observed = {"role": str(response.body.get("role") or ""), "profile": str(response.body.get("profile") or "")}
            successes.append(observed)
            if observed["role"] == role and (not profile or observed["profile"] == profile):
                return client, {"ok": True, "elapsed": response.elapsed, "successes": successes}
    return None, {"ok": False, "successes": successes}


def login_with_password(
    base_url: str,
    *,
    password: str,
    role: str,
    profile: str = "",
) -> tuple[ProductionClient | None, dict[str, Any]]:
    if not password:
        return None, {"ok": False, "reason": "missing_saved_password"}
    client = ProductionClient(base_url)
    response = client.request("POST", "/api/login", body={"password": password}, timeout=25, retries_on_5xx=2)
    ok = (
        response.status == 200
        and isinstance(response.body, dict)
        and response.body.get("role") == role
        and (not profile or response.body.get("profile") == profile)
    )
    return (client if ok else None), {
        "ok": ok,
        "http": response.status,
        "elapsed": response.elapsed,
        "role": response.body.get("role") if isinstance(response.body, dict) else "",
        "profile": response.body.get("profile") if isinstance(response.body, dict) else "",
    }


def require_admin(base_url: str) -> tuple[ProductionClient, str, dict[str, Any]]:
    note = load_password_note()
    admin, login = login_with_candidates(base_url, role="admin", profile="admin", candidates=note["candidates"])
    if not admin:
        raise RuntimeError(f"admin login failed; successful non-secret identities: {login.get('successes')}")
    csrf_response = admin.request("GET", "/api/csrf", timeout=25)
    if csrf_response.status != 200 or not isinstance(csrf_response.body, dict) or not csrf_response.body.get("csrf"):
        raise RuntimeError(f"csrf fetch failed: HTTP {csrf_response.status}")
    return admin, str(csrf_response.body["csrf"]), login


def summarize_status(payload: Any) -> dict[str, Any]:
    current = payload.get("current") if isinstance(payload, dict) else {}
    current = current if isinstance(current, dict) else {}
    spec = parse_spec_json(current.get("spec_json") or current.get("spec") or {})
    target_keys = parse_target_keys(spec.get("target_keys") or current.get("target_keys"))
    return {
        "jobId": str(current.get("id") or current.get("job_id") or ""),
        "status": str(current.get("status") or ""),
        "coverage": str(current.get("coverageState") or current.get("sourceCoverageState") or current.get("source_coverage_state") or ""),
        "resumeAvailable": bool(current.get("resumeAvailable") or current.get("resume_available")),
        "dateFrom": str(current.get("date_from") or spec.get("date_from") or ""),
        "dateTo": str(current.get("date_to") or spec.get("date_to") or ""),
        "collector": str(current.get("collector") or spec.get("collector") or ""),
        "preset": str(current.get("preset") or spec.get("preset") or ""),
        "targetKeys": target_keys,
        "targetKeysExact": target_keys == EXPECTED_TARGET_KEYS,
        "sourceRunCount": int(current.get("sourceRunCount") or current.get("source_run_count") or 0),
        "sourceRunCounts": current.get("sourceRunCounts") or current.get("source_run_counts") or {},
        "currentTarget": str(current.get("currentTarget") or current.get("current_target") or ""),
        "currentSource": str(current.get("currentSource") or current.get("current_source") or ""),
        "articles": current.get("articles_inserted") or current.get("articleCount") or current.get("articlesCount"),
        "mentions": current.get("mentions_inserted") or current.get("mentionCount") or current.get("mentionsCount"),
        "stories": current.get("stories_touched") or current.get("storyCount") or current.get("storiesCount"),
        "publishedAt": str(current.get("publishedAt") or current.get("published_at") or ""),
        "error": str(current.get("error_message") or current.get("error") or ""),
    }


def summarize_asset(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    return {
        "generatedAt": str(payload.get("generatedAt") or payload.get("generated_at") or meta.get("generatedAt") or ""),
        "storiesLen": len(payload.get("stories") or []),
        "targetsLen": len(payload.get("targets") or []),
        "totalStories": meta.get("totalStories") or payload.get("totalStories"),
        "totalArticles": meta.get("totalArticles") or payload.get("totalArticles"),
        "viewerRole": meta.get("viewerRole"),
        "viewerProfile": meta.get("viewerProfile"),
    }


def summarize_live_results(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    items = payload.get("items") or payload.get("results") or []
    if not isinstance(items, list):
        items = []
    timestamps = [
        str(item.get("savedAt") or item.get("saved_at") or item.get("publishedAt") or item.get("published_at") or "")
        for item in items
        if isinstance(item, dict)
    ]
    states = Counter(
        str(item.get("state") or item.get("status") or "")
        for item in items
        if isinstance(item, dict)
    )
    return {"count": len(items), "latestTimestamp": max(timestamps or [""]), "states": dict(states)}


def summarize_events(payload: Any) -> dict[str, Any]:
    events = payload.get("events") if isinstance(payload, dict) else []
    if not isinstance(events, list):
        events = []
    latest: list[dict[str, Any]] = []
    for event in events[:8]:
        if not isinstance(event, dict):
            continue
        details = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        latest.append(
            {
                "at": event.get("created_at") or event.get("createdAt"),
                "event": event.get("event") or event.get("type") or event.get("event_type"),
                "target": details.get("target_key") or event.get("target_key"),
                "source": details.get("source_name") or event.get("source_name"),
                "status": details.get("status") or event.get("status"),
                "error": str(details.get("error") or details.get("message") or "")[:220],
            }
        )
    return {"count": len(events), "latest": latest}


def summarize_viewer_profile(payload: Any) -> dict[str, Any]:
    rows = payload.get("viewers") if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        rows = []
    match = next((row for row in rows if isinstance(row, dict) and row.get("profile") == PROFILE_KEY), None)
    if not match:
        return {"found": False, "profileCount": len(rows)}
    target_keys = [str(key) for key in match.get("target_keys") or []]
    default_targets = [str(key) for key in match.get("default_targets") or []]
    return {
        "found": True,
        "label": match.get("label"),
        "hasPassword": bool(match.get("has_password")),
        "targetKeysCount": len(target_keys),
        "defaultTargetsCount": len(default_targets),
        "missing": [key for key in EXPECTED_TARGET_KEYS if key not in target_keys],
        "extra": [key for key in target_keys if key not in EXPECTED_TARGET_KEYS],
        "defaultsMissing": [key for key in EXPECTED_TARGET_KEYS if key not in default_targets],
        "defaultsExtra": [key for key in default_targets if key not in EXPECTED_TARGET_KEYS],
        "targetKeys": target_keys,
        "defaultTargets": default_targets,
    }


def storage_report_from_env(limit: int = 100) -> dict[str, Any]:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    bucket = os.environ.get("SUPABASE_BUCKET", "documentos").strip() or "documentos"
    prefix = os.environ.get("CLIPPING_STORAGE_PREFIX", "clipping-project").strip().strip("/") or "clipping-project"
    if not (url and key and bucket and prefix):
        return {"enabled": False, "reason": "supabase_env_not_available_locally", "prefix": prefix}

    def list_prefix(path_prefix: str) -> dict[str, Any]:
        endpoint = f"{url}/storage/v1/object/list/{urllib.parse.quote(bucket, safe='')}"
        body = {
            "prefix": path_prefix,
            "limit": limit,
            "offset": 0,
            "sortBy": {"column": "updated_at", "order": "desc"},
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "voluntarios-backfill-operator/2026-06-04",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": type(exc).__name__, "message": str(exc)[:200]}
        rows = payload if isinstance(payload, list) else []
        objects = []
        for row in rows[:limit]:
            if not isinstance(row, dict):
                continue
            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            objects.append(
                {
                    "name": row.get("name"),
                    "updatedAt": row.get("updated_at") or row.get("updatedAt"),
                    "createdAt": row.get("created_at") or row.get("createdAt"),
                    "size": metadata.get("size") or row.get("size"),
                    "etag": metadata.get("eTag") or metadata.get("etag"),
                }
            )
        return {"ok": True, "prefix": path_prefix, "count": len(objects), "objects": objects}

    return {
        "enabled": True,
        "bucket": bucket,
        "prefix": prefix,
        "current": list_prefix(f"{prefix}/current"),
        "runs": list_prefix(f"{prefix}/runs"),
        "backups": list_prefix(f"{prefix}/backups"),
    }


def audit(base_url: str) -> dict[str, Any]:
    note = load_password_note()
    admin, _csrf, admin_login = require_admin(base_url)
    _viewer, viewer_login = login_with_password(
        base_url,
        password=str(note.get("viewerPassword") or ""),
        role="viewer",
        profile=PROFILE_KEY,
    )

    endpoints = {
        "health": admin.request("GET", "/healthz", timeout=45, retries_on_5xx=2),
        "status": admin.request("GET", "/api/update/status", timeout=70, retries_on_5xx=2),
        "memory": admin.request("GET", "/api/admin/debug/memory", timeout=45, retries_on_5xx=2),
        "disk": admin.request("GET", "/api/admin/debug/disk", timeout=45, retries_on_5xx=2),
        "sqlite": admin.request("POST", "/api/admin/debug/sqlite", body={"action": "report"}, csrf=_csrf, timeout=70),
        "events": admin.request("GET", f"/api/admin/jobs/{JOB_ID}/source-run-events?limit=30", timeout=45),
        "live": admin.request("GET", "/api/update/live-results?scope=base&limit=60", timeout=45),
        "asset": admin.request("GET", f"/assets/clipping-data.json?cb={int(time.time())}", timeout=70),
        "targets": admin.request("GET", f"/api/targets?as_profile={urllib.parse.quote(PROFILE_KEY)}", timeout=45),
        "viewers": admin.request("GET", "/api/admin/viewers", timeout=45),
    }
    summary = {
        "sampledAt": now_label(),
        "baseUrl": base_url,
        "jobId": JOB_ID,
        "adminLogin": {"ok": bool(admin_login.get("ok")), "elapsed": admin_login.get("elapsed")},
        "viewerLogin": viewer_login,
        "http": {name: {"status": resp.status, "elapsed": resp.elapsed} for name, resp in endpoints.items()},
        "health": endpoints["health"].body if isinstance(endpoints["health"].body, dict) else {},
        "status": summarize_status(endpoints["status"].body),
        "memory": endpoints["memory"].body if isinstance(endpoints["memory"].body, dict) else {},
        "disk": endpoints["disk"].body if isinstance(endpoints["disk"].body, dict) else {},
        "sqlite": summarize_sqlite(endpoints["sqlite"].body),
        "events": summarize_events(endpoints["events"].body),
        "live": summarize_live_results(endpoints["live"].body),
        "asset": summarize_asset(endpoints["asset"].body),
        "targets": target_contract(endpoints["targets"].body),
        "viewerProfile": summarize_viewer_profile(endpoints["viewers"].body),
        "storage": storage_report_from_env(),
    }
    summary["barriers"] = detect_barriers(summary)
    return summary


def summarize_sqlite(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    file_state = payload.get("fileState") if isinstance(payload.get("fileState"), dict) else {}
    files = file_state.get("files") if isinstance(file_state.get("files"), dict) else {}
    probes = payload.get("probes") if isinstance(payload.get("probes"), dict) else {}
    compact_probes: dict[str, Any] = {}
    for name, probe in probes.items():
        if isinstance(probe, dict):
            compact_probes[name] = {
                "journalMode": probe.get("journalMode"),
                "quickCheck": probe.get("quickCheck"),
                "jobsCount": probe.get("jobsCount"),
                "activeJobsCount": probe.get("activeJobsCount"),
                "jobEventsCount": probe.get("jobEventsCount"),
                "connectErrorType": probe.get("connectErrorType"),
                "queryError": probe.get("queryError"),
            }
    return {"files": files, "probes": compact_probes}


def detect_barriers(summary: dict[str, Any], previous: dict[str, Any] | None = None) -> list[str]:
    barriers: list[str] = []
    status = summary.get("status") or {}
    status_name = str(status.get("status") or "")
    coverage = str(status.get("coverage") or "")
    if status_name in DANGER_STATUSES:
        barriers.append(f"job_status:{status_name}")
    if coverage in DANGER_STATUSES:
        barriers.append(f"coverage:{coverage}")
    if status.get("jobId") and status.get("jobId") != JOB_ID:
        barriers.append(f"unexpected_job:{status.get('jobId')}")
    if not status.get("targetKeysExact"):
        barriers.append("target_keys_not_exact")
    if status.get("dateFrom") != "2014-01-01" or status.get("dateTo") != "2026-06-02":
        barriers.append("date_range_mismatch")
    if summary.get("viewerLogin", {}).get("ok") is not True:
        barriers.append("viewer_login_failed")
    if summary.get("targets", {}).get("primaryExact") is not True:
        barriers.append("target_contract_failed")
    viewer_profile = summary.get("viewerProfile") or {}
    if not viewer_profile.get("found") or viewer_profile.get("missing") or viewer_profile.get("extra"):
        barriers.append("viewer_profile_target_scope_failed")
    for name, info in (summary.get("http") or {}).items():
        http_status = int(info.get("status") or 0)
        elapsed = float(info.get("elapsed") or 0)
        if http_status >= 500 or http_status == 0:
            barriers.append(f"endpoint_failed:{name}:{http_status}")
        if elapsed >= 30:
            barriers.append(f"endpoint_slow:{name}:{elapsed}")
    memory = summary.get("memory") if isinstance(summary.get("memory"), dict) else {}
    rss = float(memory.get("vm_rss_mib") or 0)
    if rss >= 430:
        barriers.append(f"memory_rss_danger:{rss}")
    disk = summary.get("disk") if isinstance(summary.get("disk"), dict) else {}
    filesystem = disk.get("filesystem") if isinstance(disk.get("filesystem"), dict) else {}
    if float(filesystem.get("free_mib") or 999999) < 1024:
        barriers.append("disk_free_below_1gib")
    sqlite = summary.get("sqlite") if isinstance(summary.get("sqlite"), dict) else {}
    probes = sqlite.get("probes") if isinstance(sqlite.get("probes"), dict) else {}
    for label, probe in probes.items():
        if isinstance(probe, dict) and probe.get("quickCheck") not in (None, "ok"):
            barriers.append(f"sqlite_quick_check_failed:{label}:{probe.get('quickCheck')}")

    if previous:
        counts = status.get("sourceRunCounts") or {}
        prev_counts = (previous.get("status") or {}).get("sourceRunCounts") or {}
        current_marker = (status.get("currentTarget"), status.get("currentSource"), counts)
        previous_marker = (
            (previous.get("status") or {}).get("currentTarget"),
            (previous.get("status") or {}).get("currentSource"),
            prev_counts,
        )
        if current_marker == previous_marker and status_name == "running":
            barriers.append("no_source_progress_since_previous_cycle")
    return barriers


def markdown_entry(title: str, summary: dict[str, Any]) -> str:
    if "ui" in summary and not summary.get("status"):
        return ui_markdown_entry(title, summary)

    status = summary.get("status") or {}
    asset = summary.get("asset") or {}
    live = summary.get("live") or {}
    memory = summary.get("memory") if isinstance(summary.get("memory"), dict) else {}
    disk = summary.get("disk") if isinstance(summary.get("disk"), dict) else {}
    filesystem = disk.get("filesystem") if isinstance(disk.get("filesystem"), dict) else {}
    sqlite_files = (summary.get("sqlite") or {}).get("files") or {}
    db_file = sqlite_files.get("clipping.db") if isinstance(sqlite_files.get("clipping.db"), dict) else {}
    storage = summary.get("storage") if isinstance(summary.get("storage"), dict) else {}
    lines = [
        "",
        f"## {summary.get('sampledAt', now_label())} - {title}",
        "",
        f"- Job `{status.get('jobId')}` status `{status.get('status')}`, coverage `{status.get('coverage') or 'n/a'}`, resumeAvailable `{status.get('resumeAvailable')}`.",
        f"- Contract: date `{status.get('dateFrom')}` to `{status.get('dateTo')}`, collector `{status.get('collector')}`, preset `{status.get('preset')}`, exact 18 keys `{status.get('targetKeysExact')}`.",
        f"- Source ledger: total `{status.get('sourceRunCount')}`, counts `{json.dumps(status.get('sourceRunCounts') or {}, ensure_ascii=False, sort_keys=True)}`.",
        f"- Current target/source: `{status.get('currentTarget') or 'n/a'}` / `{status.get('currentSource') or 'n/a'}`.",
        f"- Totals/status fields: articles `{status.get('articles')}`, mentions `{status.get('mentions')}`, stories `{status.get('stories')}`, publishedAt `{status.get('publishedAt')}`.",
        f"- Website asset: generatedAt `{asset.get('generatedAt')}`, stories `{asset.get('totalStories') or asset.get('storiesLen')}`, articles `{asset.get('totalArticles')}`, targets `{asset.get('targetsLen')}`.",
        f"- Live results: latest `{live.get('latestTimestamp')}`, count `{live.get('count')}`.",
        f"- Viewer profile/login: login ok `{(summary.get('viewerLogin') or {}).get('ok')}`, profile `{summary.get('viewerProfile')}`.",
        f"- Target contract: `{summary.get('targets')}`.",
        f"- Memory: VmRSS `{memory.get('vm_rss_mib')}` MiB, VmHWM `{memory.get('vm_hwm_mib')}` MiB, limit `{memory.get('limit_mib')}` MiB.",
        f"- Disk: free `{filesystem.get('free_mib')}` MiB, DB `{db_file.get('size_mib')}` MiB.",
        f"- Storage diagnostic: enabled `{storage.get('enabled')}`, reason `{storage.get('reason', '')}`.",
        f"- HTTP timings/status: `{json.dumps(summary.get('http') or {}, ensure_ascii=False, sort_keys=True)}`.",
        f"- Recent source events: `{json.dumps((summary.get('events') or {}).get('latest') or [], ensure_ascii=False)}`.",
        f"- Barriers: `{json.dumps(summary.get('barriers') or [], ensure_ascii=False)}`.",
    ]
    return "\n".join(lines) + "\n"


def ui_markdown_entry(title: str, summary: dict[str, Any]) -> str:
    ui = summary.get("ui") if isinstance(summary.get("ui"), dict) else {}
    lines = [
        "",
        f"## {summary.get('sampledAt', now_label())} - {title}",
        "",
        f"- Profile listed: `{ui.get('profileListed')}`.",
        f"- Viewer login HTTP: `{ui.get('loginHttp')}`; `/api/targets` HTTP: `{ui.get('targetsHttp')}`.",
        f"- Target contract: `{ui.get('targetContract')}`.",
        f"- Primary keys exact: `{ui.get('primaryExact')}`; default-checked exact: `{ui.get('checkedPrimaryExact')}`.",
        f"- Primary keys: `{json.dumps(ui.get('primaryKeys') or [], ensure_ascii=False)}`.",
        f"- Checked primary keys: `{json.dumps(ui.get('checkedPrimary') or [], ensure_ascii=False)}`.",
        f"- Secondary keys: `{json.dumps(ui.get('secondaryKeys') or [], ensure_ascii=False)}`; secondary empty `{ui.get('secondaryEmpty')}`.",
        f"- Runner status: `{ui.get('runnerStatus')}`.",
        f"- Browser errors/warnings: `{json.dumps(ui.get('errors') or [], ensure_ascii=False)}`.",
        f"- Barriers: `{json.dumps(summary.get('barriers') or [], ensure_ascii=False)}`.",
    ]
    return "\n".join(lines) + "\n"


def append_log(title: str, summary: dict[str, Any], log_path: Path = LOG_PATH) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(markdown_entry(title, summary))


def update_password_note(new_password: str, path: Path = PASSWORD_NOTE) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    output: list[str] = []
    in_block = False
    replaced = False
    for line in lines:
        if line.startswith("## "):
            in_block = PROFILE_KEY in line or PROFILE_LABEL in line
        if in_block and "Production viewer password:" in line:
            output.append(f"- Production viewer password: {new_password}")
            replaced = True
        else:
            output.append(line)
    if not replaced:
        output.extend(
            [
                "",
                f"## {PROFILE_LABEL} ({PROFILE_KEY}) - {now_label()}",
                f"- Production viewer password: {new_password}",
            ]
        )
    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def repair_password(base_url: str, *, log: bool) -> dict[str, Any]:
    before = audit(base_url)
    if before.get("viewerLogin", {}).get("ok"):
        before["passwordRepair"] = {"changed": False, "reason": "saved_password_already_valid"}
        if log:
            append_log("Password Repair Skipped", before)
        return before

    admin, csrf, _admin_login = require_admin(base_url)
    viewers_response = admin.request("GET", "/api/admin/viewers", timeout=45)
    profile = summarize_viewer_profile(viewers_response.body)
    if not profile.get("found"):
        raise RuntimeError(f"{PROFILE_KEY} profile not found in production")
    target_keys = profile.get("targetKeys") or EXPECTED_TARGET_KEYS
    default_targets = profile.get("defaultTargets") or EXPECTED_TARGET_KEYS
    new_password = secrets.token_urlsafe(30)
    patch_response = admin.request(
        "PATCH",
        f"/api/admin/viewers/{urllib.parse.quote(PROFILE_KEY)}",
        csrf=csrf,
        body={
            "label": PROFILE_LABEL,
            "target_keys": target_keys,
            "default_targets": default_targets,
            "password": new_password,
        },
        timeout=70,
        retries_on_5xx=2,
    )
    if patch_response.status != 200:
        raise RuntimeError(f"viewer password patch failed: HTTP {patch_response.status}")
    update_password_note(new_password)
    _viewer, viewer_login = login_with_password(base_url, password=new_password, role="viewer", profile=PROFILE_KEY)
    after = audit(base_url)
    after["passwordRepair"] = {
        "changed": True,
        "patchHttp": patch_response.status,
        "viewerLoginAfterPatch": viewer_login,
    }
    if log:
        append_log("Password Repair Applied", after)
    return after


def resume_same_job(base_url: str, *, log: bool) -> dict[str, Any]:
    before = audit(base_url)
    status = before.get("status") or {}
    if status.get("jobId") != JOB_ID:
        raise RuntimeError(f"refusing to resume unexpected job {status.get('jobId')}")
    if status.get("status") == "running":
        before["resume"] = {"changed": False, "reason": "already_running"}
        if log:
            append_log("Resume Skipped Already Running", before)
        return before
    if status.get("status") != "interrupted_resumable" and not status.get("resumeAvailable"):
        raise RuntimeError(f"job is not resumable: {status.get('status')}")
    if not status.get("targetKeysExact"):
        raise RuntimeError("refusing to resume because target keys are not exact")
    if status.get("dateFrom") != "2014-01-01" or status.get("dateTo") != "2026-06-02":
        raise RuntimeError("refusing to resume because date range is wrong")

    admin, csrf, _admin_login = require_admin(base_url)
    response = admin.request(
        "POST",
        "/api/update/resume",
        csrf=csrf,
        body={"job_id": JOB_ID},
        timeout=70,
        retries_on_5xx=2,
    )
    if response.status != 200:
        raise RuntimeError(f"resume failed: HTTP {response.status} {response.body}")
    time.sleep(8)
    after = audit(base_url)
    after["resume"] = {"changed": True, "http": response.status, "bodyStatus": response.body.get("status") if isinstance(response.body, dict) else ""}
    if log:
        append_log("Resumed Same Production Job", after)
    return after


def monitor(
    base_url: str,
    *,
    cycles: int,
    interval: int,
    log: bool,
    stop_on_barrier: bool,
    stall_cycles: int,
    memory_danger_cycles: int,
) -> dict[str, Any]:
    previous: dict[str, Any] | None = None
    last: dict[str, Any] = {}
    stable_cycles = 0
    high_memory_cycles = 0
    for cycle in range(1, cycles + 1):
        summary = audit(base_url)
        summary["monitorCycle"] = {"cycle": cycle, "cycles": cycles, "intervalSeconds": interval}
        summary["barriers"] = detect_barriers(summary)
        memory_barriers = [barrier for barrier in summary["barriers"] if barrier.startswith("memory_rss_danger:")]
        if memory_barriers:
            high_memory_cycles += 1
            summary["monitorCycle"]["highMemoryCycles"] = high_memory_cycles
            if high_memory_cycles < max(1, memory_danger_cycles):
                summary.setdefault("warnings", []).extend(memory_barriers)
                summary["barriers"] = [barrier for barrier in summary["barriers"] if not barrier.startswith("memory_rss_danger:")]
        else:
            high_memory_cycles = 0
        if previous:
            status = summary.get("status") or {}
            prev_status = previous.get("status") or {}
            live = summary.get("live") or {}
            marker = (
                status.get("currentTarget"),
                status.get("currentSource"),
                status.get("sourceRunCounts"),
                status.get("articles"),
                status.get("mentions"),
                status.get("stories"),
                status.get("publishedAt"),
                live.get("latestTimestamp"),
            )
            prev_marker = (
                prev_status.get("currentTarget"),
                prev_status.get("currentSource"),
                prev_status.get("sourceRunCounts"),
                prev_status.get("articles"),
                prev_status.get("mentions"),
                prev_status.get("stories"),
                prev_status.get("publishedAt"),
                (previous.get("live") or {}).get("latestTimestamp"),
            )
            stable_cycles = stable_cycles + 1 if marker == prev_marker and status.get("status") == "running" else 0
            summary["monitorCycle"]["stableCycles"] = stable_cycles
            if stable_cycles >= max(1, stall_cycles):
                summary["barriers"].append(f"source_stall_cycles:{stable_cycles}")
        if log:
            append_log(f"Monitor Cycle {cycle}", summary)
        print(redacted_json(summary))
        last = summary
        if summary["barriers"] and stop_on_barrier:
            return summary
        previous = summary
        if cycle < cycles:
            time.sleep(interval)
    return last


def run_ui_check(base_url: str, *, log: bool) -> dict[str, Any]:
    note = load_password_note()
    password = str(note.get("viewerPassword") or "")
    if not password:
        raise RuntimeError("viewer password missing from password note")
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Playwright is not available: {exc}") from exc

    result: dict[str, Any] = {"sampledAt": now_label(), "baseUrl": base_url, "ui": {}}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        errors: list[str] = []
        page.on("console", lambda msg: errors.append(f"console:{msg.type}:{msg.text}") if msg.type in {"error", "warning"} else None)
        page.on("pageerror", lambda exc: errors.append(f"pageerror:{exc}"))
        page.goto(base_url, wait_until="networkidle", timeout=60000)
        profile_options = page.locator("#profileSelect option").all_text_contents()
        matching_profile = next((option for option in profile_options if PROFILE_LABEL in option), "")
        if matching_profile:
            page.locator("#profileSelect").select_option(label=matching_profile)
        else:
            page.locator("#profileSelect").select_option("auth")
        page.locator('input[type="password"]').fill(password)
        with page.expect_response(lambda response: "/api/login" in response.url, timeout=60000) as login_response_info:
            page.locator("#loginButton").click()
        login_status = login_response_info.value.status
        errors.clear()
        page.wait_for_timeout(5000)
        targets_payload = page.evaluate(
            """async () => {
                const r = await fetch('/api/targets', {credentials: 'same-origin'});
                return {status: r.status, body: await r.json()};
            }"""
        )
        primary_keys = page.locator("#primaryRunTargets input[type='checkbox']").evaluate_all(
            "(nodes) => nodes.map((node) => node.value)"
        )
        secondary_keys = page.locator("#secondaryRunTargets input[type='checkbox']").evaluate_all(
            "(nodes) => nodes.map((node) => node.value)"
        )
        checked_primary = page.locator("#primaryRunTargets input[type='checkbox']:checked").evaluate_all(
            "(nodes) => nodes.map((node) => node.value)"
        )
        status_pill = page.locator("#runnerStatusPill").inner_text(timeout=10000)
        result["ui"] = {
            "profileListed": any(PROFILE_LABEL in option for option in profile_options),
            "loginHttp": login_status,
            "targetsHttp": targets_payload.get("status"),
            "targetContract": target_contract(targets_payload.get("body")),
            "primaryKeys": primary_keys,
            "checkedPrimary": checked_primary,
            "secondaryKeys": secondary_keys,
            "primaryExact": primary_keys == EXPECTED_TARGET_KEYS,
            "checkedPrimaryExact": checked_primary == EXPECTED_TARGET_KEYS,
            "secondaryEmpty": secondary_keys == [],
            "runnerStatus": status_pill,
            "errors": errors[:20],
        }
        browser.close()
    if log:
        append_log("Playwright UI Contract Check", {"sampledAt": result["sampledAt"], **result, "barriers": ui_barriers(result)})
    return result


def ui_barriers(result: dict[str, Any]) -> list[str]:
    ui = result.get("ui") or {}
    barriers: list[str] = []
    for key in ("profileListed", "primaryExact", "checkedPrimaryExact", "secondaryEmpty"):
        if ui.get(key) is not True:
            barriers.append(f"ui_{key}_failed")
    if ui.get("loginHttp") != 200:
        barriers.append(f"ui_login_http:{ui.get('loginHttp')}")
    if ui.get("targetsHttp") != 200:
        barriers.append(f"ui_targets_http:{ui.get('targetsHttp')}")
    if (ui.get("targetContract") or {}).get("primaryExact") is not True:
        barriers.append("ui_target_contract_failed")
    if ui.get("errors"):
        barriers.append("ui_console_or_page_errors")
    return barriers


def redacted_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Operate the Voluntarios production backfill loop.")
    parser.add_argument("mode", choices=["audit", "repair-password", "resume-same-job", "monitor", "ui-check"])
    parser.add_argument("--base", default=DEFAULT_BASE_URL)
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--stall-cycles", type=int, default=3)
    parser.add_argument("--memory-danger-cycles", type=int, default=2)
    parser.add_argument("--no-log", action="store_true")
    parser.add_argument("--continue-on-barrier", action="store_true")
    args = parser.parse_args(argv)

    log = not args.no_log
    if args.mode == "audit":
        summary = audit(args.base)
        if log:
            append_log("Production Recovery Baseline", summary)
        print(redacted_json(summary))
        return 0 if not summary.get("barriers") else 3
    if args.mode == "repair-password":
        summary = repair_password(args.base, log=log)
        print(redacted_json(summary))
        return 0 if summary.get("viewerLogin", {}).get("ok") else 3
    if args.mode == "resume-same-job":
        summary = resume_same_job(args.base, log=log)
        print(redacted_json(summary))
        return 0
    if args.mode == "monitor":
        summary = monitor(
            args.base,
            cycles=args.cycles,
            interval=args.interval,
            log=log,
            stop_on_barrier=not args.continue_on_barrier,
            stall_cycles=args.stall_cycles,
            memory_danger_cycles=args.memory_danger_cycles,
        )
        return 0 if not summary.get("barriers") else 3
    if args.mode == "ui-check":
        result = run_ui_check(args.base, log=log)
        print(redacted_json(result))
        return 0 if not ui_barriers(result) else 3
    raise AssertionError(args.mode)


if __name__ == "__main__":
    sys.exit(main())
