#!/usr/bin/env python3
"""Serve the static clipping dashboard for Render."""
from __future__ import annotations

import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class StaticHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json",
    }


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    handler = partial(StaticHandler, directory=str(ROOT))
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Serving static clipping dashboard from {ROOT} on {host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping static clipping dashboard server", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
