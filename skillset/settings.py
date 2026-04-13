"""Claude settings and permissions management."""

import json
from pathlib import Path

from skillset.builtins import PRESETS as BUILTIN_PRESETS


def load_settings(settings_path: Path) -> dict:
    """Load Claude settings from a path."""
    if settings_path.exists():
        return json.loads(settings_path.read_text())
    return {}


def save_settings(settings_path: Path, settings: dict) -> None:
    """Save Claude settings to a path."""
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")


def find_repo_permissions(repo_dir: Path) -> dict | None:
    """Find and load permissions file from repo root."""
    for name in ("settings.json", "permissions.json", "claude-settings.json"):
        path = repo_dir / name
        if path.exists():
            return json.loads(path.read_text())
    return None


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries, with override taking precedence."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            result[key] = list(set(result[key] + value))
        else:
            result[key] = value
    return result


def merge_permissions(repo_dir: Path, settings_path: Path) -> list[str]:
    """Merge repo permissions into target settings."""
    repo_perms = find_repo_permissions(repo_dir)
    if not repo_perms:
        return []
    existing = load_settings(settings_path)
    merged = deep_merge(existing, repo_perms)
    save_settings(settings_path, merged)
    return list(repo_perms.keys())


def get_preset(name: str) -> dict | None:
    """Get a preset by name."""
    return BUILTIN_PRESETS.get(name)


def add_read_permission(settings_path: Path, target_path: Path) -> None:
    """Add Read permission for a path to settings."""
    perm = f"Read({target_path}/**)"
    settings = load_settings(settings_path)
    allow_list = settings.setdefault("permissions", {}).setdefault("allow", [])
    if perm not in allow_list:
        allow_list.append(perm)
        save_settings(settings_path, settings)
