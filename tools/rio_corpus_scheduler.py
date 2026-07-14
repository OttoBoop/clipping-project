#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys

import requests


def main() -> int:
    base_url = str(os.environ.get("CLIPPING_BASE_URL") or "https://clipping-project.onrender.com").rstrip("/")
    token = str(os.environ.get("RIO_CORPUS_CRON_TOKEN") or "").strip()
    if not token:
        print("RIO_CORPUS_CRON_TOKEN is not configured", file=sys.stderr)
        return 2
    try:
        response = requests.post(
            f"{base_url}/api/rio/schedule",
            headers={"Authorization": f"Bearer {token}"},
            timeout=45,
        )
    except requests.RequestException as exc:
        print(f"scheduler request failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    try:
        payload = response.json()
    except ValueError:
        payload = {"body": response.text[:500]}
    print(json.dumps({"status": response.status_code, "response": payload}, ensure_ascii=False))
    return 0 if response.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
