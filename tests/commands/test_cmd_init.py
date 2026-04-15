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


def test_local_outside_git_creates_in_cwd(env, monkeypatch, tmp_path):
    monkeypatch.setattr("skillset.paths.get_git_root", lambda: None)
    monkeypatch.chdir(tmp_path)
    cmd_init()
    assert (tmp_path / "skillset.toml").exists()
