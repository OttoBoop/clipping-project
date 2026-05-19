from __future__ import annotations

from tools import viewer_profiles_check as check


TARGETS = {
    "targets": [
        {"key": "flavio_valle"},
        {"key": "pedro_duarte"},
        {"key": "pedro_angelito"},
        {"key": "bernardo_rubiao"},
        {"key": "shakira"},
    ]
}

PROFILES = {
    "profiles": {
        "flavio": {
            "label": "Flavio",
            "target_keys": ["flavio_valle", "pedro_duarte"],
            "default_targets": ["flavio_valle"],
        },
        "shakira": {
            "label": "Shakira",
            "target_keys": ["shakira"],
            "default_targets": ["shakira"],
        },
        "rio_economico": {
            "label": "Rio",
            "target_keys": ["rio_economico"],
            "default_targets": ["rio_economico"],
        },
        "demo_cliente": {
            "label": "Demo",
            "target_keys": [],
            "default_targets": [],
        },
    }
}


def test_current_profile_shape_allows_topic_only_rio_and_empty_demo():
    result = check.validate_profiles(PROFILES, TARGETS)

    assert result["ok"] is True
    assert result["profiles"]["rio_economico"]["target_keys"] == ["rio_economico"]
    assert result["topic_only_keys_present_as_targets"] == []


def test_default_targets_must_stay_inside_profile_scope():
    profiles = {
        "profiles": {
            **PROFILES["profiles"],
            "shakira": {
                "label": "Shakira",
                "target_keys": ["shakira"],
                "default_targets": ["flavio_valle"],
            },
        }
    }

    result = check.validate_profiles(profiles, TARGETS)

    assert result["ok"] is False
    assert "profile shakira default target outside scope: flavio_valle" in result["failures"]


def test_unknown_target_keys_fail_unless_topic_only():
    profiles = {
        "profiles": {
            **PROFILES["profiles"],
            "shakira": {
                "label": "Shakira",
                "target_keys": ["shakira", "unknown_client"],
                "default_targets": ["shakira"],
            },
        }
    }

    result = check.validate_profiles(profiles, TARGETS)

    assert result["ok"] is False
    assert "profile shakira references unknown target key: unknown_client" in result["failures"]


def test_rio_topic_key_must_not_be_a_plain_production_target_yet():
    targets = {"targets": [*TARGETS["targets"], {"key": "rio_economico"}]}

    result = check.validate_profiles(PROFILES, targets)

    assert result["ok"] is False
    assert "topic-only key must not be a production target row yet: rio_economico" in result["failures"]


def test_repository_viewer_profiles_pass_current_scope_guard():
    result = check.validate_profiles(check.load_json(check.DEFAULT_PROFILES), check.load_json(check.DEFAULT_TARGETS))

    assert result["ok"] is True
    assert result["profile_count"] == 4
    assert result["target_count"] == 5
    assert result["profiles"]["demo_cliente"]["target_count"] == 0
    assert result["profiles"]["rio_economico"]["target_keys"] == ["rio_economico"]
