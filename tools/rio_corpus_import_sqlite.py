#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from web_app.rio_corpus import rio_corpus


def main() -> int:
    parser = argparse.ArgumentParser(description="Idempotently import Rio rows from legacy SQLite into the corpus ledger.")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(rio_corpus.import_legacy_sqlite(limit=max(0, args.limit)), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
