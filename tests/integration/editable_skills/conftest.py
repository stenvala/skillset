"""Shared fixtures for editable skill integration tests."""

import re
from pathlib import Path
from unittest.mock import patch  # noqa: F401

import pytest

from skillset.commands import cmd_add, cmd_sync  # noqa: F401

FIXTURES = Path(__file__).parent / "fixtures"
ALL_SKILLS = {"alpha", "beta", "gamma"}


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Isolated environment with global scope (no local skillset.toml)."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()

    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    monkeypatch.setattr("skillset.paths.get_git_root", lambda: project)
    for mod in (
        "skillset.commands.add",
        "skillset.commands.update",
        "skillset.commands.remove",
        "skillset.commands.list",
    ):
        monkeypatch.setattr(f"{mod}.find_skillset_root", lambda: None)

    (home / ".claude").mkdir(parents=True)
    (home / ".cache" / "skillset" / "repos").mkdir(parents=True)

    return type("Env", (), {"home": home, "project": project, "tmp": tmp_path})()


@pytest.fixture
def local_env(tmp_path, monkeypatch):
    """Isolated environment with a local skillset.toml (project scope)."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()

    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    monkeypatch.setattr("skillset.paths.get_git_root", lambda: project)
    for mod in (
        "skillset.commands.add",
        "skillset.commands.update",
        "skillset.commands.remove",
        "skillset.commands.list",
    ):
        monkeypatch.setattr(f"{mod}.find_skillset_root", lambda: project)

    (home / ".claude").mkdir(parents=True)
    (home / ".cache" / "skillset" / "repos").mkdir(parents=True)

    toml_path = project / "skillset.toml"
    toml_path.write_text("[skills]\n")

    return type(
        "Env",
        (),
        {
            "home": home,
            "project": project,
            "tmp": tmp_path,
            "toml_path": toml_path,
            "skills_dir": project / ".claude" / "skills",
        },
    )()


def installed_skills(skills_dir: Path) -> set[str]:
    if not skills_dir.exists():
        return set()
    return {p.name for p in skills_dir.iterdir() if p.is_dir()}


def remove_skill_from_toml(toml_path: Path, skill_name: str) -> None:
    """Remove a single skill entry from skillset.toml (multi-line or inline)."""
    content = toml_path.read_text()
    content = re.sub(
        rf"^{re.escape(skill_name)}\s*=\s*(true|false)\n",
        "",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(rf",\s*{re.escape(skill_name)}\s*=\s*(true|false)", "", content)
    content = re.sub(rf"{re.escape(skill_name)}\s*=\s*(true|false),\s*", "", content)
    toml_path.write_text(content)
