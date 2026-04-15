"""Command handlers for adding and initializing skills."""

import shutil
import sys
from pathlib import Path

from skillset.commands._resolve import _resolve_source
from skillset.commands._templates import (
    GLOBAL_SKILLSET_TEMPLATE,
    LOCAL_SKILLSET_TEMPLATE,
)
from skillset.discovery import find_commands, find_skills
from skillset.linking import is_managed, link_commands, link_skills
from skillset.manifest import record_install
from skillset.paths import (
    abbrev,
    add_to_global_skillset,
    add_to_skillset,
    find_skillset_root,
    get_cache_dir,
    get_global_commands_dir,
    get_global_skills_dir,
    get_global_skillset_path,
    get_local_skillset_path,
)
from skillset.ui import fzf_select, fzf_select_skills, prompt_skill_selection


def cmd_add(
    *,
    repo: str | None = None,
    g: bool = False,
    skills: list[str] | None = None,
    subpath: str | None = None,
    copy: bool = False,
    no_cache: bool = False,
    trial: bool = False,
    interactive: bool = False,
) -> None:
    """Add skills and permissions from a GitHub repo or local directory."""
    skillset_root = None if g else find_skillset_root()
    is_local = skillset_root is not None

    (
        repo,
        toml_key,
        toml_source,
        is_editable,
        repo_dir,
        temp_dir,
        source_label,
        skills,
        subpath,
    ) = _resolve_source(repo, interactive, skills, subpath, no_cache)
    if repo is None:
        return

    source_dir = repo_dir / subpath if subpath else repo_dir
    if subpath and not source_dir.is_dir():
        print(f"Path not found in repo: {subpath}")
        sys.exit(1)

    use_copy = copy or no_cache
    skills_dir = (skillset_root / ".claude" / "skills") if is_local else get_global_skills_dir()

    linked_skills, skill_selections = _link_skills_for_add(
        source_dir, skills_dir, skills, interactive, use_copy, source_label, toml_key
    )

    _print_linked("skill", linked_skills, use_copy, skills_dir)

    commands_dir = (
        (skillset_root / ".claude" / "commands") if is_local else get_global_commands_dir()
    )
    linked_commands = _link_commands_for_add(source_dir, commands_dir, interactive, use_copy)
    _print_linked("command", linked_commands, use_copy, commands_dir)

    if linked_skills or linked_commands:
        _record_install(repo_dir, subpath, use_copy, is_local, trial, skills)

    if toml_key and (linked_skills or linked_commands) and not trial:
        _register_in_toml(
            toml_key,
            subpath,
            skill_selections,
            is_editable,
            toml_source,
            is_local,
            skillset_root,
        )

    if not linked_skills and not linked_commands:
        print("No skills found in repo")

    if temp_dir:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _link_skills_for_add(
    source_dir, skills_dir, skills, interactive, use_copy, source_label, toml_key
):
    """Select and link skills. Returns (linked_skills, skill_selections)."""
    skill_filter = set(skills) if skills else None
    skill_selections = None

    if interactive:
        linked, skill_selections = _link_interactive_skills(
            source_dir, skills_dir, use_copy, source_label
        )
    elif skill_filter is not None:
        available_skills = find_skills(source_dir)
        available_names = {s.name for s in available_skills}
        skill_selections = {name: name in skill_filter for name in available_names}
        linked = link_skills(
            source_dir,
            skills_dir,
            only=skill_filter,
            copy=use_copy,
            source_label=source_label,
        )
    else:
        linked, skill_selections = _link_prompted_skills(
            source_dir, skills_dir, use_copy, source_label, toml_key
        )

    return linked, skill_selections


def _link_interactive_skills(source_dir, skills_dir, use_copy, source_label):
    """Link skills selected via fzf. Returns (linked, selections)."""
    available_skills = find_skills(source_dir)
    if not available_skills:
        return [], None
    installed = (
        {p.name for p in skills_dir.iterdir() if is_managed(p)} if skills_dir.exists() else set()
    )
    selected = set(fzf_select_skills(available_skills, source_dir, installed))
    available_names = {s.name for s in available_skills}
    skill_selections = {name: name in selected for name in available_names}
    linked = link_skills(
        source_dir,
        skills_dir,
        only=selected,
        copy=use_copy,
        source_label=source_label,
    )
    return linked, skill_selections


def _link_prompted_skills(source_dir, skills_dir, use_copy, source_label, toml_key):
    """Link skills selected via interactive prompt. Returns (linked, selections)."""
    available_skills = find_skills(source_dir)
    if not available_skills:
        return [], None
    skill_filter, skill_selections = prompt_skill_selection(available_skills)
    linked = link_skills(
        source_dir,
        skills_dir,
        only=skill_filter,
        copy=use_copy,
        source_label=source_label,
    )
    if skill_selections is None and toml_key:
        skill_selections = {s.name: True for s in available_skills}
    return linked, skill_selections


def _link_commands_for_add(source_dir, commands_dir, interactive, use_copy):
    """Select and link commands. Returns linked command names."""
    if interactive:
        available_commands = find_commands(source_dir)
        if available_commands:
            cmd_names = sorted(c.name for c in available_commands)
            selected_cmds = fzf_select(cmd_names, prompt="Commands> ")
            return link_commands(source_dir, commands_dir, only=set(selected_cmds), copy=use_copy)
        return []
    return link_commands(source_dir, commands_dir, copy=use_copy)


def _print_linked(kind, linked, use_copy, target_dir):
    """Print linked skills/commands summary."""
    if linked:
        verb = "Copied" if use_copy else "Linked"
        print(f"{verb} {len(linked)} {kind}(s) to {abbrev(target_dir)}:")
        for name in sorted(linked):
            print(f"  - {name}")


def _record_install(repo_dir, subpath, use_copy, is_local, trial, skills):
    """Record install options in manifest."""
    try:
        rel = repo_dir.relative_to(get_cache_dir())
        repo_key = str(rel)
    except ValueError:
        repo_key = str(repo_dir)
    if trial:
        trial_value = True
    elif skills:
        trial_value = None
    else:
        trial_value = False
    record_install(
        repo_key,
        subpath=subpath,
        copy=use_copy,
        scope="local" if is_local else "global",
        trial=trial_value,
    )


def _register_in_toml(
    toml_key,
    subpath,
    skill_selections,
    is_editable,
    toml_source,
    is_local,
    skillset_root,
):
    """Register skill in skillset.toml."""
    if is_local:
        local_toml = skillset_root / "skillset.toml"
        written = add_to_skillset(
            local_toml,
            toml_key,
            path=subpath,
            skills=skill_selections,
            editable=is_editable,
            source=toml_source,
        )
        if written:
            print(f"Added to {abbrev(local_toml)}")
    else:
        written = add_to_global_skillset(
            toml_key,
            path=subpath,
            skills=skill_selections,
            editable=is_editable,
            source=toml_source,
        )
        if written:
            print(f"Added to {abbrev(get_global_skillset_path())}")


def cmd_init(*, g: bool = False) -> None:
    """Initialize a skillset.toml file."""
    if g:
        path = get_global_skillset_path()
        template = GLOBAL_SKILLSET_TEMPLATE
    else:
        path = get_local_skillset_path()
        if path is None:
            print("Not in a git repository -- initializing in current directory")
            path = Path.cwd() / "skillset.toml"
        template = LOCAL_SKILLSET_TEMPLATE

    if path.exists():
        print(f"Already exists: {abbrev(path)}")
        sys.exit(1)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(template)
    print(f"Created {abbrev(path)}")
