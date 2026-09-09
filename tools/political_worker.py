#!/usr/bin/env python3
"""Supervised political worker. No scheduler: claims only user-requested jobs."""
from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
import signal
import socket
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web_app.political_corpus import political_corpus

log = logging.getLogger("political_worker")


def worker_loop(service, kind: str, worker_id: str, stop: threading.Event, *, once=False) -> None:
    failures = 0
    while not stop.is_set():
        task = None
        lease_stop = threading.Event()
        try:
            service.heartbeat(worker_id, kind)
            task = service.claim_task(kind, worker_id=worker_id)
            if task:
                service.heartbeat(worker_id, kind, task["id"])

                def renew():
                    while not lease_stop.wait(20):
                        try:
                            if not service.renew_lease(task):
                                return
                            service.heartbeat(worker_id, kind, task["id"])
                        except Exception as exc:
                            log.warning("lease renewal failed worker=%s error_type=%s", worker_id, type(exc).__name__)

                renewer = threading.Thread(target=renew, name=f"{worker_id}-lease", daemon=True)
                renewer.start()
                try:
                    result = service.process_task(task)
                    log.info("task complete worker=%s task=%s status=%s", worker_id, task["id"], result.get("status"))
                finally:
                    lease_stop.set()
                    renewer.join(timeout=5)
            failures = 0
            service.heartbeat(worker_id, kind)
            if once:
                return
            if not task:
                stop.wait(2)
        except Exception as exc:
            lease_stop.set()
            failures += 1
            log.warning("worker iteration failed worker=%s error_type=%s failures=%s", worker_id, type(exc).__name__, failures)
            try:
                service.heartbeat(worker_id, kind, error_type=type(exc).__name__)
            except Exception:
                pass
            if once:
                raise
            stop.wait(min(30, 2 ** min(failures, 5)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    political_corpus.ensure_schema()
    identity = f"{socket.gethostname()}:{os.getpid()}"
    failed = threading.Event()

    def supervised(kind, worker_id):
        try:
            worker_loop(political_corpus, kind, worker_id, stop, once=args.once)
        except Exception as exc:
            failed.set()
            log.error("worker stopped worker=%s error_type=%s", worker_id, type(exc).__name__)

    threads = [threading.Thread(target=supervised, args=(kind, f"{identity}:{kind}:{i}"),
                                daemon=True, name=f"political-{kind}-{i}")
               for kind, count in (("discovery", 1 if args.once else 2), ("fetch", 1 if args.once else 4))
               for i in range(count)]
    for thread in threads:
        thread.start()
    if args.once:
        for thread in threads:
            thread.join()
        return 1 if failed.is_set() else 0
    while not stop.wait(1):
        if any(not thread.is_alive() for thread in threads):
            log.error("worker capacity lost; exiting for process supervision")
            stop.set()
            return 1
    deadline = time.monotonic() + 25
    for thread in threads:
        thread.join(timeout=max(0, deadline - time.monotonic()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
