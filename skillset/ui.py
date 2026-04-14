"""UI helpers — prompts, local path handling, fzf integration."""

import subprocess
import sys
from pathlib import Path

from skillset.discovery import find_skills
from skillset.linking import create_dir_link, is_link, remove_link
from skillset.paths import get_cache_dir, get_global_skillset_path


def is_local_path(spec: str) -> bool:
    """Check if spec looks like a local path rather than owner/repo."""
    return spec.startswith(("/", ".", "~")) or Path(spec).expanduser().is_dir()


def register_local_lib(repo_dir: Path) -> None:
    """Register a local directory as a symlink under repos/local/ for tracking by update."""
    local_dir = get_cache_dir() / "local"
    local_dir.mkdir(parents=True, exist_ok=True)
    link_path = local_dir / repo_dir.name
    if is_link(link_path):
        remove_link(link_path)
    elif link_path.exists():
        return  # Don't overwrite non-link
    create_dir_link(link_path, repo_dir)


def find_editable_skill(skill_name: str) -> tuple[Path, str] | None:
    """Search registered editable sources in global skillset.toml for a skill by name.

    Returns (source_dir, toml_key) or None.
    """
    import tomllib

    toml_path = get_global_skillset_path()
    if not toml_path.exists():
        return None
    with open(toml_path, "rb") as f:
        config = tomllib.load(f)
    for key, value in config.get("skills", {}).items():
        if not isinstance(value, dict) or not value.get("editable"):
            continue
        source = value.get("source")
        if not source:
            continue
        source_dir = Path(source).expanduser().resolve()
        path_str = value.get("path")
        search_dir = source_dir / path_str if path_str else source_dir
        if not search_dir.is_dir():
            continue
        for skill in find_skills(search_dir):
            if skill.name == skill_name:
                return search_dir, key
    return None


def fzf_select(items: list[str], prompt: str = "Select> ") -> list[str]:
    """Run fzf for multi-select; returns selected items."""
    input_text = "\n".join(items)
    result = subprocess.run(
        ["fzf", "--multi", "--prompt", prompt, "--header", "Tab to select, Enter to confirm"],
        input=input_text,
        stdout=subprocess.PIPE,
        text=True,
    )
    if result.returncode not in (0, 1):
        print("fzf not found or failed", file=sys.stderr)
        sys.exit(1)
    return [line for line in result.stdout.splitlines() if line]


def fzf_select_skills(skills: list[Path], repo_dir: Path, installed: set[str]) -> list[str]:
    """Interactive skill selection with group drill-down. Marks installed skills with *."""
    groups: dict[str, list[str]] = {}
    for skill in skills:
        group = skill.parent.name
        groups.setdefault(group, []).append(skill.name)

    def mark(name: str) -> str:
        return f"* {name}" if name in installed else f"  {name}"

    def unmark(item: str) -> str:
        return item.lstrip("* ").strip()

    def make_items(names: list[str]) -> list[str]:
        return [mark(n) for n in sorted(names)]

    if len(groups) <= 1:
        items = make_items(next(iter(groups.values()))) if groups else []
        selected = fzf_select(items, prompt="Skills> ")
        return [unmark(s) for s in selected]

    # Show default group flat, others as [group] entries
    default = "skills" if "skills" in groups else sorted(groups)[0]
    items = make_items(groups[default]) + sorted(f"[{g}]" for g in groups if g != default)
    selected = fzf_select(items, prompt="Skills> ")

    result = []
    for item in selected:
        if item.startswith("[") and item.endswith("]"):
            group_name = item[1:-1]
            sub = fzf_select(make_items(groups[group_name]), prompt=f"{group_name}> ")
            result.extend(unmark(s) for s in sub)
        else:
            result.append(unmark(item))
    return result


def prompt_skill_selection(available: list[Path]) -> tuple[set[str] | None, dict[str, bool] | None]:
    """Prompt user to add all or select individual skills.

    Returns (filter, selections):
      - (None, None): add all
      - (set, dict): selective — filter has names to install, dict has all y/n choices
    """
    names = sorted(s.name for s in available)
    print(f"\n{len(names)} skill(s) found:")
    for name in names:
        print(f"  {name}")

    choice = input(f"\nAdd all {len(names)} skills? [Y/s(elect)] ").strip().lower()
    if choice in ("s", "select"):
        selected = set()
        selections: dict[str, bool] = {}
        for name in names:
            answer = input(f"  Add {name}? [Y/n] ").strip().lower()
            if answer in ("n", "no"):
                selections[name] = False
            else:
                selected.add(name)
                selections[name] = True
        return selected, selections
    # Default: add all
    return None, None
