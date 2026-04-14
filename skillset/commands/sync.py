"""Command handler for sync."""

import sys
from pathlib import Path

from skillset.commands._templates import SYNC_META_KEYS
from skillset.commands.update import _resolve_toml_path
from skillset.discovery import find_skills
from skillset.linking import is_managed, link_commands, link_skills, remove_managed
from skillset.manifest import record_install
from skillset.paths import (
    abbrev,
    get_global_commands_dir,
    get_global_skills_dir,
    get_global_skillset_path,
    update_skillset_skills,
)
from skillset.repo import clone_or_pull, parse_repo_spec
from skillset.ui import register_local_lib


def cmd_sync(*, file: str | None = None, g: bool = False) -> None:
    """Sync skills from skillset.toml -- pull repos, link skills, report new."""
    import tomllib

    file_path = _resolve_toml_path(file, g)
    is_local = file_path != get_global_skillset_path()

    if not file_path.exists():
        print(f"No skillset.toml at {abbrev(file_path)}")
        hint = "'skillset init'" if is_local else "'skillset init --global'"
        print(f"Run {hint} to create one.")
        sys.exit(1)

    with open(file_path, "rb") as f:
        config = tomllib.load(f)

    skills_config = config.get("skills", {})
    if not skills_config:
        print("No [skills] entries in skillset.toml")
        return

    skills_dir, commands_dir = _sync_dirs(is_local, file_path)
    scope = "local" if is_local else "global"
    total_linked = 0
    new_skills_found: dict[str, list[str]] = {}
    new_skills_ctx: dict[str, tuple[Path, bool]] = {}

    for repo_key, value in skills_config.items():
        linked = _sync_entry(
            repo_key,
            value,
            skills_dir,
            commands_dir,
            scope,
            new_skills_found,
            new_skills_ctx,
        )
        total_linked += linked

    total_linked += _prompt_for_new_skills(new_skills_found, new_skills_ctx, skills_dir, file_path)

    print(f"\nSync complete ({total_linked} skill(s) linked)")


def _sync_dirs(is_local, file_path):
    """Return (skills_dir, commands_dir) for sync."""
    if is_local:
        local_root = file_path.parent
        return (
            local_root / ".claude" / "skills",
            local_root / ".claude" / "commands",
        )
    return get_global_skills_dir(), get_global_commands_dir()


def _sync_entry(repo_key, value, skills_dir, commands_dir, scope, new_found, new_ctx):
    """Sync a single entry. Returns count of linked skills."""
    if isinstance(value, bool):
        return _sync_bool_entry(repo_key, value, skills_dir, commands_dir, scope)
    if isinstance(value, dict):
        return _sync_dict_entry(
            repo_key,
            value,
            skills_dir,
            commands_dir,
            scope,
            new_found,
            new_ctx,
        )
    print(f"\nSkipping {repo_key}: invalid value type")
    return 0


def _sync_bool_entry(repo_key, value, skills_dir, commands_dir, scope):
    """Sync a bool entry (true = all skills)."""
    if not value:
        return 0
    print(f"\nSyncing {repo_key}...")
    try:
        owner, repo_name = parse_repo_spec(repo_key)
    except ValueError as e:
        print(f"  {e}")
        return 0
    repo_dir = clone_or_pull(owner, repo_name)
    linked = link_skills(repo_dir, skills_dir)
    link_commands(repo_dir, commands_dir)
    if linked:
        record_install(f"{owner}/{repo_name}", scope=scope)
    for name in sorted(linked):
        print(f"  + {name}")
    return len(linked)


def _sync_dict_entry(
    repo_key,
    value,
    skills_dir,
    commands_dir,
    scope,
    new_found,
    new_ctx,
):
    """Sync a dict entry (selective skills, editable, etc.)."""
    editable = value.get("editable", False)
    path_str = value.get("path")
    source_str = value.get("source")
    use_copy = value.get("copy", False)
    skill_entries = {k: v for k, v in value.items() if k not in SYNC_META_KEYS}

    source_dir, repo_dir, owner, repo_name = _resolve_sync_source(
        repo_key,
        editable,
        source_str,
        path_str,
    )
    if source_dir is None:
        return 0

    available = find_skills(source_dir)
    available_names = {s.name for s in available}
    total = 0

    if skill_entries:
        total = _sync_selective(
            skill_entries,
            available_names,
            source_dir,
            skills_dir,
            use_copy,
            repo_key,
            new_found,
            new_ctx,
        )
    else:
        linked = link_skills(source_dir, skills_dir, copy=use_copy)
        link_commands(source_dir, commands_dir, copy=use_copy)
        total = len(linked)
        for name in sorted(linked):
            print(f"  + {name}")

    if not editable:
        record_install(
            f"{owner}/{repo_name}",
            subpath=path_str,
            copy=use_copy,
            scope=scope,
        )
    return total


def _resolve_sync_source(repo_key, editable, source_str, path_str):
    """Resolve source directory for sync."""
    owner = repo_name = None
    if editable:
        return _resolve_editable_source(repo_key, source_str, path_str, owner, repo_name)

    print(f"\nSyncing {repo_key}...")
    try:
        owner, repo_name = parse_repo_spec(repo_key)
    except ValueError as e:
        print(f"  {e}")
        return None, None, None, None
    repo_dir = clone_or_pull(owner, repo_name)
    source_dir = repo_dir / path_str if path_str else repo_dir
    if path_str and not source_dir.is_dir():
        print(f"  Path not found in repo: {path_str}")
        return None, None, None, None
    return source_dir, repo_dir, owner, repo_name


def _resolve_editable_source(repo_key, source_str, path_str, owner, repo_name):
    """Resolve editable source directory for sync."""
    if not source_str:
        print(f"\n{repo_key}: editable requires 'source' path")
        return None, None, None, None
    print(f"\nSyncing {repo_key} (editable)...")
    base_dir = Path(source_str).expanduser().resolve()
    if not base_dir.is_dir():
        print(f"  Source not found: {source_str}")
        return None, None, None, None
    source_dir = base_dir / path_str if path_str else base_dir
    if path_str and not source_dir.is_dir():
        print(f"  Path not found: {path_str} in {source_str}")
        return None, None, None, None
    register_local_lib(base_dir)
    return source_dir, base_dir, owner, repo_name


def _sync_selective(
    skill_entries,
    available_names,
    source_dir,
    skills_dir,
    use_copy,
    repo_key,
    new_found,
    new_ctx,
):
    """Handle selective skill sync. Returns count of linked skills."""
    enabled = {k for k, v in skill_entries.items() if v is True}
    disabled = {k for k, v in skill_entries.items() if v is False}
    new = available_names - (enabled | disabled)
    if new:
        new_found[repo_key] = sorted(new)
        new_ctx[repo_key] = (source_dir, use_copy)

    total = 0
    if enabled:
        linked = link_skills(source_dir, skills_dir, only=enabled, copy=use_copy)
        total = len(linked)
        for name in sorted(linked):
            print(f"  + {name}")

    for skill_name in disabled:
        skill_path = skills_dir / skill_name
        if skill_path.exists() and is_managed(skill_path):
            remove_managed(skill_path)
            print(f"  - {skill_name} (excluded)")

    return total


def _collect_new_skill_decisions(names, source_dir, skills_dir, use_copy):
    """Collect user decisions for new skills. Returns (decisions, linked_count)."""
    prompt = "\nAdd [a]ll / [i]gnore all / [s]elect individually? [a/i/s] "
    choice = input(prompt).strip().lower()

    if choice in ("a", "all"):
        linked = link_skills(source_dir, skills_dir, only=set(names), copy=use_copy)
        for name in names:
            print(f"  + {name}")
        return {name: True for name in names}, len(linked)

    if choice in ("i", "ignore"):
        for name in names:
            print(f"  - {name} (skipped)")
        return {name: False for name in names}, 0

    return _collect_individual_decisions(names, source_dir, skills_dir, use_copy)


def _collect_individual_decisions(names, source_dir, skills_dir, use_copy):
    """Collect individual yes/no decisions for each skill."""
    decisions = {}
    total = 0
    for name in names:
        accepted = input(f"  Add {name}? [y/N] ").strip().lower() in ("y", "yes")
        decisions[name] = accepted
        if accepted:
            total += len(link_skills(source_dir, skills_dir, only={name}, copy=use_copy))
            print(f"  + {name}")
        else:
            print(f"  - {name} (skipped)")
    return decisions, total


def _prompt_for_new_skills(new_skills_found, new_skills_ctx, skills_dir, file_path):
    """Prompt user for new untracked skills. Returns count of linked skills."""
    if not new_skills_found:
        return 0

    total = 0
    print("\n--- New skills detected ---")
    for repo_key, names in new_skills_found.items():
        source_dir, use_copy = new_skills_ctx[repo_key]
        print(f"\n{repo_key}: {len(names)} new skill(s):")
        for name in names:
            print(f"  {name}")

        decisions, linked = _collect_new_skill_decisions(names, source_dir, skills_dir, use_copy)
        total += linked

        if decisions:
            update_skillset_skills(file_path, repo_key, decisions)
            print(f"  Updated {abbrev(file_path)}")

    return total
