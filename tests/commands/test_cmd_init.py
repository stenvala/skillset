"""Tests for skillset.commands.cmd_init."""

import pytest

from skillset.commands import cmd_init


def test_creates_global_skillset_toml(env):
    cmd_init(g=True)
    path = env.home / ".claude" / "skillset.toml"
    assert path.exists()
    assert "[skills]" in path.read_text()


def test_creates_local_skillset_toml(env):
    cmd_init()
    path = env.project / "skillset.toml"
    assert path.exists()
    assert "[skills]" in path.read_text()


def test_exits_if_already_exists(env):
    path = env.home / ".claude" / "skillset.toml"
    path.write_text("[skills]\n")

    with pytest.raises(SystemExit):
        cmd_init(g=True)


def test_local_exits_outside_git(env, monkeypatch):
    monkeypatch.setattr("skillset.paths.get_git_root", lambda: None)
    with pytest.raises(SystemExit):
        cmd_init()
