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
    skills: dict[str, bool] | None = None,
    editable: bool = False,
    source: str | None = None,
) -> bool:
    """Append a repo entry to a skillset.toml file if it exists. Returns True if written."""
    if not toml_path.exists():
        return False

    content = toml_path.read_text()
    if f'"{repo_key}"' in content or f"'{repo_key}'" in content:
        return False

    if editable or path or skills:
        lines = [f'[skills."{repo_key}"]']
        if editable:
            lines.append("editable = true")
        if source:
            lines.append(f'source = "{source}"')
        if path:
            lines.append(f'path = "{path}"')
        if skills:
            for name, enabled in sorted(skills.items()):
                lines.append(f"{name} = {'true' if enabled else 'false'}")
        entry = "\n".join(lines) + "\n"
    else:
        entry = f'"{repo_key}" = true\n'

    toml_path.write_text(content.rstrip() + "\n" + entry)
    return True


def add_to_global_skillset(
    repo_key: str,
    *,
    path: str | None = None,
    skills: dict[str, bool] | None = None,
    editable: bool = False,
    source: str | None = None,
) -> bool:
    """Append a repo entry to ~/.claude/skillset.toml if it exists. Returns True if written."""
    return add_to_skillset(
        get_global_skillset_path(),
        repo_key,
        path=path,
        skills=skills,
        editable=editable,
        source=source,
    )


def update_skillset_skills(
    toml_path: Path,
    repo_key: str,
    new_skills: dict[str, bool],
) -> bool:
    """Add new skill entries to an existing repo entry in a skillset.toml file.

    Supports both inline dict format and sub-table format:
      Inline:    "repo/key" = {zaira = true, ...}
      Sub-table: [skills."repo/key"]
                 zaira = true
    Returns True if the file was modified.
    """
    if not toml_path.exists() or not new_skills:
        return False

    content = toml_path.read_text()
    new_lines = [
        f"{name} = {'true' if enabled else 'false'}"
        for name, enabled in sorted(new_skills.items())
    ]

    # Try sub-table format first: [skills."repo/key"]
    header_pattern = re.compile(
        r'^(\[skills\."' + re.escape(repo_key) + r'"\])\s*$',
        re.MULTILINE,
    )
    header_match = header_pattern.search(content)
    if header_match:
        # Find the end of this section (next header or EOF)
        section_end = len(content)
        next_header = re.search(r'^\[', content[header_match.end():], re.MULTILINE)
        if next_header:
            section_end = header_match.end() + next_header.start()
        insert_at = content[:section_end].rstrip()
        content = insert_at + "\n" + "\n".join(new_lines) + "\n" + content[section_end:]
        toml_path.write_text(content)
        return True

    # Try inline dict format: "repo/key" = {existing content}
    inline_pattern = re.compile(
        r'((?:"' + re.escape(repo_key) + r'"|'
        + "'" + re.escape(repo_key) + r"')\s*=\s*\{)(.*?)(\})",
        re.DOTALL,
    )
    inline_match = inline_pattern.search(content)
    if inline_match:
        new_parts = ", ".join(new_lines)
        prefix = inline_match.group(1)
        existing = inline_match.group(2).rstrip()
        suffix = inline_match.group(3)

        if existing:
            updated = f"{prefix}{existing}, {new_parts}{suffix}"
        else:
            updated = f"{prefix}{new_parts}{suffix}"

        content = content[:inline_match.start()] + updated + content[inline_match.end():]
        toml_path.write_text(content)
        return True

    return False


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
