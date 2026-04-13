"""Tests for skillset.paths.get_project_commands_dir."""

from skillset.paths import get_project_commands_dir


def test_returns_project_commands_dir(git_root):
    result = get_project_commands_dir()
    assert result == git_root / ".claude" / "commands"


def test_returns_none_outside_git_repo(monkeypatch):
    monkeypatch.setattr("skillset.paths.get_git_root", lambda: None)
    assert get_project_commands_dir() is None
