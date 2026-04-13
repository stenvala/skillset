"""Tests for skillset.settings."""

import json
from pathlib import Path

from skillset.settings import (
    add_read_permission,
    deep_merge,
    find_repo_permissions,
    load_settings,
    save_settings,
)


def test_load_settings_missing(tmp_path):
    assert load_settings(tmp_path / "nope.json") == {}


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "settings.json"
    data = {"permissions": {"allow": ["Read(**/**)"]}}
    save_settings(path, data)
    assert load_settings(path) == data


def test_deep_merge_dicts():
    base = {"a": {"x": 1}, "b": 2}
    override = {"a": {"y": 3}, "c": 4}
    result = deep_merge(base, override)
    assert result == {"a": {"x": 1, "y": 3}, "b": 2, "c": 4}


def test_deep_merge_lists():
    base = {"allow": ["a", "b"]}
    override = {"allow": ["b", "c"]}
    result = deep_merge(base, override)
    assert set(result["allow"]) == {"a", "b", "c"}


def test_deep_merge_override_scalar():
    base = {"key": "old"}
    override = {"key": "new"}
    assert deep_merge(base, override) == {"key": "new"}


def test_find_repo_permissions_settings_json(tmp_path):
    (tmp_path / "settings.json").write_text(json.dumps({"permissions": {"allow": []}}))
    result = find_repo_permissions(tmp_path)
    assert result == {"permissions": {"allow": []}}


def test_find_repo_permissions_fallback(tmp_path):
    (tmp_path / "permissions.json").write_text(json.dumps({"perms": True}))
    result = find_repo_permissions(tmp_path)
    assert result == {"perms": True}


def test_find_repo_permissions_none(tmp_path):
    assert find_repo_permissions(tmp_path) is None


def test_add_read_permission(tmp_path):
    settings_path = tmp_path / "settings.json"
    target = tmp_path / "repo"
    add_read_permission(settings_path, target)
    data = load_settings(settings_path)
    assert f"Read({target}/**)" in data["permissions"]["allow"]


def test_add_read_permission_no_duplicate(tmp_path):
    settings_path = tmp_path / "settings.json"
    target = tmp_path / "repo"
    add_read_permission(settings_path, target)
    add_read_permission(settings_path, target)
    data = load_settings(settings_path)
    assert data["permissions"]["allow"].count(f"Read({target}/**)") == 1
