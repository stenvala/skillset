"""Command handler for apply -- install all skills declared in skillset.yaml."""

import os
import subprocess
import sys
from pathlib import Path

from skillset.commands.add import cmd_add
from skillset.paths import (
    SKILLSET_CONFIG_FILE,
    abbrev,
    find_skillset_root,
    get_global_skillset_path,
    load_skillset,
)


def _resolve_toml_path(file, g):
    """Resolve the skillset.yaml file path."""
    if file:
        return Path(file)
    if g:
        return get_global_skillset_path()
    skillset_root = find_skillset_root()
    if skillset_root:
        return skillset_root / SKILLSET_CONFIG_FILE
    return get_global_skillset_path()


def cmd_apply(*, file: str | None = None, g: bool = False) -> None:
    """Apply skillset.yaml -- install all declared skills."""
    file_path = _resolve_toml_path(file, g)

    if not file_path.exists():
        print(f"No skillset.yaml found at {abbrev(file_path)}")
        sys.exit(1)

    config = load_skillset(file_path)
    skills_config = config.get("skills")
    if skills_config is None:
        print("No skills section found in skillset.yaml")
        sys.exit(1)

    _apply_links(config.get("links", {}))

    for repo, value in skills_config.items():
        entry_skills, entry_copy, entry_subpath = _parse_apply_entry(repo, value)
        if entry_skills is None and entry_copy is None:
            continue
        print(f"\nAdding {repo}...")
        cmd_add(
            repo=repo,
            skills=entry_skills,
            subpath=entry_subpath,
            copy=entry_copy,
            no_cache=False,
            trial=False,
        )


def _apply_links(links_config):
    """Process links section from skillset.yaml."""
    for local_path, target in links_config.items():
        link = Path(local_path)
        if link.is_symlink():
            print(f"Link already exists: {local_path} -> {os.readlink(local_path)}")
        elif link.exists():
            print(f"Skipping {local_path}: exists and is not a symlink")
        else:
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(target)
            print(f"Linked {local_path} -> {target}")
        ignored = (
            subprocess.run(
                ["git", "check-ignore", "-q", local_path],
                capture_output=True,
            ).returncode
            == 0
        )
        if not ignored:
            print(f"  Warning: {local_path} is not in .gitignore")


def _parse_apply_entry(repo, value):
    """Parse a single skills config entry under the enabled/disabled schema.

    Returns (skills_filter, use_copy, subpath).
    skills_filter is None for "all", otherwise a list of names to install.
    """
    if not isinstance(value, dict):
        print(f"Invalid entry for {repo!r}: must be a mapping")
        sys.exit(1)

    enabled = value.get("enabled")
    subpath = value.get("path")
    use_copy = value.get("copy", False)

    if enabled is None or any(_looks_like_glob(e) for e in enabled):
        return None, use_copy, subpath

    if not enabled:
        return None, None, None  # explicitly nothing

    return list(enabled), use_copy, subpath


def _looks_like_glob(entry: str) -> bool:
    return any(c in entry for c in "*?[")
