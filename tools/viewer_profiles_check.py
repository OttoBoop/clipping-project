#!/usr/bin/env python3
"""Validate non-secret viewer profile scopes against target configuration."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILES = PROJECT_ROOT / "data" / "viewer_profiles.json"
DEFAULT_TARGETS = PROJECT_ROOT / "data" / "targets.json"
DEFAULT_REQUIRED_PROFILES = ("flavio", "shakira", "rio_economico", "demo_cliente")
DEFAULT_EMPTY_SCOPE_PROFILES = {"demo_cliente"}
DEFAULT_TOPIC_ONLY_KEYS = {"rio_economico"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def profiles_from_payload(payload: Any) -> dict[str, dict[str, Any]]:
    profiles = payload.get("profiles") if isinstance(payload, dict) else payload
    if not isinstance(profiles, dict):
        raise ValueError("viewer profiles payload must contain a profiles object")
    return {str(key).strip(): value for key, value in profiles.items() if str(key).strip()}


def targets_from_payload(payload: Any) -> dict[str, dict[str, Any]]:
    rows = payload.get("targets") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("targets payload must contain a target list")
    targets: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "").strip()
        if key:
            targets[key] = row
    return targets


def clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def duplicate_values(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def validate_profiles(
    profiles_payload: Any,
    targets_payload: Any,
    *,
    required_profiles: tuple[str, ...] = DEFAULT_REQUIRED_PROFILES,
    empty_scope_profiles: set[str] = DEFAULT_EMPTY_SCOPE_PROFILES,
    topic_only_keys: set[str] = DEFAULT_TOPIC_ONLY_KEYS,
) -> dict[str, Any]:
    failures: list[str] = []
    profiles = profiles_from_payload(profiles_payload)
    targets = targets_from_payload(targets_payload)
    target_keys = set(targets)

    for required in required_profiles:
        if required not in profiles:
            failures.append(f"missing required profile: {required}")

    if "admin" in profiles:
        failures.append("viewer_profiles.json must not define admin as a viewer profile")

    profile_summaries: dict[str, dict[str, Any]] = {}
    for profile_key, row in sorted(profiles.items()):
        if not isinstance(row, dict):
            failures.append(f"profile {profile_key} must be an object")
            continue
        target_list = clean_list(row.get("target_keys") or row.get("targetKeys"))
        default_list = clean_list(row.get("default_targets") or row.get("defaultTargets"))
        if duplicate_values(target_list):
            failures.append(f"profile {profile_key} has duplicate target_keys: {duplicate_values(target_list)}")
        if duplicate_values(default_list):
            failures.append(f"profile {profile_key} has duplicate default_targets: {duplicate_values(default_list)}")
        if not target_list and profile_key not in empty_scope_profiles:
            failures.append(f"profile {profile_key} has empty target_keys without being allowlisted as empty")
        for default_target in default_list:
            if default_target not in target_list:
                failures.append(f"profile {profile_key} default target outside scope: {default_target}")
        for target_key in target_list:
            if target_key not in target_keys and target_key not in topic_only_keys:
                failures.append(f"profile {profile_key} references unknown target key: {target_key}")
        profile_summaries[profile_key] = {
            "target_count": len(target_list),
            "default_count": len(default_list),
            "target_keys": target_list,
        }

    topic_keys_present_as_targets = sorted(key for key in topic_only_keys if key in target_keys)
    for key in topic_keys_present_as_targets:
        failures.append(f"topic-only key must not be a production target row yet: {key}")

    return {
        "ok": not failures,
        "profile_count": len(profiles),
        "target_count": len(targets),
        "profiles": profile_summaries,
        "topic_only_keys": sorted(topic_only_keys),
        "topic_only_keys_present_as_targets": topic_keys_present_as_targets,
        "failures": failures,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate viewer profile scopes.")
    parser.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate_profiles(load_json(args.profiles), load_json(args.targets))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
