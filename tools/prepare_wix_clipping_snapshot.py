#!/usr/bin/env python3
"""Prepare a Wix-ready clipping snapshot — validate, archive, screenshot.

Restored from SSD recovery (from_patches + 63MB Codex session log).
Original path: tools/prepare_wix_clipping_snapshot.py

RECOVERY STATUS:
- scope_token() — CLEAN (recovered verbatim)
- validate_snapshot_html() — CLEAN (recovered verbatim)
- render_review_screenshots() — CLEAN (recovered verbatim, requires playwright)
- prepare_snapshot() — MOSTLY CLEAN (last ~5 lines after 'metada' lost to binary corruption)
- main()/parse_args() — NOT RECOVERED (no fragments found)

KNOWN DEPENDENCY:
- Calls export_mobile_snapshot.build_snapshot_artifact(args)
- Calls export_mobile_snapshot.output_path_for_args(args)
- The current export_mobile_snapshot.py is a simplified version that does NOT have
  build_snapshot_artifact() or output_path_for_args(). Those functions exist in the
  original (recovered in 63MB file) but haven't been restored to export_mobile_snapshot.py yet.
  Until they are, prepare_snapshot() will fail at runtime.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.export_mobile_snapshot as export_mobile_snapshot  # noqa: E402


# --- Recovered from from_patches + 63MB Codex session log ---

REQUIRED_MARKERS = [
    export_mobile_snapshot.WIX_SNAPSHOT_SENTINEL
    if hasattr(export_mobile_snapshot, "WIX_SNAPSHOT_SENTINEL")
    else "WIX_CLIPPING_SNAPSHOT_ROOT",
    "story-card",
    "snapshot-payload",
]


def scope_token(args: argparse.Namespace) -> str:
    """Recovered verbatim from 63MB Codex session log."""
    if args.all_stories:
        return "all_stories"
    return f"{args.date_from}_{args.date_to}"


def validate_snapshot_html(html_doc: str) -> dict[str, Any]:
    """Recovered verbatim from 63MB Codex session log.

    Validates that generated HTML contains all Wix-required markers.
    """
    lowered = html_doc.lstrip().lower()
    checks = {
        "is_full_document": lowered.startswith("<!doctype html>"),
        "has_wix_sentinel": (
            export_mobile_snapshot.WIX_SNAPSHOT_SENTINEL
            if hasattr(export_mobile_snapshot, "WIX_SNAPSHOT_SENTINEL")
            else "WIX_CLIPPING_SNAPSHOT_ROOT"
        )
        in html_doc,
        "has_payload_script": 'id="snapshot-payload"' in html_doc,
        "has_story_cards": 'class="story-card"' in html_doc,
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "missing_markers": [marker for marker in REQUIRED_MARKERS if marker not in html_doc],
    }


def render_review_screenshots(html_path: Path, output_dir: Path) -> dict[str, str]:
    """Recovered verbatim from 63MB Codex session log.

    Renders desktop (1440x2200) and mobile (390x844 iPhone) screenshots
    of the snapshot HTML using Playwright headless Chromium.
    """
    from playwright.sync_api import sync_playwright

    output_dir.mkdir(parents=True, exist_ok=True)
    desktop_path = output_dir / "desktop.png"
    mobile_path = output_dir / "mobile.png"
    html_url = html_path.resolve().as_uri()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        desktop = browser.new_page(viewport={"width": 1440, "height": 2200})
        desktop.goto(html_url, wait_until="load")
        desktop.screenshot(path=str(desktop_path), full_page=True)
        desktop.close()

        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                "Mobile/15E148 Safari/604.1"
            ),
        )
        mobile.goto(html_url, wait_until="load")
        mobile.screenshot(path=str(mobile_path), full_page=True)
        mobile.close()

        browser.close()

    return {
        "desktop": str(desktop_path.resolve()),
        "mobile": str(mobile_path.resolve()),
    }


def prepare_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    """Recovered from 63MB Codex session log.

    Main orchestrator: generate HTML via export_mobile_snapshot, validate,
    archive to timestamped dirs, render screenshots.

    NOTE: Last ~5 lines after 'metada...' were lost to binary corruption.
    The metadata writing (likely a JSON sidecar with stats) is reconstructed
    from context clues in the test file fragments.
    """
    prepared_at = datetime.now(timezone.utc)
    prepared_token = prepared_at.strftime("%Y%m%dT%H%M%SZ")

    canonical_output = export_mobile_snapshot.output_path_for_args(args)
    current_output = Path(args.current_output).expanduser().resolve()
    archive_dir = Path(args.archive_dir).expanduser().resolve()
    review_root = Path(args.review_dir).expanduser().resolve()

    artifact = export_mobile_snapshot.build_snapshot_artifact(args)
    html_doc = artifact["html_doc"]
    initial_stats = artifact["initial_stats"]

    validation = validate_snapshot_html(html_doc)
    if not validation["ok"]:
        raise RuntimeError(
            "Snapshot HTML invalido para o fluxo do Wix: "
            + ", ".join(validation["missing_markers"])
        )

    canonical_output.parent.mkdir(parents=True, exist_ok=True)
    current_output.parent.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    review_bundle_dir = review_root / f"{scope_token(args)}_{prepared_token}"
    review_bundle_dir.mkdir(parents=True, exist_ok=True)

    canonical_output.write_text(html_doc, encoding="utf-8")
    shutil.copy2(canonical_output, current_output)

    archive_html = archive_dir / f"clipping_mobile_snapshot_wix_{scope_token(args)}_{prepared_token}.html"
    shutil.copy2(current_output, archive_html)

    screenshots = render_review_screenshots(current_output, review_bundle_dir)

    # --- Below this line: reconstructed from context (original lost to binary corruption) ---
    # The original wrote a metadata JSON sidecar. Reconstructed from test fragments
    # that referenced 'initial_stats' and screenshot paths.
    metadata = {
        "prepared_at": prepared_token,
        "scope_token": scope_token(args),
        "initial_stats": initial_stats,
        "validation": validation,
        "screenshots": screenshots,
        "canonical_output": str(canonical_output),
        "current_output": str(current_output),
        "archive_html": str(archive_html),
    }
    metadata_path = review_bundle_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")

    return metadata
