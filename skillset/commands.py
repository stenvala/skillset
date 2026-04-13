"""Command handlers — all cmd_* functions dispatched from main()."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from skillset.discovery import find_commands, find_skills
from skillset.linking import (
    get_copy_source,
    is_link,
    is_managed,
    is_managed_copy,
    link_commands,
    link_skills,
    remove_link,
    remove_managed,
)
from skillset.manifest import (
    get_install_options,
    load_manifest,
    record_install,
    save_manifest,
)
from skillset.paths import (
    abbrev,
    add_to_global_skillset,
    get_cache_dir,
    get_git_root,
    get_global_commands_dir,
    get_global_settings_path,
    get_global_skills_dir,
    get_global_skillset_path,
    get_project_commands_dir,
    get_project_settings_path,
    get_project_skills_dir,
    require_project_dir,
)
from skillset.repo import (
    clone_or_pull,
    clone_to_temp,
    get_repo_dir,
    parse_github_url,
    parse_repo_spec,
)
from skillset.settings import (
    add_read_permission,
    deep_merge,
    get_preset,
    load_settings,
    merge_permissions,
    save_settings,
)
from skillset.ui import (
    find_editable_skill,
    fzf_select,
    fzf_select_skills,
    is_local_path,
    prompt_skill_selection,
    register_local_lib,
)

GLOBAL_SKILLSET_TEMPLATE = """\
# Global skillset configuration (~/.claude/skillset.toml)
# Skills are installed to ~/.claude/skills/
#
# Examples:
#   "owner/repo" = true                                        # all skills from repo
#   "owner/repo" = {skill-a = true, skill-b = false}           # selective per skill
#   "owner/repo" = {path = "subdir"}                           # skills from subdirectory
#   "owner/repo" = {path = "sub", editable = true, source = "~/local/checkout"}
#
# Run 'skillset sync' to install/update skills.

[skills]
"""

_SYNC_META_KEYS = {"editable", "path", "source", "copy"}


def cmd_list(args: argparse.Namespace) -> None:
    """List installed skills and commands."""
    prune = getattr(args, "prune", False)
    global_skills_dir = get_global_skills_dir()
    project_skills_dir = get_project_skills_dir()
    global_commands_dir = get_global_commands_dir()
    project_commands_dir = get_project_commands_dir()

    global_skills = sorted(global_skills_dir.iterdir()) if global_skills_dir.exists() else []
    if project_skills_dir and project_skills_dir.exists():
        project_skills = sorted(project_skills_dir.iterdir())
    else:
        project_skills = []
    global_commands = sorted(global_commands_dir.iterdir()) if global_commands_dir.exists() else []
    if project_commands_dir and project_commands_dir.exists():
        project_commands = sorted(project_commands_dir.iterdir())
    else:
        project_commands = []

    # Build set of trial repo keys for tagging
    manifest = load_manifest()
    trial_repos = {k for k, v in manifest.items() if v.get("trial")}

    def _is_trial_skill(item: Path) -> bool:
        """Check if a skill belongs to a trial repo."""
        if is_managed_copy(item):
            source = get_copy_source(item) or ""
        elif is_link(item):
            resolved = item.resolve()
            source = str(resolved.parent)
        else:
            return False
        # Match against trial repo keys (which may be owner/repo or absolute paths)
        for key in trial_repos:
            if key in source or abbrev(key) in abbrev(source):
                return True
        return False

    def print_grouped(items: list[Path], is_link_fn, label: str, install_dir: Path) -> None:
        if not items:
            return
        print(f"{label} ({abbrev(install_dir)}):")
        groups: dict[str, list[str]] = {}
        broken: list[Path] = []
        for item in items:
            if is_link_fn(item):
                if is_managed_copy(item):
                    source = get_copy_source(item)
                    target_dir = abbrev(source) if source else "(copied)"
                else:
                    resolved = item.resolve()
                    if not resolved.exists():
                        broken.append(item)
                        continue
                    target_dir = abbrev(resolved.parent)
            else:
                target_dir = "(manual)"
            trial_tag = " (trial)" if _is_trial_skill(item) else ""
            groups.setdefault(target_dir, []).append(item.name + trial_tag)
        for target_dir, names in sorted(groups.items()):
            print(f"  {target_dir}:")
            for name in sorted(names):
                print(f"    {name}")
        for item in broken:
            if prune:
                remove_link(item)
                print(f"  [pruned broken link: {item.name}]")
            else:
                print(f"  [broken link: {item.name}]")

    print_grouped(global_skills, is_managed, "Global skills", global_skills_dir)
    if project_skills_dir:
        print_grouped(project_skills, is_managed, "Project skills", project_skills_dir)
    print_grouped(global_commands, lambda p: p.is_symlink(), "Global commands", global_commands_dir)
    if project_commands_dir:
        print_grouped(
            project_commands, lambda p: p.is_symlink(), "Project commands", project_commands_dir
        )

    # List registered repos
    cache_dir = get_cache_dir()
    repos = []
    if cache_dir.exists():
        for owner_dir in sorted(cache_dir.iterdir()):
            if owner_dir.is_dir():
                for repo_dir in sorted(owner_dir.iterdir()):
                    if repo_dir.is_dir():
                        repos.append(f"{owner_dir.name}/{repo_dir.name}")
    if repos:
        print(f"Repos ({abbrev(cache_dir)}):")
        for repo in repos:
            repo_path = cache_dir / repo.replace("/", os.sep)
            if is_link(repo_path):
                print(f"  {repo} -> {abbrev(repo_path.resolve())}")
            else:
                print(f"  {repo}")

    if (
        not global_skills
        and not project_skills
        and not global_commands
        and not project_commands
        and not repos
    ):
        print("No skills, commands, or repos found")


def cmd_allow(args: argparse.Namespace) -> None:
    """Apply permission presets."""
    settings_path = require_project_dir(get_project_settings_path(), "project settings")
    presets = args.presets or ["developer"]

    existing = load_settings(settings_path)
    total_perms = 0
    applied = []
    for name in presets:
        preset = get_preset(name)
        if not preset:
            print(f"Unknown preset '{name}'")
            sys.exit(1)
        existing = deep_merge(existing, preset)
        total_perms += len(preset.get("permissions", {}).get("allow", []))
        applied.append(name)
    save_settings(settings_path, existing)
    print(f"Applied {', '.join(applied)} ({total_perms} permissions) to {abbrev(settings_path)}")


def cmd_add(args: argparse.Namespace) -> None:
    """Add skills and permissions from a GitHub repo or local directory."""
    if args.local and get_git_root() is None:
        print("Not in a git repository — cannot use --local")
        sys.exit(1)
    if not args.repo:
        if not args.interactive:
            print("Provide a repo or use -i for interactive selection")
            sys.exit(1)
        cache_dir = get_cache_dir()
        repos = []
        if cache_dir.exists():
            for owner_dir in sorted(cache_dir.iterdir()):
                if owner_dir.is_dir():
                    for repo_dir in sorted(owner_dir.iterdir()):
                        if repo_dir.is_dir():
                            repos.append(f"{owner_dir.name}/{repo_dir.name}")
        if not repos:
            print("No repos cached. Run 'skillset add owner/repo' first.")
            sys.exit(1)
        selected = fzf_select(repos, prompt="Repo> ")
        if not selected:
            return
        args.repo = selected[0]

    subpath = getattr(args, "subpath", None)
    no_cache = getattr(args, "no_cache", False)
    temp_dir = None  # track temp clone for cleanup
    source_label = None  # human-readable origin for --no-cache copies
    toml_key = None  # normalized key for global skillset.toml
    is_editable = getattr(args, "editable", False)
    toml_source = None  # local path for editable toml entries

    if is_editable:
        if is_local_path(args.repo):
            # Path given directly — register as editable source
            repo_dir = Path(args.repo).expanduser().resolve()
            if not repo_dir.is_dir():
                print(f"Directory not found: {repo_dir}")
                sys.exit(1)
            toml_key = repo_dir.name
            toml_source = str(repo_dir).replace("\\", "/")
        else:
            # Skill name — look up in registered editable sources
            result = find_editable_skill(args.repo)
            if not result:
                print(f"Skill '{args.repo}' not found in registered editable sources")
                print("Register a source first: skillset add /path/to/skills -e")
                sys.exit(1)
            repo_dir, toml_key = result
            toml_source = str(repo_dir).replace("\\", "/")
            if not args.skills:
                args.skills = [args.repo]
    elif args.repo and "://" in args.repo:
        github_info = parse_github_url(args.repo)
        if not github_info:
            print(f"Invalid GitHub URL: {args.repo}")
            sys.exit(1)
        owner, repo_name, _branch, url_subpath = github_info
        toml_key = f"{owner}/{repo_name}"
        subpath = subpath or url_subpath
        if no_cache:
            repo_dir = clone_to_temp(owner, repo_name)
            temp_dir = repo_dir.parent
            source_label = f"{owner}/{repo_name}"
        else:
            repo_dir = get_repo_dir(owner, repo_name)
            if is_link(repo_dir):
                repo_dir = repo_dir.resolve()
            else:
                repo_dir = clone_or_pull(owner, repo_name)
    elif is_local_path(args.repo):
        repo_dir = Path(args.repo).expanduser().resolve()
        if not repo_dir.is_dir():
            print(f"Directory not found: {repo_dir}")
            sys.exit(1)
        if not no_cache:
            register_local_lib(repo_dir)
    else:
        try:
            owner, repo_name = parse_repo_spec(args.repo)
        except ValueError as e:
            print(str(e))
            sys.exit(1)
        toml_key = f"{owner}/{repo_name}"
        if no_cache:
            repo_dir = clone_to_temp(owner, repo_name)
            temp_dir = repo_dir.parent
            source_label = f"{owner}/{repo_name}"
        else:
            repo_dir = get_repo_dir(owner, repo_name)
            if is_link(repo_dir):
                repo_dir = repo_dir.resolve()
            else:
                repo_dir = clone_or_pull(owner, repo_name)

    source_dir = repo_dir / subpath if subpath else repo_dir
    if subpath and not source_dir.is_dir():
        print(f"Path not found in repo: {subpath}")
        sys.exit(1)

    # Link skills (global or project)
    use_copy = getattr(args, "copy", False) or no_cache
    skills_dir = get_project_skills_dir() if args.local else get_global_skills_dir()
    skill_filter = set(args.skills) if getattr(args, "skills", None) else None
    skill_selections = None  # tracks y/n per skill for toml
    if args.interactive:
        available_skills = find_skills(source_dir)
        if available_skills:
            installed = (
                {p.name for p in skills_dir.iterdir() if is_managed(p)}
                if skills_dir.exists()
                else set()
            )
            selected = fzf_select_skills(available_skills, source_dir, installed)
            linked_skills = link_skills(
                source_dir, skills_dir, only=set(selected), copy=use_copy, source_label=source_label
            )
        else:
            linked_skills = []
    elif skill_filter is not None:
        linked_skills = link_skills(
            source_dir, skills_dir, only=skill_filter, copy=use_copy, source_label=source_label
        )
    else:
        # No -i, no -s: prompt user to add all or select
        available_skills = find_skills(source_dir)
        if available_skills:
            skill_filter, skill_selections = prompt_skill_selection(available_skills)
            linked_skills = link_skills(
                source_dir, skills_dir, only=skill_filter, copy=use_copy, source_label=source_label
            )
        else:
            linked_skills = []

    if linked_skills:
        verb = "Copied" if use_copy else "Linked"
        print(f"{verb} {len(linked_skills)} skill(s) to {abbrev(skills_dir)}:")
        for skill_name in sorted(linked_skills):
            print(f"  - {skill_name}")

    # Link commands (global or project)
    commands_dir = get_project_commands_dir() if args.local else get_global_commands_dir()
    if args.interactive:
        available_commands = find_commands(source_dir)
        if available_commands:
            selected = fzf_select(sorted(c.name for c in available_commands), prompt="Commands> ")
            linked_commands = link_commands(
                source_dir, commands_dir, only=set(selected), copy=use_copy
            )
        else:
            linked_commands = []
    else:
        linked_commands = link_commands(source_dir, commands_dir, copy=use_copy)

    if linked_commands:
        verb = "Copied" if use_copy else "Linked"
        print(f"{verb} {len(linked_commands)} command(s) to {abbrev(commands_dir)}:")
        for cmd_name in sorted(linked_commands):
            print(f"  - {cmd_name}")

    # Add read permission for source directory if we linked anything
    if linked_skills or linked_commands:
        settings_path = get_project_settings_path() if args.local else get_global_settings_path()
        add_read_permission(settings_path, repo_dir)
        print(f"Added Read permission for {abbrev(repo_dir)}")

    # Merge permissions (project if in a git repo)
    settings_path = get_project_settings_path()
    if settings_path:
        merged_keys = merge_permissions(repo_dir, settings_path)
    else:
        merged_keys = []

    if merged_keys:
        print(f"Merged permissions into {abbrev(settings_path)}:")
        for key in sorted(merged_keys):
            print(f"  - {key}")

    # Record install options for update
    if linked_skills or linked_commands:
        # Derive a repo key from the repo_dir relative to cache, or use abs path for local
        try:
            rel = repo_dir.relative_to(get_cache_dir())
            repo_key = str(rel)
        except ValueError:
            repo_key = str(repo_dir)
        is_trial = getattr(args, "trial", False)
        # --try sets trial; no --try with -s preserves existing; no --try without -s clears trial
        if is_trial:
            trial_value = True
        elif getattr(args, "skills", None):
            trial_value = None  # adding specific skills — don't change trial status
        else:
            trial_value = False  # full re-add — promote to permanent
        record_install(
            repo_key,
            subpath=subpath,
            copy=use_copy,
            scope="local" if args.local else "global",
            trial=trial_value,
        )

    # Register in global skillset.toml (if exists, not local, not trial)
    if (
        toml_key
        and (linked_skills or linked_commands)
        and not args.local
        and not getattr(args, "trial", False)
    ):
        written = add_to_global_skillset(
            toml_key,
            path=subpath,
            skills=skill_selections,
            editable=is_editable,
            source=toml_source,
        )
        if written:
            print(f"Added to {abbrev(get_global_skillset_path())}")

    if not linked_skills and not linked_commands and not merged_keys:
        print("No skills or permissions found in repo")

    # Clean up temp clone
    if temp_dir:
        shutil.rmtree(temp_dir, ignore_errors=True)


def cmd_remove(args: argparse.Namespace) -> None:
    """Remove a skill by name, or interactively select skills to remove."""
    if args.local and get_git_root() is None:
        print("Not in a git repository — cannot use --local")
        sys.exit(1)
    skills_dir = (
        require_project_dir(get_project_skills_dir()) if args.local else get_global_skills_dir()
    )

    if args.interactive:
        import fnmatch

        installed = (
            sorted(p.name for p in skills_dir.iterdir() if is_managed(p))
            if skills_dir.exists()
            else []
        )
        if not installed:
            print(f"No managed skills in {abbrev(skills_dir)}")
            return
        scope = "project" if args.local else "global"
        selected = fzf_select(installed, prompt=f"Remove {scope} skills> ")
        for name in selected:
            remove_managed(skills_dir / name)
            print(f"Removed {name} from {abbrev(skills_dir)}")
        return

    if not args.name:
        print("Provide a skill name or use -i for interactive selection")
        sys.exit(1)

    # Glob pattern support (e.g. "bs-*")
    import fnmatch

    if any(c in args.name for c in "*?["):
        if not skills_dir.exists():
            print(f"No skills in {abbrev(skills_dir)}")
            sys.exit(1)
        matched = sorted(
            p.name
            for p in skills_dir.iterdir()
            if fnmatch.fnmatch(p.name, args.name) and is_managed(p)
        )
        if not matched:
            print(f"No managed skills matching '{args.name}' in {abbrev(skills_dir)}")
            sys.exit(1)
        for name in matched:
            remove_managed(skills_dir / name)
            print(f"Removed {name} from {abbrev(skills_dir)}")
        return

    skill_path = skills_dir / args.name

    if not skill_path.exists():
        print(f"Skill '{args.name}' not found in {abbrev(skills_dir)}")
        sys.exit(1)

    if is_managed(skill_path):
        remove_managed(skill_path)
        print(f"Removed {args.name} from {abbrev(skills_dir)}")
    else:
        print(f"'{args.name}' is not managed by skillset - remove manually if intended")
        sys.exit(1)


def _resolve_update_options(
    repo_key: str, args: argparse.Namespace
) -> tuple[str | None, bool, str]:
    """Resolve subpath/copy/scope from manifest, with CLI flags as overrides."""
    opts = get_install_options(repo_key) or {}
    use_copy = getattr(args, "copy", False) or opts.get("copy", False)
    subpath = opts.get("subpath")
    scope = opts.get("scope", "global")
    # CLI --global flag overrides saved scope
    if getattr(args, "g", False):
        scope = "global"
    return subpath, use_copy, scope


def cmd_update(args: argparse.Namespace) -> None:
    """Update repo(s) and refresh links (or copies) and permissions."""
    cache_dir = get_cache_dir()
    existing_only = not getattr(args, "new", False)

    if args.repo:
        try:
            owner, repo_name = parse_repo_spec(args.repo)
        except ValueError as e:
            print(str(e))
            sys.exit(1)

        repo_dir = get_repo_dir(owner, repo_name)
        if not repo_dir.exists():
            print(f"Repo {args.repo} not installed. Use 'skillset add {args.repo}' first.")
            sys.exit(1)

        if not is_link(repo_dir):
            clone_or_pull(owner, repo_name)

        repo_key = f"{owner}/{repo_name}"
        subpath, use_copy, scope = _resolve_update_options(repo_key, args)
        target_dir = repo_dir / subpath if subpath else repo_dir

        skills_dir = (
            get_global_skills_dir()
            if scope == "global"
            else require_project_dir(get_project_skills_dir())
        )
        linked_skills = link_skills(
            target_dir, skills_dir, copy=use_copy, existing_only=existing_only
        )

        commands_dir = (
            get_global_commands_dir()
            if scope == "global"
            else require_project_dir(get_project_commands_dir())
        )
        linked_commands = link_commands(
            target_dir, commands_dir, copy=use_copy, existing_only=existing_only
        )

        print(f"Updated {len(linked_skills)} skill(s), {len(linked_commands)} command(s)")
    else:
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
                    resolved_dir = repo_dir.resolve() if is_link(repo_dir) else repo_dir
                    repo_key = f"{owner_dir.name}/{repo_dir.name}"
                    subpath, use_copy, scope = _resolve_update_options(repo_key, args)
                    source_dir = resolved_dir / subpath if subpath else resolved_dir

                    if scope == "local" and get_git_root() is None:
                        print(f"  Skipping {repo_key} (local scope, not in a git repo)")
                        continue
                    skills_dir = (
                        get_global_skills_dir()
                        if scope == "global"
                        else require_project_dir(get_project_skills_dir())
                    )
                    commands_dir = (
                        get_global_commands_dir()
                        if scope == "global"
                        else require_project_dir(get_project_commands_dir())
                    )
                    total_skills += len(
                        link_skills(
                            source_dir, skills_dir, copy=use_copy, existing_only=existing_only
                        )
                    )
                    total_commands += len(
                        link_commands(
                            source_dir, commands_dir, copy=use_copy, existing_only=existing_only
                        )
                    )

        if total_skills == 0 and total_commands == 0:
            print("No repos installed")
        else:
            print(f"Updated ({total_skills} skill(s), {total_commands} command(s))")


def cmd_apply(args: argparse.Namespace) -> None:
    """Apply skills.toml — install all declared skills."""
    import tomllib

    file_path = Path(getattr(args, "file", None) or "skillset.toml")
    if not file_path.exists():
        print(f"No skillset.toml found at {file_path}")
        sys.exit(1)

    with open(file_path, "rb") as f:
        config = tomllib.load(f)

    skills_config = config.get("skills")
    if skills_config is None:
        print("No [skills] section found in skillset.toml")
        sys.exit(1)

    links_config = config.get("links", {})
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

    for repo, value in skills_config.items():
        if isinstance(value, bool):
            if not value:
                continue  # false = disabled
            entry_skills, entry_local, entry_copy, entry_subpath = None, False, False, None
        elif isinstance(value, list):
            entry_skills, entry_local, entry_copy, entry_subpath = value, False, False, None
        elif isinstance(value, dict):
            entry_skills = value.get("skills")
            entry_local = value.get("local", False)
            entry_copy = value.get("copy", False)
            entry_subpath = value.get("path")
        else:
            print(f"Invalid entry for {repo!r}")
            sys.exit(1)

        print(f"\nAdding {repo}...")
        cmd_add(
            argparse.Namespace(
                repo=repo,
                local=entry_local,
                skills=entry_skills,
                subpath=entry_subpath,
                copy=entry_copy,
                no_cache=False,
                trial=False,
                interactive=False,
            )
        )


def cmd_clean(args: argparse.Namespace) -> None:
    """Remove all trial skills."""
    manifest = load_manifest()
    trial_repos = {k: v for k, v in manifest.items() if v.get("trial")}

    if not trial_repos:
        print("No trial skills to clean")
        return

    removed = 0
    for repo_key, opts in trial_repos.items():
        scope = opts.get("scope", "global")
        if scope == "local":
            skills_dir = get_project_skills_dir()
            if skills_dir is None:
                print(f"  Skipping {repo_key} (local scope, not in a git repo)")
                continue
        else:
            skills_dir = get_global_skills_dir()

        if skills_dir.exists():
            for item in sorted(skills_dir.iterdir()):
                if not is_managed(item):
                    continue
                # Check if this skill points back to the trial repo
                if is_managed_copy(item):
                    source = get_copy_source(item) or ""
                elif is_link(item):
                    source = str(item.resolve())
                else:
                    continue
                if repo_key in source or abbrev(repo_key) in abbrev(source):
                    remove_managed(item)
                    print(f"  Removed {item.name}")
                    removed += 1

        # Remove from manifest
        del manifest[repo_key]

        # Remove cached repo if no other manifest entries reference it
        remaining_keys = set(manifest.keys())
        # repo_key is like "owner/repo" or an absolute path
        repo_dir = get_cache_dir() / repo_key.replace("/", os.sep)
        if repo_dir.exists() and not any(k.startswith(repo_key) for k in remaining_keys):
            if is_link(repo_dir):
                remove_link(repo_dir)
            else:
                shutil.rmtree(repo_dir)
            # Clean up empty parent dirs
            parent = repo_dir.parent
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
            print(f"  Removed cached repo {repo_key}")

    save_manifest(manifest)
    print(f"Cleaned {removed} trial skill(s) from {len(trial_repos)} repo(s)")


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize a skillset.toml file."""
    if args.scope != "global":
        print(f"Unknown scope '{args.scope}'. Only 'global' is supported.")
        sys.exit(1)

    path = get_global_skillset_path()
    if path.exists():
        print(f"Already exists: {abbrev(path)}")
        sys.exit(1)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(GLOBAL_SKILLSET_TEMPLATE)
    print(f"Created {abbrev(path)}")


def cmd_sync(args: argparse.Namespace) -> None:
    """Sync skills from global skillset.toml — pull repos, link skills, report new."""
    import tomllib

    file_path = Path(args.file) if getattr(args, "file", None) else get_global_skillset_path()

    if not file_path.exists():
        print(f"No skillset.toml at {abbrev(file_path)}")
        print("Run 'skillset init global' to create one.")
        sys.exit(1)

    with open(file_path, "rb") as f:
        config = tomllib.load(f)

    skills_config = config.get("skills", {})
    if not skills_config:
        print("No [skills] entries in skillset.toml")
        return

    skills_dir = get_global_skills_dir()
    commands_dir = get_global_commands_dir()
    settings_path = get_global_settings_path()
    total_linked = 0
    new_skills_found: dict[str, list[str]] = {}

    for repo_key, value in skills_config.items():
        if isinstance(value, bool):
            if not value:
                continue
            # All skills from github repo
            print(f"\nSyncing {repo_key}...")
            try:
                owner, repo_name = parse_repo_spec(repo_key)
            except ValueError as e:
                print(f"  {e}")
                continue
            repo_dir = clone_or_pull(owner, repo_name)
            linked = link_skills(repo_dir, skills_dir)
            link_commands(repo_dir, commands_dir)
            if linked:
                add_read_permission(settings_path, repo_dir)
                merge_permissions(repo_dir, settings_path)
                record_install(f"{owner}/{repo_name}", scope="global")
            total_linked += len(linked)
            for name in sorted(linked):
                print(f"  + {name}")

        elif isinstance(value, dict):
            editable = value.get("editable", False)
            path_str = value.get("path")
            source_str = value.get("source")
            use_copy = value.get("copy", False)
            skill_entries = {k: v for k, v in value.items() if k not in _SYNC_META_KEYS}

            # Resolve source directory
            if editable:
                if not source_str:
                    print(f"\n{repo_key}: editable requires 'source' path")
                    continue
                print(f"\nSyncing {repo_key} (editable)...")
                base_dir = Path(source_str).expanduser().resolve()
                if not base_dir.is_dir():
                    print(f"  Source not found: {source_str}")
                    continue
                source_dir = base_dir / path_str if path_str else base_dir
                if path_str and not source_dir.is_dir():
                    print(f"  Path not found: {path_str} in {source_str}")
                    continue
                register_local_lib(base_dir)
                repo_dir = base_dir
            else:
                print(f"\nSyncing {repo_key}...")
                try:
                    owner, repo_name = parse_repo_spec(repo_key)
                except ValueError as e:
                    print(f"  {e}")
                    continue
                repo_dir = clone_or_pull(owner, repo_name)
                source_dir = repo_dir / path_str if path_str else repo_dir
                if path_str and not source_dir.is_dir():
                    print(f"  Path not found in repo: {path_str}")
                    continue

            available = find_skills(source_dir)
            available_names = {s.name for s in available}

            if skill_entries:
                # Selective mode — only link true, remove false, report unknown
                enabled = {k for k, v in skill_entries.items() if v is True}
                disabled = {k for k, v in skill_entries.items() if v is False}
                tracked = enabled | disabled
                new = available_names - tracked

                if new:
                    new_skills_found[repo_key] = sorted(new)

                if enabled:
                    linked = link_skills(source_dir, skills_dir, only=enabled, copy=use_copy)
                    total_linked += len(linked)
                    for name in sorted(linked):
                        print(f"  + {name}")

                # Remove excluded skills that are currently linked
                for skill_name in disabled:
                    skill_path = skills_dir / skill_name
                    if skill_path.exists() and is_managed(skill_path):
                        remove_managed(skill_path)
                        print(f"  - {skill_name} (excluded)")
            else:
                # All skills
                linked = link_skills(source_dir, skills_dir, copy=use_copy)
                link_commands(source_dir, commands_dir, copy=use_copy)
                total_linked += len(linked)
                for name in sorted(linked):
                    print(f"  + {name}")

            # Permissions and tracking
            add_read_permission(settings_path, source_dir)
            if not editable:
                merge_permissions(repo_dir, settings_path)
                record_install(
                    f"{owner}/{repo_name}", subpath=path_str, copy=use_copy, scope="global"
                )

        else:
            print(f"\nSkipping {repo_key}: invalid value type")

    # Report new untracked skills
    if new_skills_found:
        print("\n--- New skills detected ---")
        for repo_key, names in new_skills_found.items():
            print(f"{repo_key}:")
            for name in names:
                print(f"  {name}")
        print("Add true/false for these in your skillset.toml")

    print(f"\nSync complete ({total_linked} skill(s) linked)")
