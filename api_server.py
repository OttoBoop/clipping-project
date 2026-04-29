#!/usr/bin/env python3
"""Flask write API for the clipping classification feature.

Endpoints
---------
GET  /api/health
GET  /api/categories
POST /api/categories                 {name, created_by?}
GET  /api/articles/<id>/classifications
POST /api/classifications            {article_id, target_key, article_sentiment,
                                      target_sentiment, centimetragem?, categories?[],
                                      classified_by?}

Run
---
    python api_server.py                    # default 0.0.0.0:8765
    PORT=9000 python api_server.py
    CLIPPING_DB=/path/to.db python api_server.py

The dashboard reads its API URL from `app.dataset.clippingApiUrl` in index.html.
If unset, the editor stays hidden (read-only mode).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).parent))
from pipeline.database import ClippingDB

VALID_SENTIMENTS = {"positive", "negative", "neutral"}

app = Flask(__name__)
CORS(app)

_db_path = Path(os.environ.get("CLIPPING_DB", "data/clipping.db")).expanduser()
db = ClippingDB(_db_path)


def _err(message: str, status: int = 400):
    return jsonify({"error": message}), status


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "db": str(_db_path)})


@app.get("/api/categories")
def list_categories():
    return jsonify({"categories": db.list_categories()})


@app.post("/api/categories")
def create_category():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name") or "").strip()
    if not name:
        return _err("name is required")
    created_by = str(payload.get("created_by") or "coworker").strip() or "coworker"
    cid = db.get_or_create_category(name, created_by=created_by)
    return jsonify({"id": cid, "name": name, "created_by": created_by})


@app.get("/api/articles/<int:article_id>/classifications")
def article_classifications(article_id: int):
    rows = db.get_classifications_with_context(limit=1000)
    matched = [r for r in rows if int(r.get("article_id") or 0) == article_id]
    return jsonify({"article_id": article_id, "classifications": matched})


@app.get("/api/classifications")
def list_classifications():
    rows = db.get_classifications_with_context(limit=100000)
    projected = [
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
    return jsonify({"classifications": projected})


@app.post("/api/classifications")
def upsert_classification():
    payload = request.get_json(silent=True) or {}

    try:
        article_id = int(payload.get("article_id") or 0)
    except (TypeError, ValueError):
        return _err("article_id must be an integer")
    target_key = str(payload.get("target_key") or "").strip()
    if not article_id or not target_key:
        return _err("article_id and target_key are required")

    art_sent = payload.get("article_sentiment")
    tgt_sent = payload.get("target_sentiment")
    for label, val in (("article_sentiment", art_sent), ("target_sentiment", tgt_sent)):
        if val is not None and val not in VALID_SENTIMENTS:
            return _err(f"{label} must be one of {sorted(VALID_SENTIMENTS)} or null")

    centimetragem_raw = payload.get("centimetragem")
    centimetragem: float | None
    if centimetragem_raw in (None, ""):
        centimetragem = None
    else:
        try:
            centimetragem = float(centimetragem_raw)
        except (TypeError, ValueError):
            return _err("centimetragem must be numeric or null")

    classified_by = str(payload.get("classified_by") or "coworker").strip() or "coworker"

    mention_id = db.find_mention_id(article_id, target_key)
    if mention_id is None:
        return _err(f"no mention found for article {article_id} + target {target_key}", 404)

    classification_id = db.upsert_classification(
        mention_id=mention_id,
        article_sentiment=art_sent,
        target_sentiment=tgt_sent,
        centimetragem=centimetragem,
        classified_by=classified_by,
        ai_generated=bool(payload.get("ai_generated") or False),
    )

    raw_categories = payload.get("categories") or []
    if not isinstance(raw_categories, list):
        return _err("categories must be a list of names")
    category_ids = []
    for raw_name in raw_categories:
        name = str(raw_name or "").strip()
        if not name:
            continue
        category_ids.append(db.get_or_create_category(name, created_by=classified_by))
    db.set_classification_categories(classification_id, category_ids)

    return jsonify(
        {
            "ok": True,
            "classification_id": classification_id,
            "mention_id": mention_id,
            "article_id": article_id,
            "target_key": target_key,
            "article_sentiment": art_sent,
            "target_sentiment": tgt_sent,
            "centimetragem": centimetragem,
            "categories": [str(n).strip() for n in raw_categories if str(n).strip()],
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Clipping write API listening on http://{host}:{port} (db={_db_path})")
    app.run(host=host, port=port, debug=False)
