"""Command handlers for update and apply."""

import os
import subprocess
import sys
from pathlib import Path

from skillset.commands.add import cmd_add
from skillset.linking import is_link, link_commands, link_skills
from skillset.manifest import get_install_options
from skillset.paths import (
    abbrev,
    find_skillset_root,
    get_cache_dir,
    get_git_root,
    get_global_commands_dir,
    get_global_skills_dir,
    get_global_skillset_path,
)
from skillset.repo import clone_or_pull, get_repo_dir, parse_repo_spec


def _resolve_update_options(
    repo_key: str, *, copy: bool = False, g: bool = False
) -> tuple[str | None, bool, str]:
    """Resolve subpath/copy/scope from manifest, with CLI flags as overrides."""
    opts = get_install_options(repo_key) or {}
    use_copy = copy or opts.get("copy", False)
    subpath = opts.get("subpath")
    scope = opts.get("scope", "global")
    if g:
        scope = "global"
    return subpath, use_copy, scope


def _scope_dirs(scope, skillset_root):
    """Return (skills_dir, commands_dir) for the given scope."""
    if scope == "global" or not skillset_root:
        return get_global_skills_dir(), get_global_commands_dir()
    return (
        skillset_root / ".claude" / "skills",
        skillset_root / ".claude" / "commands",
    )


def cmd_update(
    *,
    repo: str | None = None,
    g: bool = False,
    copy: bool = False,
    new: bool = False,
) -> None:
    """Update repo(s) and refresh links (or copies) and permissions."""
    cache_dir = get_cache_dir()
    existing_only = not new

    if repo:
        _update_single_repo(repo, g, copy, existing_only)
    else:
        _update_all_repos(cache_dir, g, copy, existing_only)


def _update_single_repo(repo, g, copy, existing_only):
    """Update a single repo by spec."""
    try:
        owner, repo_name = parse_repo_spec(repo)
    except ValueError as e:
        print(str(e))
        sys.exit(1)

    repo_dir = get_repo_dir(owner, repo_name)
    if not repo_dir.exists():
        print(f"Repo {repo} not installed. Use 'skillset add {repo}' first.")
        sys.exit(1)

    if not is_link(repo_dir):
        clone_or_pull(owner, repo_name)

    repo_key = f"{owner}/{repo_name}"
    subpath, use_copy, scope = _resolve_update_options(repo_key, copy=copy, g=g)
    target_dir = repo_dir / subpath if subpath else repo_dir

    skillset_root = find_skillset_root()
    skills_dir, commands_dir = _scope_dirs(scope, skillset_root)
    linked_skills = link_skills(target_dir, skills_dir, copy=use_copy, existing_only=existing_only)
    linked_commands = link_commands(
        target_dir, commands_dir, copy=use_copy, existing_only=existing_only
    )
    print(f"Updated {len(linked_skills)} skill(s), {len(linked_commands)} command(s)")


def _update_all_repos(cache_dir, g, copy, existing_only):
    """Update all cached repos."""
    total_skills = 0
    total_commands = 0

    if cache_dir.exists():
        for owner_dir in cache_dir.iterdir():
            if not owner_dir.is_dir():
                continue
            for repo_dir in owner_dir.iterdir():
                if not repo_dir.is_dir():
                    continue
                if not is_link(repo_dir):
                    clone_or_pull(owner_dir.name, repo_dir.name)
                resolved = repo_dir.resolve() if is_link(repo_dir) else repo_dir
                repo_key = f"{owner_dir.name}/{repo_dir.name}"
                subpath, use_copy, scope = _resolve_update_options(repo_key, copy=copy, g=g)
                source_dir = resolved / subpath if subpath else resolved

                root = find_skillset_root()
                if scope == "local" and root is None and get_git_root() is None:
                    print(f"  Skipping {repo_key} (local scope, not in a git repo)")
                    continue
                skills_dir, commands_dir = _scope_dirs(scope, root)
                total_skills += len(
                    link_skills(
                        source_dir,
                        skills_dir,
                        copy=use_copy,
                        existing_only=existing_only,
                    )
                )
                total_commands += len(
                    link_commands(
                        source_dir,
                        commands_dir,
                        copy=use_copy,
                        existing_only=existing_only,
                    )
                )

    if total_skills == 0 and total_commands == 0:
        print("No repos installed")
    else:
        print(f"Updated ({total_skills} skill(s), {total_commands} command(s))")


def _resolve_toml_path(file, g):
    """Resolve the skillset.toml file path."""
    if file:
        return Path(file)
    if g:
        return get_global_skillset_path()
    skillset_root = find_skillset_root()
    if skillset_root:
        return skillset_root / "skillset.toml"
    return get_global_skillset_path()


def cmd_apply(*, file: str | None = None, g: bool = False) -> None:
    """Apply skillset.toml — install all declared skills."""
    import tomllib

    file_path = _resolve_toml_path(file, g)

    if not file_path.exists():
        print(f"No skillset.toml found at {abbrev(file_path)}")
        sys.exit(1)

    with open(file_path, "rb") as f:
        config = tomllib.load(f)

    skills_config = config.get("skills")
    if skills_config is None:
        print("No [skills] section found in skillset.toml")
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
    """Process [links] section from skillset.toml."""
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
    """Parse a single skills config entry."""
    if isinstance(value, bool):
        if not value:
            return None, None, None
        return None, False, None
    if isinstance(value, list):
        return value, False, None
    if isinstance(value, dict):
        return value.get("skills"), value.get("copy", False), value.get("path")
    print(f"Invalid entry for {repo!r}")
    sys.exit(1)
