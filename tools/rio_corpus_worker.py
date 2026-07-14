#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import os
import signal
import socket
import threading
import time

from web_app.rio_corpus import rio_corpus


STOP = False


def _stop(_signum, _frame) -> None:
    global STOP
    STOP = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process durable Rio corpus source windows.")
    parser.add_argument("--once", action="store_true", help="Claim at most one source window and exit.")
    parser.add_argument("--poll-seconds", type=float, default=3.0)
    parser.add_argument("--worker-id", default="")
    parser.add_argument("--run-workers", type=int, default=int(os.environ.get("RIO_CORPUS_RUN_WORKERS") or 3))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    worker_id = args.worker_id or f"{socket.gethostname()}:{os.getpid()}"
    rio_corpus.ensure_schema()
    run_workers = 1 if args.once else max(1, min(8, int(args.run_workers or 1)))
    logging.info("Rio corpus worker ready worker_id=%s run_workers=%s", worker_id, run_workers)

    def loop(index: int) -> None:
        thread_id = f"{worker_id}:{index}"
        while not STOP:
            result = rio_corpus.run_worker_once(worker_id=thread_id)
            logging.info("Rio corpus worker result=%s", result)
            if args.once:
                break
            if result.get("status") == "idle":
                time.sleep(max(0.25, args.poll_seconds))

    threads = [threading.Thread(target=loop, args=(index,), name=f"rio-source-run-{index}") for index in range(run_workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
