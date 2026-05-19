# Viewer Profile Scope Review - 2026-05-20

_Created by Atlas/Codex during the segregation product loop._

This review records the non-secret profile scope boundary. It does not contain
passwords and does not prove authenticated Render login by itself.

## Current Profile Shape

Source:

```text
data/viewer_profiles.json
data/targets.json
```

Current profiles:

```text
flavio -> flavio_valle, pedro_duarte, pedro_angelito, bernardo_rubiao
shakira -> shakira
rio_economico -> rio_economico topic-only key
demo_cliente -> empty scope
```

Current production target rows:

```text
flavio_valle
pedro_duarte
pedro_angelito
bernardo_rubiao
shakira
```

## Guardrail

`rio_economico` is intentionally allowed as a profile scope key while remaining
absent from `data/targets.json`. That keeps Rio on the scoped topic-report path
and prevents an accidental plain keyword target row.

`demo_cliente` is the only profile currently allowed to have an empty scope.
Unknown viewer profiles also resolve to empty scope in the app, but they should
not be used as a product surface without an explicit profile row.

## Checker

Run:

```bash
python3 -B tools/viewer_profiles_check.py
```

Current expected result:

```text
ok=true
profile_count=4
target_count=5
topic_only_keys_present_as_targets=[]
demo_cliente target_count=0
rio_economico target_keys=[rio_economico]
```

The checker fails if:

```text
a required profile is missing
admin is defined as a viewer profile
default_targets are outside target_keys
a profile references an unknown target key
rio_economico appears as a production target row before the Rio gate passes
demo_cliente stops being empty
```

## Product Meaning

This guard does not replace live authentication smoke. It makes the non-secret
scope file reviewable and prevents a future edit from silently turning profile
segregation into a broad or fake surface.
