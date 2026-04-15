"""Path helpers and constants for skillset."""

import re
import subprocess
import sys
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"
CLAUDE_SETTINGS_FILE = ".claude/settings.json"


def get_cache_dir() -> Path:
    """Get the directory where repos are cached."""
    return Path.home() / ".cache" / "skillset" / "repos"


def get_global_skills_dir() -> Path:
    """Get global Claude skills directory."""
    return Path.home() / ".claude" / "skills"


def get_git_root() -> Path | None:
    """Get the root of the current git repository, or None if not in one."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_project_skills_dir() -> Path | None:
    """Get project-local Claude skills directory, or None if not in a git repo."""
    root = get_git_root()
    return root / ".claude" / "skills" if root else None


def get_global_commands_dir() -> Path:
    """Get global Claude commands directory."""
    return Path.home() / ".claude" / "commands"


def get_project_commands_dir() -> Path | None:
    """Get project-local Claude commands directory, or None if not in a git repo."""
    root = get_git_root()
    return root / ".claude" / "commands" if root else None


def get_global_skillset_path() -> Path:
    """Get the path to the global skillset.toml."""
    return Path.home() / ".claude" / "skillset.toml"


def get_local_skillset_path() -> Path | None:
    """Get the path to the local skillset.toml at the repo root, or None if not in a git repo."""
    root = get_git_root()
    return root / "skillset.toml" if root else None


def find_skillset_root() -> Path | None:
    """Walk up from CWD looking for skillset.toml. Return its parent dir, or None."""
    current = Path.cwd()
    while True:
        if (current / "skillset.toml").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def add_to_skillset(
    toml_path: Path,
    repo_key: str,
    *,
    path: str | None = None,
    enabled: list[str] | None = None,
    disabled: list[str] | None = None,
    editable: bool = False,
    source: str | None = None,
) -> bool:
    """Append a [skills."repo"] sub-table to a skillset.toml file. Returns True if written.

    Skill selection is expressed as two lists:
      enabled = ["skill-a", "skill-b"]   # or ["*"] for all
      disabled = ["skill-c"]              # explicit opt-outs (skipped by sync)
    """
    if not toml_path.exists():
        return False

    content = toml_path.read_text()
    if f'"{repo_key}"' in content or f"'{repo_key}'" in content:
        return False

    lines = [f'[skills."{repo_key}"]']
    if editable:
        lines.append("editable = true")
    if source:
        lines.append(f'source = "{source}"')
    if path:
        lines.append(f'path = "{path}"')
    if enabled is not None:
        lines.append(_format_str_list("enabled", enabled))
    if disabled:
        lines.append(_format_str_list("disabled", disabled))
    entry = "\n".join(lines) + "\n"

    toml_path.write_text(content.rstrip() + "\n" + entry)
    return True


def add_to_global_skillset(
    repo_key: str,
    *,
    path: str | None = None,
    enabled: list[str] | None = None,
    disabled: list[str] | None = None,
    editable: bool = False,
    source: str | None = None,
) -> bool:
    """Append a repo entry to ~/.claude/skillset.toml if it exists. Returns True if written."""
    return add_to_skillset(
        get_global_skillset_path(),
        repo_key,
        path=path,
        enabled=enabled,
        disabled=disabled,
        editable=editable,
        source=source,
    )


def _format_str_list(key: str, items: list[str]) -> str:
    """Format a string list as a TOML array assignment."""
    if not items:
        return f"{key} = []"
    body = ", ".join(f'"{s}"' for s in items)
    return f"{key} = [{body}]"


def update_skillset_skills(
    toml_path: Path,
    repo_key: str,
    *,
    add_enabled: list[str] | None = None,
    add_disabled: list[str] | None = None,
) -> bool:
    """Fold skill names into the enabled/disabled arrays of an existing sub-table.

    Move semantics: names added to `enabled` are removed from `disabled` and
    vice versa, so a skill is never listed in both. Dedupes within a list.
    Returns True if the file was modified.
    """
    add_enabled = add_enabled or []
    add_disabled = add_disabled or []
    if not toml_path.exists() or not (add_enabled or add_disabled):
        return False

    content = toml_path.read_text()
    header_pattern = re.compile(
        r'^\[skills\."' + re.escape(repo_key) + r'"\]\s*$',
        re.MULTILINE,
    )
    header_match = header_pattern.search(content)
    if not header_match:
        return False

    section_start = header_match.end()
    next_header = re.search(r"^\[", content[section_start:], re.MULTILINE)
    section_end = section_start + next_header.start() if next_header else len(content)
    section = content[section_start:section_end]

    new_section = section
    new_section, a = _rewrite_list(new_section, "enabled", lambda xs: _add_unique(xs, add_enabled))
    new_section, b = _rewrite_list(new_section, "disabled", lambda xs: _remove(xs, add_enabled))
    new_section, c = _rewrite_list(
        new_section, "disabled", lambda xs: _add_unique(xs, add_disabled)
    )
    new_section, d = _rewrite_list(new_section, "enabled", lambda xs: _remove(xs, add_disabled))
    if not (a or b or c or d):
        return False

    toml_path.write_text(content[:section_start] + new_section + content[section_end:])
    return True


def _parse_list_body(body: str) -> list[str]:
    """Extract double-quoted names from a TOML array body."""
    return re.findall(r'"([^"]*)"', body)


def _add_unique(existing: list[str], additions: list[str]) -> list[str]:
    """Append items not already in existing. Preserves order."""
    out = list(existing)
    for name in additions:
        if name not in out:
            out.append(name)
    return out


def _remove(existing: list[str], removals: list[str]) -> list[str]:
    """Remove items from existing."""
    if not removals:
        return existing
    drop = set(removals)
    return [n for n in existing if n not in drop]


def _rewrite_list(section: str, key: str, mutate) -> tuple[str, bool]:
    """Find `key = [...]` in section and apply `mutate(names) -> names`.

    Returns (section, changed). If the key is missing and mutate returns a
    non-empty list, the assignment is appended to the section.
    """
    pattern = re.compile(rf"^{key}\s*=\s*\[([^\]]*)\]\s*$", re.MULTILINE)
    match = pattern.search(section)
    if match:
        current = _parse_list_body(match.group(1))
        updated = mutate(current)
        if updated == current:
            return section, False
        replacement = _format_str_list(key, updated)
        return section[: match.start()] + replacement + section[match.end() :], True
    updated = mutate([])
    if not updated:
        return section, False
    trailing_ws = len(section) - len(section.rstrip("\n"))
    body = section.rstrip("\n")
    suffix = "\n" * max(trailing_ws, 1)
    return f"{body}\n{_format_str_list(key, updated)}{suffix}", True


def require_project_dir(path: Path | None, kind: str = "project") -> Path:
    """Return path if set, or exit with error if not in a git repo."""
    if path is None:
        print(f"Not in a git repository — cannot use {kind} scope")
        sys.exit(1)
    return path


def abbrev(path: str | Path) -> str:
    """Replace home directory with ~ in a path string."""
    s = str(path)
    home = str(Path.home())
    return s.replace(home, "~", 1) if s.startswith(home) else s
