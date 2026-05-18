from __future__ import annotations

import json
from contextlib import asynccontextmanager
from html import escape
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response

from .auth import (
    COOKIE_NAME,
    auth_configured,
    csrf_token,
    login_configured,
    login_identity,
    make_session,
    missing_auth_config,
    public_empty_demo_configured,
    require_admin,
    require_csrf,
    require_viewer,
    verify_session,
    viewer_auth_configured,
)
from .config import ASSETS_DIR, ROOT, db_path, local_writes_allowed
from .db_admin import (
    ValidationError,
    archive_known_test_targets,
    archive_secondary_target,
    ensure_app_tables,
    insert_manual_story,
    load_targets,
    normalize_targets_file,
    restore_secondary_target,
    update_secondary_target,
)
from .jobs import (
    JobConflict,
    job_manager,
    live_results_for_job,
    mark_orphaned_active_jobs_interrupted,
    recent_jobs,
    record_target_sync,
    run_export_snapshot,
)
from .segmentation import (
    scoped_classifications,
    scoped_dashboard_payload,
    scoped_live_results,
    scoped_raw_texts,
    scoped_status_response,
    scoped_targets_response,
    viewer_profiles_configured,
)
from .storage_bridge import artifact_store
from pipeline.database import ClippingDB

VALID_SENTIMENTS = {"positive", "negative", "neutral"}

BASE_CATEGORIES = (
    "Causa Animal",
    "Combate ao Antissemitismo",
    "Conservação",
    "Economia",
    "Esporte e Lazer",
    "Gabinete",
    "Mandato",
    "Meio Ambiente",
    "Ordenamento",
    "Sancionado",
    "Saúde",
    "Segurança",
    "Turismo",
)


ACTIVE_TARGET_MUTATION_STATUSES = {"queued", "running", "exporting", "cancel_requested"}


def public_targets(*, include_archived: bool = False) -> dict[str, Any] | list[dict[str, Any]]:
    from . import db_admin

    helper = getattr(db_admin, "public_targets", None)
    if helper:
        try:
            return helper(include_archived=include_archived)
        except TypeError:
            return helper()
    return load_targets()


def public_targets_response(*, include_archived: bool = False) -> dict[str, Any]:
    try:
        targets = public_targets(include_archived=include_archived)
    except TypeError:
        targets = public_targets()
    if isinstance(targets, dict):
        return {
            "targets": targets.get("targets", []),
            "primaryKeys": targets.get("primaryKeys", []),
        }
    return {"targets": targets, "primaryKeys": []}


def create_secondary_target(payload: dict[str, Any]) -> dict[str, Any]:
    from . import db_admin

    helper = getattr(db_admin, "create_secondary_target", None)
    if not helper:
        raise ValidationError("Cadastro de alvo ainda nao disponivel.")
    return helper(payload)


def target_mutations_blocked() -> bool:
    status = str(job_manager.current_status().get("status") or "")
    return status in ACTIVE_TARGET_MUTATION_STATUSES


def ensure_target_mutations_allowed() -> None:
    if target_mutations_blocked():
        raise HTTPException(status_code=409, detail="Aguarde a atualização terminar para mudar os nomes acompanhados.")


def upload_targets_artifacts(kind: str, result: dict[str, Any], key: str) -> list[str]:
    if not artifact_store.enabled:
        return []
    safe_key = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in key)[:80] or "target"
    return artifact_store.upload_current_artifacts(
        manifest={"kind": kind, "result": result},
        job_id=f"{kind}-{safe_key}",
    )


def target_mutation_notice() -> dict[str, Any]:
    status = job_manager.current_status()
    current_status = str(status.get("status") or "")
    if current_status not in ACTIVE_TARGET_MUTATION_STATUSES:
        return {}
    return {
        "activeJobNotice": (
            "Nome salvo agora. A atualização em andamento continua com os nomes congelados no início; "
            "esta mudança vale para a base atual e para as próximas rodadas."
        ),
        "activeJob": {
            "id": str(status.get("id") or ""),
            "status": current_status,
        },
    }


def target_validation_payload(exc: ValidationError) -> dict[str, Any]:
    message = str(exc)
    field = "display_name"
    suggestion = "Revise o nome e tente novamente."
    if "pelo menos 3 caracteres" in message:
        suggestion = "Digite um nome de exibicao com 3 caracteres ou mais."
    elif "desconhecido" in message:
        field = "target_key"
        suggestion = "Atualize a lista de nomes e tente de novo com um nome existente."
    elif "principais" in message:
        field = "target_key"
        suggestion = "Edite apenas nomes secundarios criados no painel."
    elif "Restaure" in message:
        suggestion = "Restaure o nome arquivado antes de editar."
    return {
        "error": "target_validation_error",
        "message": message,
        "field": field,
        "suggestion": suggestion,
        "detail": {
            "code": "target_validation_error",
            "message": message,
            "field": field,
            "suggestion": suggestion,
        },
    }


def target_validation_response(exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content=target_validation_payload(exc))


def target_operation_error_response(operation: str, exc: Exception) -> JSONResponse:
    operation_label = {
        "create": "salvar",
        "update": "atualizar",
        "archive": "arquivar",
        "restore": "restaurar",
    }.get(operation, "alterar")
    message = f"Não foi possível {operation_label} este nome."
    cause = f"{type(exc).__name__}: {exc}"
    suggestion = (
        "Verifique se data/targets.json está íntegro e gravável; se o problema persistir, rode os testes "
        "de targets e consulte o WORK_LOG do loop atual."
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "target_operation_failed",
            "message": message,
            "cause": cause,
            "suggestion": suggestion,
            "detail": {
                "code": "target_operation_failed",
                "message": message,
                "cause": cause,
                "suggestion": suggestion,
            },
        },
    )


def sync_target_after_mutation(target_key: str, *, reason: str, cleanup: bool = False) -> tuple[dict[str, Any], dict[str, Any] | None]:
    try:
        return record_target_sync(target_key, reason=reason, cleanup=cleanup), None
    except Exception as exc:
        return {}, {
            "code": "target_sync_failed",
            "message": "O nome foi salvo, mas a sincronizacao com a base atual falhou.",
            "suggestion": "Rode uma atualizacao ou tente salvar o nome novamente depois de verificar a base.",
            "error": str(exc),
        }


def target_mutation_response(
    kind: str,
    result: dict[str, Any],
    target_key: str,
    *,
    sync_reason: str = "",
    cleanup: bool = False,
) -> JSONResponse:
    target_sync: dict[str, Any] = {}
    warning: dict[str, Any] | None = None
    if sync_reason:
        target_sync, warning = sync_target_after_mutation(target_key, reason=sync_reason, cleanup=cleanup)
    uploaded = upload_targets_artifacts(kind, result, target_key)
    response: dict[str, Any] = {
        **result,
        "uploadedArtifactCount": len(uploaded),
        "uploadedArtifacts": uploaded,
        **target_mutation_notice(),
    }
    if sync_reason:
        response["targetSync"] = target_sync
        if warning:
            response["warning"] = warning
    return JSONResponse(response)


def _classification_db() -> ClippingDB:
    return ClippingDB(db_path())


@asynccontextmanager
async def lifespan(_: FastAPI):
    artifact_store.download_current_artifacts()
    target_cleanup = archive_known_test_targets()
    targets_normalized = normalize_targets_file()
    ensure_app_tables(db_path())
    interrupted_jobs = mark_orphaned_active_jobs_interrupted()
    resume_startup = getattr(job_manager, "resume_startup_jobs", None)
    resumed_jobs = resume_startup() if resume_startup else 0
    # Ensure classification + category tables exist (idempotent CREATE IF NOT EXISTS).
    cdb = ClippingDB(db_path())
    existing_names = {row["name"] for row in cdb.list_categories()}
    newly_seeded = [n for n in BASE_CATEGORIES if n not in existing_names]
    for name in newly_seeded:
        cdb.get_or_create_category(name, created_by="system")
    if (newly_seeded or targets_normalized or interrupted_jobs or resumed_jobs) and artifact_store.enabled:
        artifact_store.upload_current_artifacts(
            manifest={
                "kind": "startup-normalization",
                "seededCategories": newly_seeded,
                "targetsNormalized": targets_normalized,
                "orphanedJobsInterrupted": interrupted_jobs,
                "resumedJobs": resumed_jobs,
            },
            job_id="startup-runtime-normalization",
        )
    if target_cleanup.get("archivedCount") and artifact_store.enabled:
        artifact_store.upload_current_artifacts(
            manifest={"kind": "targets-auto-archived", "result": target_cleanup},
            job_id="targets-auto-archived",
        )
    yield


app = FastAPI(title="Clipping Project", docs_url=None, redoc_url=None, lifespan=lifespan)


@app.middleware("http")
async def no_cache_for_dashboard_assets(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith("/assets/clipping"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


def current_session(request: Request) -> dict[str, Any] | None:
    return verify_session(request.cookies.get(COOKIE_NAME))


def read_json_file(path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def safe_asset_path(asset_path: str):
    asset_file = (ASSETS_DIR / asset_path).resolve()
    assets_root = ASSETS_DIR.resolve()
    if asset_file != assets_root and assets_root not in asset_file.parents:
        raise HTTPException(status_code=404, detail="asset_not_found")
    if not asset_file.is_file():
        raise HTTPException(status_code=404, detail="asset_not_found")
    return asset_file


def dashboard_html_for_session(index_path, session: dict[str, Any]) -> str:
    html_doc = index_path.read_text(encoding="utf-8")
    html_doc = html_doc.replace('data-clipping-static="1"', 'data-clipping-static="0"', 1)
    role = str(session.get("role") or "admin")
    profile = str(session.get("profile") or ("admin" if role == "admin" else ""))
    html_doc = html_doc.replace(
        'id="app"',
        (
            'id="app"'
            f' data-clipping-session-role="{escape(role)}"'
            f' data-clipping-session-profile="{escape(profile)}"'
        ),
        1,
    )
    if role != "admin":
        html_doc = html_doc.replace("<body>", '<body class="viewer-readonly">', 1)
    return html_doc


@app.get("/assets/{asset_path:path}")
def dashboard_asset(asset_path: str, request: Request) -> Response:
    if asset_path == "clipping-data.json":
        session = require_viewer(request)
        payload = scoped_dashboard_payload(read_json_file(ASSETS_DIR / "clipping-data.json"), session)
        return JSONResponse(payload)
    if asset_path == "clipping-raw-texts.json":
        session = require_viewer(request)
        scoped_payload = scoped_dashboard_payload(read_json_file(ASSETS_DIR / "clipping-data.json"), session)
        raw_payload = read_json_file(ASSETS_DIR / "clipping-raw-texts.json")
        return JSONResponse(scoped_raw_texts(raw_payload, scoped_payload))
    return FileResponse(safe_asset_path(asset_path))


@app.get("/", response_class=HTMLResponse)
def public_dashboard(request: Request) -> Response:
    session = current_session(request)
    if not session:
        return HTMLResponse(login_html(), status_code=200)
    index_path = ROOT / "index.html"
    if index_path.is_file():
        return HTMLResponse(dashboard_html_for_session(index_path, session), status_code=200)
    return HTMLResponse("<h1>Clipping institucional</h1><p>Painel ainda nao gerado.</p>", status_code=200)


@app.get("/admin")
def admin_page() -> RedirectResponse:
    return RedirectResponse("/", status_code=307)


@app.post("/api/login")
async def login(request: Request) -> JSONResponse:
    if not login_configured():
        raise HTTPException(status_code=503, detail="login_auth_not_configured")
    payload = await read_json(request)
    identity = login_identity(str(payload.get("password") or ""))
    if not identity:
        raise HTTPException(status_code=401, detail="invalid_password")
    session_token = make_session(
        identity["sub"],
        role=identity["role"],
        profile=identity["profile"],
    )
    response = JSONResponse({"ok": True, "role": identity["role"], "profile": identity["profile"]})
    response.set_cookie(
        COOKIE_NAME,
        session_token,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        max_age=8 * 60 * 60,
    )
    return response


@app.post("/api/logout")
def logout(request: Request) -> JSONResponse:
    require_viewer(request)
    require_csrf(request)
    response = JSONResponse({"ok": True})
    response.delete_cookie(COOKIE_NAME)
    return response


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {
        "ok": True,
        "dbExists": db_path().is_file(),
        "authConfigured": auth_configured(),
        "loginConfigured": login_configured(),
        "viewerAuthConfigured": viewer_auth_configured(),
        "demoViewerConfigured": public_empty_demo_configured(),
        "viewerProfilesConfigured": viewer_profiles_configured(),
        "missingConfig": missing_auth_config(),
        "storage": artifact_store.status(),
        "localWritesAllowed": local_writes_allowed(),
        "job": safe_current_status().get("status", "idle"),
        "shakiraLoopVersion": "2026-05-06-durable-source-ledger-wp-internal-v2",
    }


@app.get("/api/update/status")
def update_status(request: Request) -> dict[str, Any]:
    session = require_viewer(request)
    try:
        recent = recent_jobs(include_observability=False)
    except Exception:
        recent = []
    return scoped_status_response({"current": safe_current_status(), "recent": recent}, session)


def safe_current_status() -> dict[str, Any]:
    try:
        return job_manager.current_status()
    except Exception:
        return {
            "status": "status_unavailable",
            "error_message": "Não foi possível ler o status da atualização agora. Os artefatos publicados continuam disponíveis.",
        }


@app.get("/api/update/live-results")
def update_live_results(request: Request, job_id: str = "", target_key: str = "", scope: str = "", limit: int = 60) -> dict[str, Any]:
    session = require_viewer(request)
    data = live_results_for_job(job_id, target_key=target_key, scope=scope, limit=limit)
    return scoped_live_results(data, session, requested_target_key=target_key)


@app.post("/api/update/start")
async def start_update(request: Request) -> JSONResponse:
    require_admin(request)
    require_csrf(request)
    payload = await read_json(request)
    try:
        job = job_manager.start_update(payload, started_by="admin")
    except JobConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return JSONResponse(job)


@app.post("/api/update/resume")
async def resume_update(request: Request) -> JSONResponse:
    require_admin(request)
    require_csrf(request)
    payload = await read_json(request)
    try:
        job = job_manager.resume_update(str(payload.get("job_id") or payload.get("jobId") or ""), started_by="admin")
    except JobConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return JSONResponse(job)


@app.post("/api/update/cancel")
async def cancel_update(request: Request) -> JSONResponse:
    require_admin(request)
    require_csrf(request)
    try:
        cancel_helper = getattr(job_manager, "cancel_active", None) or getattr(job_manager, "cancel_update", None)
        if not cancel_helper:
            raise JobConflict("no_active_job")
        job = cancel_helper()
    except JobConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return JSONResponse(job)


@app.post("/api/export")
async def start_export(request: Request) -> JSONResponse:
    require_admin(request)
    require_csrf(request)
    try:
        job = job_manager.start_export(started_by="admin")
    except JobConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return JSONResponse(job)


@app.post("/api/manual-story")
async def manual_story(request: Request) -> JSONResponse:
    require_admin(request)
    require_csrf(request)
    if not artifact_store.writes_available:
        raise HTTPException(status_code=503, detail="persistent_storage_not_configured")
    payload = await read_json(request)
    try:
        artifact_store.backup_current_artifacts("manual-story")
        result = insert_manual_story(db_path(), payload, created_by="admin")
        export_requested = bool(payload.get("export", False))
        if export_requested:
            run_export_snapshot()
        uploaded: list[str] = []
        if artifact_store.enabled:
            uploaded = artifact_store.upload_current_artifacts(
                manifest={"kind": "manual-story", "result": result},
                job_id=f"manual-{result.get('articleId', 'duplicate')}",
            )
        job = job_manager.record_completed_manual(
            result=result,
            uploaded=uploaded,
            started_by="admin",
            export=export_requested,
            mentions_inserted=len(payload.get("target_keys") or payload.get("targetKeys") or []),
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse({**result, "job": job})


@app.get("/api/csrf")
def get_csrf(request: Request) -> dict[str, Any]:
    """Returns the CSRF token for the current session. 401 if not authed."""
    require_viewer(request)
    return {"csrf": csrf_token(request.cookies.get(COOKIE_NAME))}


@app.get("/api/categories")
def list_classification_categories(request: Request) -> dict[str, Any]:
    require_viewer(request)
    return {"categories": _classification_db().list_categories()}


@app.get("/api/targets")
def list_targets(request: Request, include_archived: bool = False) -> dict[str, Any]:
    session = require_viewer(request)
    return scoped_targets_response(public_targets_response(include_archived=include_archived), session)


@app.post("/api/targets")
async def add_target(request: Request) -> JSONResponse:
    require_admin(request)
    require_csrf(request)
    payload = await read_json(request)
    try:
        result = create_secondary_target(payload)
    except ValidationError as exc:
        return target_validation_response(exc)
    except Exception as exc:
        return target_operation_error_response("create", exc)
    key = str(result.get("key") or "created")
    return target_mutation_response("targets-created", result, key, sync_reason="target-created")


@app.patch("/api/targets/{target_key}")
async def update_target(target_key: str, request: Request) -> JSONResponse:
    require_admin(request)
    require_csrf(request)
    payload = await read_json(request)
    try:
        result = update_secondary_target(target_key, payload)
    except ValidationError as exc:
        return target_validation_response(exc)
    except Exception as exc:
        return target_operation_error_response("update", exc)
    key = str(result.get("key") or target_key)
    return target_mutation_response("targets-updated", result, key, sync_reason="target-updated", cleanup=True)


@app.post("/api/targets/{target_key}/archive")
async def archive_target(target_key: str, request: Request) -> JSONResponse:
    require_admin(request)
    require_csrf(request)
    payload = await read_json(request)
    try:
        result = archive_secondary_target(target_key, str(payload.get("reason") or "Arquivado pela equipe."))
    except ValidationError as exc:
        return target_validation_response(exc)
    except Exception as exc:
        return target_operation_error_response("archive", exc)
    return target_mutation_response("targets-archived", result, target_key)


@app.post("/api/targets/{target_key}/restore")
def restore_target(target_key: str, request: Request) -> JSONResponse:
    require_admin(request)
    require_csrf(request)
    try:
        result = restore_secondary_target(target_key)
    except ValidationError as exc:
        return target_validation_response(exc)
    except Exception as exc:
        return target_operation_error_response("restore", exc)
    key = str(result.get("key") or target_key)
    return target_mutation_response("targets-restored", result, key, sync_reason="target-restored")


@app.post("/api/categories")
async def create_classification_category(request: Request) -> dict[str, Any]:
    require_admin(request)
    require_csrf(request)
    payload = await read_json(request)
    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    created_by = str(payload.get("created_by") or "coworker").strip() or "coworker"
    cid = _classification_db().get_or_create_category(name, created_by=created_by)
    uploaded: list[str] = []
    if artifact_store.enabled:
        uploaded = artifact_store.upload_current_artifacts(
            manifest={"kind": "category", "category_id": cid, "name": name},
            job_id=f"category-{cid}",
        )
    return {
        "id": cid,
        "name": name,
        "created_by": created_by,
        "uploadedArtifactCount": len(uploaded),
        "uploadedArtifacts": uploaded,
    }


@app.get("/api/classifications")
def list_classifications_bulk(request: Request) -> dict[str, Any]:
    session = require_viewer(request)
    rows = _classification_db().get_classifications_with_context(limit=100000)
    rows = scoped_classifications(rows, session)
    return {
        "classifications": [
            {
                "article_id": r.get("article_id"),
                "target_key": r.get("target_key"),
                "article_sentiment": r.get("article_sentiment"),
                "target_sentiment": r.get("target_sentiment"),
                "centimetragem": r.get("centimetragem"),
                "categories": r.get("categories") or [],
            }
            for r in rows
        ]
    }


@app.post("/api/classifications")
async def upsert_classification(request: Request) -> dict[str, Any]:
    require_admin(request)
    require_csrf(request)
    payload = await read_json(request)

    try:
        article_id = int(payload.get("article_id") or 0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="article_id must be an integer")
    target_key = str(payload.get("target_key") or "").strip()
    target_name = str(payload.get("target_name") or target_key).strip() or target_key
    if not article_id or not target_key:
        raise HTTPException(status_code=400, detail="article_id and target_key are required")

    art_sent = payload.get("article_sentiment")
    tgt_sent = payload.get("target_sentiment")
    for label, val in (("article_sentiment", art_sent), ("target_sentiment", tgt_sent)):
        if val is not None and val not in VALID_SENTIMENTS:
            raise HTTPException(
                status_code=400,
                detail=f"{label} must be one of {sorted(VALID_SENTIMENTS)} or null",
            )

    centimetragem_raw = payload.get("centimetragem")
    centimetragem: float | None
    if centimetragem_raw in (None, ""):
        centimetragem = None
    else:
        try:
            centimetragem = float(centimetragem_raw)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="centimetragem must be numeric or null")

    classified_by = str(payload.get("classified_by") or "coworker").strip() or "coworker"

    cdb = _classification_db()
    mention_id = cdb.find_mention_id(article_id, target_key)
    if mention_id is None:
        mention_id = cdb.create_mention(
            article_id=article_id,
            target_key=target_key,
            target_name=target_name,
        )

    classification_id = cdb.upsert_classification(
        mention_id=mention_id,
        article_sentiment=art_sent,
        target_sentiment=tgt_sent,
        centimetragem=centimetragem,
        classified_by=classified_by,
        ai_generated=bool(payload.get("ai_generated") or False),
    )

    raw_categories = payload.get("categories") or []
    if not isinstance(raw_categories, list):
        raise HTTPException(status_code=400, detail="categories must be a list of names")
    category_ids = []
    for raw_name in raw_categories:
        name = str(raw_name or "").strip()
        if not name:
            continue
        category_ids.append(cdb.get_or_create_category(name, created_by=classified_by))
    cdb.set_classification_categories(classification_id, category_ids)

    uploaded: list[str] = []
    if artifact_store.enabled:
        uploaded = artifact_store.upload_current_artifacts(
            manifest={
                "kind": "classification",
                "classification_id": classification_id,
                "mention_id": mention_id,
                "article_id": article_id,
                "target_key": target_key,
            },
            job_id=f"classification-{classification_id}",
        )

    return {
        "ok": True,
        "classification_id": classification_id,
        "mention_id": mention_id,
        "article_id": article_id,
        "target_key": target_key,
        "article_sentiment": art_sent,
        "target_sentiment": tgt_sent,
        "centimetragem": centimetragem,
        "categories": [str(n).strip() for n in raw_categories if str(n).strip()],
        "uploadedArtifactCount": len(uploaded),
        "uploadedArtifacts": uploaded,
    }


async def read_json(request: Request) -> dict[str, Any]:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        raw = (await request.body()).decode("utf-8")
        return json.loads(raw) if raw.strip().startswith("{") else {}


def login_html() -> str:
    configured = login_configured()
    disabled = "" if configured else "disabled"
    status = (
        "Entre para acessar sua visao do clipping."
        if configured
        else "Acesso por senha ainda nao configurado no Render."
    )
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Acessar clipping</title>
  <style>{ADMIN_CSS}</style>
</head>
<body class="admin-body">
  <main class="admin-shell login-shell">
    <section class="admin-card login-card">
      <p class="eyebrow">Clipping institucional</p>
      <h1>Acessar clipping</h1>
      <p>{escape(status)}</p>
      <label>Senha de acesso
        <input id="password" type="password" autocomplete="current-password" {disabled}>
      </label>
      <button id="loginButton" type="button" {disabled}>Entrar</button>
      <p id="loginMessage" class="muted"></p>
    </section>
  </main>
  <script>
    const btn = document.getElementById('loginButton');
    if (btn) btn.addEventListener('click', async () => {{
      const password = document.getElementById('password').value;
      const res = await fetch('/api/login', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{password}})
      }});
      if (res.ok) window.location.reload();
      else document.getElementById('loginMessage').textContent = 'Senha incorreta ou acesso ainda nao configurado.';
    }});
  </script>
</body>
</html>"""


def admin_html(token: str) -> str:
    targets = load_targets()
    target_checks = "\n".join(
        f'<label class="check"><input type="checkbox" value="{escape(str(row["key"]))}"> {escape(str(row.get("label") or row["key"]))}</label>'
        for row in targets
    )
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="csrf-token" content="{escape(token)}">
  <title>Atualizacao do clipping</title>
  <style>{ADMIN_CSS}</style>
</head>
<body class="admin-body">
  <main class="admin-shell">
    <header class="admin-hero">
      <p class="eyebrow">Mandato Flavio Valle</p>
      <h1>Atualizacao do clipping</h1>
      <p>Escolha um fluxo, acompanhe a coleta e publique a base atualizada sem abrir o terminal.</p>
      <a href="/" class="plain-link">Ver painel publico</a>
    </header>

    <section class="admin-card">
      <div class="section-title">
        <div>
          <p class="eyebrow">Coleta guiada</p>
          <h2>Rodar pipeline</h2>
        </div>
        <button type="button" id="refreshStatus">Atualizar status</button>
      </div>
      <div class="preset-grid">
        <button class="preset active" data-preset="rapido"><strong>Rapido</strong><span>Flavio Valle, hoje e ontem</span></button>
        <button class="preset" data-preset="completo"><strong>Completo</strong><span>Circulo principal, ultimos 7 dias</span></button>
        <button class="preset" data-preset="custom"><strong>Personalizado</strong><span>Escolha nomes e periodo</span></button>
      </div>
      <div class="form-grid" id="customFields">
        <fieldset>
          <legend>Nomes acompanhados</legend>
          {target_checks}
        </fieldset>
        <label>Data inicial <input id="dateFrom" type="date"></label>
        <label>Data final <input id="dateTo" type="date"></label>
        <label>Fontes
          <select id="collector">
            <option value="all">Todas as fontes seguras</option>
            <option value="google_news">Google News</option>
            <option value="rss">RSS</option>
            <option value="wordpress_api">Sites WordPress</option>
            <option value="internal_search">Busca em sites</option>
          </select>
        </label>
      </div>
      <label class="check"><input id="exportAfter" type="checkbox" checked> Atualizar o painel depois da coleta</label>
      <button type="button" id="startUpdate">Comecar atualizacao</button>
      <pre id="jobStatus" class="status-box">Nenhum job carregado.</pre>
    </section>

    <section class="admin-card">
      <p class="eyebrow">Historia unica</p>
      <h2>Adicionar materia manualmente</h2>
      <div class="form-grid">
        <label>Titulo <input id="manualTitle" type="text"></label>
        <label>Link da materia <input id="manualUrl" type="url"></label>
        <label>Fonte <input id="manualSource" type="text"></label>
        <label>Data publicada <input id="manualPublished" type="datetime-local"></label>
        <fieldset>
          <legend>Nomes citados</legend>
          <div id="manualTargets">{target_checks}</div>
        </fieldset>
        <label class="wide">Resumo <textarea id="manualSummary" rows="4"></textarea></label>
        <label class="wide">Texto completo <textarea id="manualText" rows="6"></textarea></label>
        <label class="wide">Nota interna <textarea id="manualNote" rows="2"></textarea></label>
      </div>
      <label class="check"><input id="manualExport" type="checkbox" checked> Atualizar painel depois de adicionar</label>
      <button type="button" id="addManual">Adicionar materia</button>
      <p id="manualMessage" class="muted"></p>
    </section>
  </main>
  <script>{ADMIN_JS}</script>
</body>
</html>"""


ADMIN_CSS = """
:root{--bg:#eef3f7;--ink:#05253e;--muted:#516679;--brand:#0b4b7f;--gold:#f6bb1b;--line:#b4c4d1;--card:#fff}
*{box-sizing:border-box}body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.5}
.admin-shell{width:min(1120px,calc(100% - 32px));margin:0 auto;padding:24px 0 48px}.login-shell{min-height:100vh;display:grid;place-items:center}
.admin-hero,.admin-card{border:1px solid var(--line);border-radius:8px;background:var(--card);box-shadow:0 16px 32px rgba(5,37,62,.08)}
.admin-hero{padding:28px;background:linear-gradient(135deg,#05253e,#0b4b7f);color:#fff}.admin-hero p{max-width:680px}.admin-card{padding:22px;margin-top:18px}
.login-card{width:min(440px,100%)}.eyebrow{margin:0 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:.12em;font-weight:800;color:var(--muted)}.admin-hero .eyebrow{color:#b4c4d1}
h1,h2{margin:0 0 8px;line-height:1.05}h1{font-size:clamp(34px,5vw,52px)}h2{font-size:24px}.section-title{display:flex;justify-content:space-between;gap:12px;align-items:center}
button{border:0;border-radius:8px;background:var(--gold);color:var(--ink);font-weight:800;padding:11px 14px;cursor:pointer}button:disabled{opacity:.5;cursor:not-allowed}.plain-link{color:#fff;font-weight:800}
.preset-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:16px 0}.preset{background:#f8fafc;border:1px solid var(--line);text-align:left}.preset.active{border-color:transparent;background:var(--gold)}.preset span{display:block;margin-top:4px;font-weight:500}
.form-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:14px}.wide{grid-column:1/-1}
label,fieldset{display:grid;gap:6px;font-weight:700}fieldset{border:1px solid var(--line);border-radius:8px;padding:12px}.check{display:flex;gap:8px;align-items:flex-start;font-weight:600}
input,select,textarea{width:100%;border:1px solid var(--line);border-radius:8px;padding:10px;font:inherit;background:#fff}textarea{resize:vertical}.muted{color:var(--muted)}
.status-box{min-height:120px;white-space:pre-wrap;background:#05253e;color:#e9f2fb;border-radius:8px;padding:14px;overflow:auto}.admin-card button+pre{margin-top:12px}
"""


ADMIN_JS = """
const csrf = document.querySelector('meta[name="csrf-token"]').content;
let preset = 'rapido';
const statusBox = document.getElementById('jobStatus');
document.querySelectorAll('.preset').forEach(btn => btn.addEventListener('click', () => {
  preset = btn.dataset.preset;
  document.querySelectorAll('.preset').forEach(b => b.classList.toggle('active', b === btn));
}));
async function api(path, body) {
  const res = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json','X-CSRF-Token':csrf}, body:JSON.stringify(body||{})});
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || 'Falha na operacao');
  return data;
}
async function refreshStatus() {
  const res = await fetch('/api/update/status');
  const data = await res.json();
  statusBox.textContent = JSON.stringify(data.current, null, 2);
}
document.getElementById('refreshStatus').addEventListener('click', refreshStatus);
document.getElementById('startUpdate').addEventListener('click', async () => {
  const targetKeys = [...document.querySelectorAll('#customFields input[type="checkbox"]:checked')].map(x => x.value);
  const body = {preset, export: document.getElementById('exportAfter').checked};
  if (preset === 'custom') {
    body.target_keys = targetKeys;
    body.date_from = document.getElementById('dateFrom').value;
    body.date_to = document.getElementById('dateTo').value;
    body.collector = document.getElementById('collector').value;
  }
  try { statusBox.textContent = JSON.stringify(await api('/api/update/start', body), null, 2); }
  catch (e) { statusBox.textContent = e.message; }
});
document.getElementById('addManual').addEventListener('click', async () => {
  const manualBox = document.getElementById('manualMessage');
  const body = {
    title: document.getElementById('manualTitle').value,
    url: document.getElementById('manualUrl').value,
    source_name: document.getElementById('manualSource').value,
    published_at: document.getElementById('manualPublished').value,
    summary: document.getElementById('manualSummary').value,
    full_text: document.getElementById('manualText').value,
    note: document.getElementById('manualNote').value,
    target_keys: [...document.querySelectorAll('#manualTargets input[type="checkbox"]:checked')].map(x => x.value),
    export: document.getElementById('manualExport').checked
  };
  try { const data = await api('/api/manual-story', body); manualBox.textContent = data.message || 'Materia registrada.'; }
  catch (e) { manualBox.textContent = e.message; }
});
refreshStatus().catch(() => {});
"""
