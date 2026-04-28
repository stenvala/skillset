"""Tests for skillset.commands.cmd_apply."""

import subprocess
from unittest.mock import patch

import pytest

from skillset.commands import cmd_apply


def test_applies_skillset_yaml(env, source_repo, capsys):
    yaml_file = env.project / "skillset.yaml"
    yaml_file.write_text(f"skills:\n  {source_repo}:\n    enabled: ['*']\n")

    with patch("builtins.input", return_value="y"):
        cmd_apply(file=str(yaml_file))

    output = capsys.readouterr().out
    assert "Adding" in output


def test_no_file_exits(env):
    with pytest.raises(SystemExit):
        cmd_apply()


def test_no_skills_section_exits(env):
    yaml_file = env.project / "skillset.yaml"
    yaml_file.write_text("other:\n  key: true\n")

    with pytest.raises(SystemExit):
        cmd_apply(file=str(yaml_file))


def test_empty_enabled_skipped(env, source_repo, capsys):
    yaml_file = env.project / "skillset.yaml"
    yaml_file.write_text(f"skills:\n  {source_repo}:\n    enabled: []\n")

    cmd_apply(file=str(yaml_file))
    # No "Adding" output since enabled is empty
    output = capsys.readouterr().out
    assert "Adding" not in output


def test_dict_entry_with_copy(env, source_repo, capsys):
    yaml_file = env.project / "skillset.yaml"
    yaml_file.write_text(
        f"skills:\n  {source_repo}:\n    copy: true\n    enabled: ['*']\n"
    )

    with patch("builtins.input", return_value="y"):
        cmd_apply(file=str(yaml_file))
    output = capsys.readouterr().out
    assert "Adding" in output


def test_invalid_entry_exits(env):
    yaml_file = env.project / "skillset.yaml"
    yaml_file.write_text("skills:\n  repo: 42\n")

    with pytest.raises(SystemExit):
        cmd_apply(file=str(yaml_file))


def test_links_section(env, capsys):
    yaml_file = env.project / "skillset.yaml"
    target = env.tmp / "target_file"
    target.write_text("content")
    link_path = env.project / "mylink"

    yaml_file.write_text(
        f"skills: {{}}\nlinks:\n  {link_path}: {target}\n"
    )

    with patch("skillset.commands.apply.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=1)
        cmd_apply(file=str(yaml_file))

    output = capsys.readouterr().out
    assert "Linked" in output


def test_links_existing_symlink(env, capsys):
    yaml_file = env.project / "skillset.yaml"
    target = env.tmp / "target"
    target.write_text("x")
    link_path = env.project / "mylink"
    link_path.symlink_to(target)

    yaml_file.write_text(
        f"skills: {{}}\nlinks:\n  {link_path}: {target}\n"
    )

    with patch("skillset.commands.apply.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        cmd_apply(file=str(yaml_file))

    output = capsys.readouterr().out
    assert "already exists" in output


def test_links_existing_file_skipped(env, capsys):
    yaml_file = env.project / "skillset.yaml"
    target = env.tmp / "target"
    target.write_text("x")
    existing = env.project / "myfile"
    existing.write_text("real file")

    yaml_file.write_text(
        f"skills: {{}}\nlinks:\n  {existing}: {target}\n"
    )

    with patch("skillset.commands.apply.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        cmd_apply(file=str(yaml_file))

    output = capsys.readouterr().out
    assert "Skipping" in output


def test_apply_global_flag(env, source_repo, capsys):
    """cmd_apply(g=True) uses global skillset.yaml."""
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text(f"skills:\n  {source_repo}:\n    enabled: ['*']\n")

    with patch("builtins.input", return_value="y"):
        cmd_apply(g=True)

    output = capsys.readouterr().out
    assert "Adding" in output


def test_apply_local_skillset(env, source_repo, capsys, monkeypatch):
    """cmd_apply() finds local skillset.yaml via find_skillset_root."""
    monkeypatch.setattr("skillset.commands.apply.find_skillset_root", lambda: env.project)
    yaml_file = env.project / "skillset.yaml"
    yaml_file.write_text(f"skills:\n  {source_repo}:\n    enabled: ['*']\n")

    with patch("builtins.input", return_value="y"):
        cmd_apply()

    output = capsys.readouterr().out
    assert "Adding" in output
