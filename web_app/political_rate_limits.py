"""Shared publisher cooldowns, independent of task retry budgets and HTTP clients."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import math
from urllib.parse import urlparse


DEFAULT_429_COOLDOWN_SECONDS = 60


def normalize_domain(hostname: str) -> str:
    host = str(hostname or "").strip().lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    try:
        return host.encode("idna").decode("ascii")
    except UnicodeError:
        return host


def task_request_domain(kind: str, payload: dict, source_domains: dict[str, str]) -> str:
    if kind == "review":
        return ""
    if kind == "discovery" and payload.get("strategy") == "google_news":
        return "news.google.com"
    if payload.get("url"):
        try:
            return normalize_domain(urlparse(str(payload["url"])).hostname or "")
        except ValueError:
            return ""
    return normalize_domain(source_domains.get(str(payload.get("source_key") or ""), ""))


def retry_after_deadline(value: str | None, *, now: datetime | None = None) -> datetime | None:
    """Parse delta seconds or an HTTP date, preserving deadlines beyond one hour."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    raw = str(value or "").strip()
    if not raw or len(raw) > 256:
        return None
    try:
        seconds = float(raw)
    except ValueError:
        try:
            deadline = parsedate_to_datetime(raw)
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            return max(now, deadline.astimezone(timezone.utc))
        except (ValueError, TypeError, OverflowError):
            return None
    if not math.isfinite(seconds) or seconds < 0:
        return None
    try:
        return now + timedelta(seconds=seconds)
    except OverflowError:
        # An unrepresentably long valid delay must never turn into an early retry.
        return datetime.max.replace(tzinfo=timezone.utc)


def remaining_seconds(deadline: datetime, *, now: datetime | None = None) -> int:
    return max(0, math.ceil((deadline - (now or datetime.now(timezone.utc))).total_seconds()))


class DomainCooldown(Exception):
    """Scheduling deferral: no new HTTP attempt or per-task retry was consumed."""

    def __init__(self, domain: str, retry_at: datetime):
        super().__init__("domain_cooldown")
        self.domain = normalize_domain(domain)
        self.retry_at = retry_at
        self.retryable = True
        self.retry_after = remaining_seconds(retry_at)


def domain_deferral(error: Exception) -> DomainCooldown | None:
    # Discovery wraps fetch failures with `raise ... from exc`; keep its module
    # independent while recovering this scheduling signal before generic retries.
    current = error
    for _ in range(5):
        if isinstance(current, DomainCooldown):
            return current
        current = getattr(current, "__cause__", None)
        if current is None:
            break
    return None


def active_cooldown(conn, domain: str) -> datetime | None:
    row = conn.execute("""SELECT cooldown_until FROM political_domain_limits
        WHERE domain=%s AND cooldown_until>clock_timestamp()""", (normalize_domain(domain),)).fetchone()
    return row["cooldown_until"] if row else None


def record_response_cooldown(conn, domain: str, status_code: int, retry_after: str | None) -> datetime | None:
    """429 always backs off; 503 only shares an explicit Retry-After deadline.

    401/403 do not create a retry policy or change existing access restrictions.
    Database time anchors delta seconds consistently across worker processes.
    """
    if status_code not in {429, 503}:
        return None
    now = conn.execute("SELECT clock_timestamp() AS now").fetchone()["now"]
    deadline = retry_after_deadline(retry_after, now=now)
    if deadline is None:
        if status_code != 429:
            return None
        deadline = now + timedelta(seconds=DEFAULT_429_COOLDOWN_SECONDS)
    row = conn.execute("""INSERT INTO political_domain_limits(domain,cooldown_until,cooldown_status)
        VALUES (%s,%s,%s) ON CONFLICT(domain) DO UPDATE SET
        cooldown_until=GREATEST(political_domain_limits.cooldown_until,EXCLUDED.cooldown_until),
        cooldown_status=CASE WHEN political_domain_limits.cooldown_until IS NULL
            OR EXCLUDED.cooldown_until>=political_domain_limits.cooldown_until
            THEN EXCLUDED.cooldown_status ELSE political_domain_limits.cooldown_status END
        RETURNING cooldown_until""", (normalize_domain(domain), deadline, status_code)).fetchone()
    return row["cooldown_until"]


# Old queued tasks predate request_domain. This read-time fallback avoids a bulk
# task rewrite during an active collection. Once claimed, the Python-normalized
# value is persisted; redirect deferrals replace it with the actual cooled host.
# Existing publisher domains are ASCII. Non-ASCII legacy URLs still encounter
# the authoritative IDNA-normalized cooldown check immediately before HTTP.
TASK_DOMAIN_FALLBACK_SQL = """COALESCE(t.request_domain,
    CASE WHEN t.kind='review' THEN ''
    WHEN t.kind='discovery' AND t.payload->>'strategy'='google_news' THEN 'news.google.com'
    WHEN COALESCE(t.payload->>'url','')<>'' THEN
        regexp_replace(lower(rtrim(split_part(
            regexp_replace(substring(t.payload->>'url' FROM '^[A-Za-z]+://([^/?#]+)'), '^.*@', ''),
            ':', 1), '.')), '^www[.]', '')
    ELSE COALESCE(%s::jsonb->>t.source_key,'') END)"""
