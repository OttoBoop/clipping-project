from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ASSETS_DIR = ROOT / "assets"
REPORTS_DIR = DATA_DIR / "reports"


def db_path() -> Path:
    configured = os.environ.get("CLIPPING_DB_PATH", "").strip()
    return Path(configured).expanduser().resolve() if configured else DATA_DIR / "clipping.db"


def local_writes_allowed() -> bool:
    return os.environ.get("CLIPPING_ALLOW_LOCAL_WRITES", "").strip() == "1"

