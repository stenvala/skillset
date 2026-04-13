"""UI helpers — prompts, local path handling."""

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
