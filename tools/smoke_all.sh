#!/usr/bin/env bash
# Run every CCM-2026-05-19 loop smoke in sequence against production.
# Each one exits non-zero on failure; this wrapper preserves exit codes
# but keeps going so the operator sees the full picture.
#
# Usage:
#   CLIPPING_ADMIN_PASSWORD=clipping-admin-2026 ./tools/smoke_all.sh
#   ./tools/smoke_all.sh --base http://localhost:8000

set -u
set -o pipefail
BASE_ARG=()
if [ "${1:-}" = "--base" ]; then
  BASE_ARG=(--base "$2")
fi

PASS=0
FAIL=0
FAILED_SMOKES=()
run() {
  local name="$1"
  shift
  echo
  echo "================================================================"
  echo " Smoke: $name"
  echo "================================================================"
  if "$@"; then
    PASS=$((PASS+1))
  else
    FAIL=$((FAIL+1))
    FAILED_SMOKES+=("$name")
  fi
}

# Goal coverage:
run "logged_out_render_smoke (Goal 4 — pre-auth)"     python tools/logged_out_render_smoke.py "${BASE_ARG[@]}"
run "authenticated_render_smoke (Goal 4 — viewer scope)" python tools/authenticated_render_smoke.py "${BASE_ARG[@]}"
run "admin_readonly_smoke (Goal 4 — admin GETs)"      python tools/admin_readonly_smoke.py "${BASE_ARG[@]}"
run "admin_viewers_smoke (Goal 1 — viewer CRUD)"      python tools/admin_viewers_smoke.py "${BASE_ARG[@]}"
run "targets_mgmt_smoke (Goal 5 — target ops)"        python tools/targets_mgmt_smoke.py "${BASE_ARG[@]}"
run "password_change_smoke (Goal 2 — change-password)" python tools/password_change_smoke.py "${BASE_ARG[@]}"
run "manual_story_smoke (Goal 4 — input gates)"        python tools/manual_story_smoke.py "${BASE_ARG[@]}"
run "categories_smoke (Goal 4 — idempotent CRUD)"      python tools/categories_smoke.py "${BASE_ARG[@]}"
run "classifications_smoke (Goal 4 — input gates)"     python tools/classifications_smoke.py "${BASE_ARG[@]}"
run "visual_smoke_playwright (Goals 1/2/3/5 — UI)"    .venv_playwright/bin/python tools/visual_smoke_playwright.py "${BASE_ARG[@]}"

echo
echo "================================================================"
echo " SUMMARY: $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
  echo " Failed: ${FAILED_SMOKES[*]}"
fi
echo "================================================================"

exit "$FAIL"
