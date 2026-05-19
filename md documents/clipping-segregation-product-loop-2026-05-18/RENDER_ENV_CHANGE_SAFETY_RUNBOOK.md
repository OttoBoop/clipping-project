# Render Env Change Safety Runbook

_Created 2026-05-18 by Atlas/Codex._

Use this before changing Render environment variables for passwords, profile
access, storage, or deploy behavior.

## Rule

Do not replace the full Render environment to change one password.

Use merge/update semantics for the specific key being changed, and never print
or commit secret values.

## When This Applies

- adding a prospect viewer password;
- rotating a viewer password after a demo;
- removing a viewer password during offboarding;
- changing `CLIPPING_VIEWER_PASSWORDS`;
- changing `CLIPPING_SESSION_SECRET`;
- changing storage/admin env vars that affect the live app.

## Pre-Change Checklist

Write down non-secret intent first:

```text
profile_key:
change_type: add / rotate / remove / emergency_rotate
reason:
scope_file_change_needed: yes / no
expected_post_change_profiles:
operator:
```

Then verify:

```text
git status checked
no password value is in the worktree
data/viewer_profiles.json has the intended non-secret scope
logged-out Render smoke currently passes or current failure is logged
```

## Safe Render MCP Pattern

Use `update_environment_variables` only with the exact env var(s) that must
change.

Required:

```text
replace=false
envVars includes only the intended key(s)
no unrelated env vars are rewritten
secret value is not echoed into WORK_LOG.md
```

Never use:

```text
replace=true
copy/paste of the full current environment into chat/logs
password values in markdown
password values in git commit messages
```

## Post-Change Verification

After Render applies the env change:

```text
GET /healthz -> 200
viewerAuthConfigured=true
viewerProfilesConfigured=true
missingConfig=[]
logged-out /assets/clipping-data.json -> 401
logged-out /assets/clipping-raw-texts.json -> 401
target profile login -> expected profile
target profile /api/targets -> only approved targets
target profile /api/update/live-results?target_key=<forbidden> -> empty
target profile POST /api/targets -> 401/403
```

For offboarding:

```text
old password no longer logs in
profile has no stale target scope unless intentionally retained
unused prospect password is absent from CLIPPING_VIEWER_PASSWORDS
```

## Logging Rule

Log only non-secret evidence in `WORK_LOG.md`:

```text
profile key changed
change type
Render health result
scoped smoke result
old access removed: yes/no/blocked
next follow-up
```

Never log:

```text
password value
full CLIPPING_VIEWER_PASSWORDS value
session secret
storage credentials
private buyer contact details
```

## Emergency Rollback

If an env change breaks login or storage:

1. Do not guess secrets from memory.
2. Restore only the affected env var from the operator's secret store.
3. Keep `replace=false`.
4. Hit `/healthz`.
5. Run logged-out payload/API smoke.
6. Record the non-secret failure and rollback result in `WORK_LOG.md`.
