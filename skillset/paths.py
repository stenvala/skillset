"""Path helpers and constants for skillset."""

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


def get_global_settings_path() -> Path:
    """Get global Claude settings.local path (user preferences)."""
    return Path.home() / ".claude" / "settings.local.json"


def get_project_settings_path() -> Path | None:
    """Get project-local Claude settings.local path, or None if not in a git repo."""
    root = get_git_root()
    return root / ".claude" / "settings.local.json" if root else None


def get_global_skillset_path() -> Path:
    """Get the path to the global skillset.toml."""
    return Path.home() / ".claude" / "skillset.toml"


def add_to_global_skillset(
    repo_key: str,
    *,
    path: str | None = None,
    skills: dict[str, bool] | None = None,
    editable: bool = False,
    source: str | None = None,
) -> bool:
    """Append a repo entry to ~/.claude/skillset.toml if it exists. Returns True if written."""
    toml_path = get_global_skillset_path()
    if not toml_path.exists():
        return False

    content = toml_path.read_text()
    if f'"{repo_key}"' in content or f"'{repo_key}'" in content:
        return False

    if editable or path or skills:
        parts = []
        if editable:
            parts.append("editable = true")
        if source:
            parts.append(f'source = "{source}"')
        if path:
            parts.append(f'path = "{path}"')
        if skills:
            for name, enabled in sorted(skills.items()):
                parts.append(f"{name} = {'true' if enabled else 'false'}")
        entry = f'"{repo_key}" = {{{", ".join(parts)}}}\n'
    else:
        entry = f'"{repo_key}" = true\n'

    toml_path.write_text(content.rstrip() + "\n" + entry)
    return True


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
