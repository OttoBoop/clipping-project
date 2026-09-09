"""Authenticated, bounded political-clipping interfaces.

The legacy dashboard remains available for administration and static exports.
This surface never reads either of the full-archive JSON bundles.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from html import escape

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from starlette.concurrency import run_in_threadpool

from .auth import require_admin, require_csrf, require_not_demo, require_viewer
from .config import ROOT
from .political_corpus import PoliticalAccessDenied, PoliticalNotFound, political_corpus
from .segmentation import PSD_PROFILE, allowed_target_keys, is_admin_session, psd_target_keys, viewer_profiles

SCOPE = "politica_rj_2026"
router = APIRouter()


def access(request: Request, *, mutation: bool = False, admin: bool = False):
    # Import at request time to share the existing admin simulation rules.
    from .app import effective_session_for, public_targets_response

    session = require_admin(request) if admin else require_viewer(request)
    effective = effective_session_for(request, session)
    if mutation:
        require_csrf(request)
        require_not_demo(effective)
        if effective is not session:
            raise HTTPException(403, "simulation_is_read_only")
    allowed = allowed_target_keys(effective)
    client = request.query_params.get("client", "")
    if client:
        if not is_admin_session(effective):
            raise HTTPException(403, "political_client_admin_required")
        if client != PSD_PROFILE or client not in viewer_profiles():
            raise HTTPException(404, "political_client_not_found")
        # Keep the real administrator identity while restricting every read and
        # mutation to this client's roster. This is an operating context, not simulation.
        allowed = psd_target_keys()
    rows = public_targets_response(include_archived=True).get("targets", [])
    client_keys = psd_target_keys()
    political = [r for r in rows if r.get("political_roster_version") or PSD_PROFILE in (r.get("collection_profiles") or []) or r.get("key") in client_keys or r.get("key") in {
        "flavio_valle", "pedro_duarte", "pedro_angelito", "bernardo_rubiao"
    }]
    keys = sorted({str(r["key"]) for r in political if allowed is None or r["key"] in allowed})
    if not keys:
        raise HTTPException(403, "political_profile_required")
    return effective, keys, [r for r in political if r["key"] in keys]


@contextmanager
def service_errors():
    try:
        yield
    except (PermissionError, PoliticalAccessDenied):
        raise HTTPException(403, "political_scope_denied") from None
    except (LookupError, PoliticalNotFound):
        raise HTTPException(404, "political_record_not_found") from None
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    except RuntimeError:
        raise HTTPException(503, "political_service_unavailable") from None
    except HTTPException:
        raise
    except Exception as exc:
        # Database exceptions can contain connection strings; expose no details.
        logging.getLogger(__name__).error("Political service failure: %s", type(exc).__name__)
        raise HTTPException(503, "political_service_unavailable") from None


async def json_body(request: Request, *, allow_empty: bool = False) -> dict:
    import json
    cached = getattr(request.state, "political_json_body", None)
    if cached is not None:
        return cached
    chunks = bytearray()
    async for chunk in request.stream():
        if len(chunks) + len(chunk) > 2 * 1024 * 1024:
            raise HTTPException(413, "political_request_too_large")
        chunks.extend(chunk)
    try:
        value = {} if allow_empty and not chunks else json.loads(chunks)
    except ValueError:
        raise HTTPException(400, "invalid_json") from None
    if not isinstance(value, dict):
        raise HTTPException(400, "object_required")
    # Legacy aliases inspect scope before delegating to these same handlers.
    # Keep the bounded parse so delegation never consumes the stream twice.
    request.state.political_json_body = value
    return value


def list_filters(request: Request, keys: list[str]) -> dict:
    query = request.query_params
    try:
        page_size = max(1, min(200, int(query.get("page_size", "50"))))
    except ValueError:
        raise HTTPException(400, "invalid_page_size") from None
    selected = query.getlist("target_key")
    if any(key not in keys for key in selected):
        raise HTTPException(403, "political_scope_denied")
    return dict(allowed_target_keys=keys, page_size=page_size,
                cursor=query.get("cursor", ""), target_keys=selected or None,
                q=query.get("q", "")[:300], date_from=query.get("date_from", ""),
                date_to=query.get("date_to", ""), source_key=query.get("source_key", ""),
                body_status=query.get("body_status", ""), story_id=query.get("story_id") or None)


@router.get("/politica", response_class=HTMLResponse)
def page(request: Request):
    session, _, _ = access(request)
    html = (ROOT / "web_app" / "templates" / "political.html").read_text(encoding="utf-8")
    return HTMLResponse(html.replace("{{ROLE}}", "admin" if is_admin_session(session) else "viewer")
                        .replace("{{PROFILE}}", escape(str(session.get("profile") or session.get("sub") or "admin"))))


@router.get("/api/political/meta")
def meta(request: Request):
    session, _, targets = access(request)
    active = [row for row in targets if not row.get("archived")]
    profile = request.query_params.get("client") or str(session.get("profile") or "")
    config = viewer_profiles().get(profile, {})
    available = {row["key"] for row in active}
    defaults = [key for key in config.get("default_targets", []) if key in available]
    if not defaults:
        defaults = [row["key"] for row in active if row.get("preferred_for_political_run")]
    if not defaults:
        defaults = [row["key"] for row in active]
    return {"scope": SCOPE, "configured": political_corpus.configured,
            "canRun": is_admin_session(session), "dateFrom": "2026-06-01",
            "defaultTargets": defaults, "clientProfile": profile,
            "clientLabel": config.get("label") or profile,
            "psdClientAvailable": is_admin_session(require_viewer(request)) and PSD_PROFILE in viewer_profiles(),
            "targets": active,
            "archivedTargets": [row for row in targets if row.get("archived")]}


@router.get("/api/political/sources")
def sources(request: Request):
    access(request)
    import json
    with (ROOT / "data" / "political_sources_v1.json").open(encoding="utf-8") as f:
        return json.load(f)


@router.get("/api/political/status")
def status(request: Request, job_id: str = ""):
    _, keys, _ = access(request)
    with service_errors():
        return political_corpus.status(job_id, allowed_target_keys=keys)


@router.post("/api/political/jobs")
async def start(request: Request):
    session, keys, targets = access(request, mutation=True, admin=True)
    payload = await json_body(request)
    selected = payload.get("target_keys")
    if not isinstance(selected, list) or not selected or any(not isinstance(k, str) or k not in keys for k in selected):
        raise HTTPException(400, "select_allowed_targets")
    active = {row["key"]: row for row in targets if not row.get("archived")}
    if any(k not in active for k in selected):
        raise HTTPException(400, "archived_target")
    # Never trust client-supplied matching rules or hidden target snapshots.
    payload["target_snapshots"] = [active[k] for k in dict.fromkeys(selected)]
    payload["scope"] = SCOPE
    payload.setdefault("date_from", "2026-06-01")
    with service_errors():
        return await run_in_threadpool(political_corpus.start_job, payload,
                                      started_by=str(session.get("sub") or "admin"), allowed_target_keys=keys)


@router.post("/api/political/jobs/{job_id}/resume")
def resume(request: Request, job_id: str):
    _, keys, _ = access(request, mutation=True, admin=True)
    with service_errors():
        return political_corpus.resume_job(job_id, allowed_target_keys=keys)


@router.post("/api/political/jobs/{job_id}/cancel")
def cancel(request: Request, job_id: str):
    _, keys, _ = access(request, mutation=True, admin=True)
    with service_errors():
        return political_corpus.cancel_job(job_id, allowed_target_keys=keys)


@router.get("/api/political/articles")
def articles(request: Request):
    _, keys, _ = access(request)
    with service_errors():
        return political_corpus.list_articles(**list_filters(request, keys))


@router.get("/api/political/stories")
def stories(request: Request):
    _, keys, _ = access(request)
    with service_errors():
        return political_corpus.list_stories(**list_filters(request, keys))


@router.get("/api/political/articles/{article_id}/text")
def article_text(request: Request, article_id: int):
    _, keys, _ = access(request)
    with service_errors():
        return political_corpus.article_text(article_id, allowed_target_keys=keys)


@router.get("/api/political/coverage")
def coverage(request: Request, job_id: str = ""):
    _, keys, _ = access(request)
    with service_errors():
        return political_corpus.coverage(job_id, allowed_target_keys=keys)


@router.get("/api/political/articles/{article_id}/classifications")
def classifications(request: Request, article_id: int):
    _, keys, _ = access(request)
    with service_errors():
        return political_corpus.classifications(article_id, allowed_target_keys=keys)


@router.post("/api/political/articles/{article_id}/classifications")
async def classify(request: Request, article_id: int):
    session, keys, _ = access(request, mutation=True)
    payload = await json_body(request)
    payload["ai_generated"] = False
    if isinstance(payload.get("payload"), dict):
        payload["payload"]["ai_generated"] = False
    with service_errors():
        return await run_in_threadpool(political_corpus.upsert_classification, article_id, payload,
                                      allowed_target_keys=keys, updated_by=str(session.get("sub") or "viewer"))


@router.post("/api/political/manual-story")
async def manual_story(request: Request):
    session, keys, targets = access(request, mutation=True, admin=True)
    payload = await json_body(request)
    selected = payload.get("target_keys")
    if not isinstance(selected, list) or not selected or any(not isinstance(k, str) or k not in keys for k in selected):
        raise HTTPException(400, "select_allowed_targets")
    active = {row["key"]: row for row in targets if not row.get("archived")}
    if any(k not in active for k in selected):
        raise HTTPException(400, "archived_target")
    payload["target_snapshots"] = [active[k] for k in dict.fromkeys(selected)]
    with service_errors():
        return await run_in_threadpool(political_corpus.insert_manual_story, payload,
                                      allowed_target_keys=keys, created_by=str(session.get("sub") or "admin"))
