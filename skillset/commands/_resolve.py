"""Source resolution helpers for the add command."""

import sys
from pathlib import Path

from skillset.linking import is_link
from skillset.paths import get_cache_dir
from skillset.repo import (
    clone_or_pull,
    clone_to_temp,
    get_repo_dir,
    parse_github_url,
    parse_repo_spec,
)
from skillset.ui import (
    find_editable_skill,
    fzf_select,
    is_local_path,
    register_local_lib,
)


def _resolve_source(repo, interactive, editable, skills, subpath, no_cache):
    """Resolve the source repo/dir and metadata. Returns a 9-tuple."""
    temp_dir = None
    source_label = None
    toml_key = None
    is_editable = editable
    toml_source = None

    if not repo:
        if not interactive:
            print("Provide a repo (e.g. skillset add owner/repo)")
            sys.exit(1)
        repo = _pick_repo_interactively()
        if not repo:
            return None, None, None, False, None, None, None, None, None

    if is_editable:
        repo_dir, toml_key, toml_source, skills = _resolve_editable(repo, skills)
    elif repo and "://" in repo:
        repo_dir, toml_key, subpath, temp_dir, source_label = _resolve_url(repo, subpath, no_cache)
    elif is_local_path(repo):
        repo_dir = Path(repo).expanduser().resolve()
        if not repo_dir.is_dir():
            print(f"Directory not found: {repo_dir}")
            sys.exit(1)
        if not no_cache:
            register_local_lib(repo_dir)
    else:
        repo_dir, toml_key, temp_dir, source_label = _resolve_spec(repo, no_cache)

    return (
        repo,
        toml_key,
        toml_source,
        is_editable,
        repo_dir,
        temp_dir,
        source_label,
        skills,
        subpath,
    )


def _pick_repo_interactively() -> str | None:
    """Use fzf to pick a cached repo. Returns repo spec or None."""
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
    return selected[0] if selected else None


def _resolve_editable(repo, skills):
    """Resolve an editable source. Returns (repo_dir, toml_key, toml_source, skills)."""
    if is_local_path(repo):
        repo_dir = Path(repo).expanduser().resolve()
        if not repo_dir.is_dir():
            print(f"Directory not found: {repo_dir}")
            sys.exit(1)
        toml_key = repo_dir.name
        toml_source = str(repo_dir).replace("\\", "/")
    else:
        result = find_editable_skill(repo)
        if not result:
            print(f"Skill '{repo}' not found in registered editable sources")
            print("Register a source first: skillset add /path/to/skills -e")
            sys.exit(1)
        repo_dir, toml_key = result
        toml_source = str(repo_dir).replace("\\", "/")
        if not skills:
            skills = [repo]
    return repo_dir, toml_key, toml_source, skills


def _resolve_url(repo, subpath, no_cache):
    """Resolve a GitHub URL. Returns (repo_dir, toml_key, subpath, temp_dir, source_label)."""
    github_info = parse_github_url(repo)
    if not github_info:
        print(f"Invalid GitHub URL: {repo}")
        sys.exit(1)
    owner, repo_name, _branch, url_subpath = github_info
    toml_key = f"{owner}/{repo_name}"
    subpath = subpath or url_subpath
    temp_dir = None
    source_label = None
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
    return repo_dir, toml_key, subpath, temp_dir, source_label


def _resolve_spec(repo, no_cache):
    """Resolve an owner/repo spec. Returns (repo_dir, toml_key, temp_dir, source_label)."""
    try:
        owner, repo_name = parse_repo_spec(repo)
    except ValueError as e:
        print(str(e))
        sys.exit(1)
    toml_key = f"{owner}/{repo_name}"
    temp_dir = None
    source_label = None
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
    return repo_dir, toml_key, temp_dir, source_label
