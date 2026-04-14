"""Shared fixtures for vivainio/agent-skills integration tests."""

from pathlib import Path

import pytest

REPO = "vivainio/agent-skills"

MAIN_SKILLS = {
    "chat-transcript",
    "github-release",
    "public-github",
    "python-project",
    "tasks-py",
    "zaira",
}
EXTRA_SKILLS = {"mspec", "vp-code-review", "zipget"}


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Isolated environment with redirected home and project dirs."""
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
