"""Tests for skillset.commands.cmd_apply."""

import subprocess
from unittest.mock import patch

import pytest

from skillset.commands import cmd_apply


def test_applies_skillset_toml(env, source_repo, capsys):
    toml = env.project / "skillset.toml"
    toml.write_text(f'[skills]\n"{source_repo}" = true\n')

    with patch("builtins.input", return_value="y"):
        cmd_apply(file=str(toml))

    output = capsys.readouterr().out
    assert "Adding" in output


def test_no_file_exits(env):
    with pytest.raises(SystemExit):
        cmd_apply()


def test_no_skills_section_exits(env):
    toml = env.project / "skillset.toml"
    toml.write_text("[other]\nkey = true\n")

    with pytest.raises(SystemExit):
        cmd_apply(file=str(toml))


def test_bool_false_skipped(env, source_repo, capsys):
    toml = env.project / "skillset.toml"
    toml.write_text(f'[skills]\n"{source_repo}" = false\n')

    cmd_apply(file=str(toml))
    # No "Adding" output since entry is disabled
    output = capsys.readouterr().out
    assert "Adding" not in output


def test_list_entry(env, source_repo, capsys):
    toml = env.project / "skillset.toml"
    toml.write_text(f'[skills]\n"{source_repo}" = ["skill-a"]\n')

    cmd_apply(file=str(toml))
    output = capsys.readouterr().out
    assert "Adding" in output


def test_dict_entry(env, source_repo, capsys):
    toml = env.project / "skillset.toml"
    toml.write_text(f'[skills."{source_repo}"]\nlocal = false\ncopy = true\n')

    with patch("builtins.input", return_value="y"):
        cmd_apply(file=str(toml))
    output = capsys.readouterr().out
    assert "Adding" in output


def test_invalid_entry_exits(env):
    toml = env.project / "skillset.toml"
    toml.write_text('[skills]\n"repo" = 42\n')

    with pytest.raises(SystemExit):
        cmd_apply(file=str(toml))


def test_links_section(env, capsys):
    toml = env.project / "skillset.toml"
    target = env.tmp / "target_file"
    target.write_text("content")

    toml.write_text(f'[skills]\n\n[links]\n"{env.project / "mylink"}" = "{target}"\n')

    with patch("skillset.commands.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=1)
        cmd_apply(file=str(toml))

    output = capsys.readouterr().out
    assert "Linked" in output


def test_links_existing_symlink(env, capsys):
    toml = env.project / "skillset.toml"
    target = env.tmp / "target"
    target.write_text("x")
    link_path = env.project / "mylink"
    link_path.symlink_to(target)

    toml.write_text(f'[skills]\n\n[links]\n"{link_path}" = "{target}"\n')

    with patch("skillset.commands.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        cmd_apply(file=str(toml))

    output = capsys.readouterr().out
    assert "already exists" in output


def test_links_existing_file_skipped(env, capsys):
    toml = env.project / "skillset.toml"
    target = env.tmp / "target"
    target.write_text("x")
    existing = env.project / "myfile"
    existing.write_text("real file")

    toml.write_text(f'[skills]\n\n[links]\n"{existing}" = "{target}"\n')

    with patch("skillset.commands.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        cmd_apply(file=str(toml))

    output = capsys.readouterr().out
    assert "Skipping" in output


def test_apply_global_flag(env, source_repo, capsys):
    """cmd_apply(g=True) uses global skillset.toml."""
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text(f'[skills]\n"{source_repo}" = true\n')

    with patch("builtins.input", return_value="y"):
        cmd_apply(g=True)

    output = capsys.readouterr().out
    assert "Adding" in output


def test_apply_local_skillset(env, source_repo, capsys, monkeypatch):
    """cmd_apply() finds local skillset.toml via find_skillset_root."""
    monkeypatch.setattr("skillset.commands.find_skillset_root", lambda: env.project)
    toml = env.project / "skillset.toml"
    toml.write_text(f'[skills]\n"{source_repo}" = true\n')

    with patch("builtins.input", return_value="y"):
        cmd_apply()

    output = capsys.readouterr().out
    assert "Adding" in output
