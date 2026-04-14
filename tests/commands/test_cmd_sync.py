"""Tests for skillset.commands.cmd_sync."""

from unittest.mock import patch

import pytest

from skillset.commands import cmd_sync


def test_no_file_exits(env):
    with pytest.raises(SystemExit):
        cmd_sync()


def test_empty_skills_section(env, capsys):
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text("[skills]\n")

    cmd_sync()
    output = capsys.readouterr().out
    assert "No [skills] entries" in output


def test_sync_bool_true_entry(env, source_repo, capsys):
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text('[skills]\n"owner/repo" = true\n')

    with patch("skillset.commands.clone_or_pull", return_value=source_repo):
        cmd_sync()

    output = capsys.readouterr().out
    assert "Syncing owner/repo" in output
    assert "skill-a" in output


def test_sync_bool_false_skipped(env, capsys):
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text('[skills]\n"owner/repo" = false\n')

    cmd_sync()
    output = capsys.readouterr().out
    assert "Sync complete (0 skill(s) linked)" in output


def test_sync_invalid_repo_spec(env, capsys):
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text('[skills]\n"invalid" = true\n')

    cmd_sync()
    output = capsys.readouterr().out
    assert "Invalid repo format" in output


def test_sync_dict_entry_all_skills(env, source_repo, capsys):
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text('[skills]\n"owner/repo" = {}\n')

    with patch("skillset.commands.clone_or_pull", return_value=source_repo):
        cmd_sync()

    output = capsys.readouterr().out
    assert "Syncing owner/repo" in output


def test_sync_selective_skills(env, source_repo, capsys):
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text('[skills."owner/repo"]\nskill-a = true\nskill-b = false\n')

    with patch("skillset.commands.clone_or_pull", return_value=source_repo):
        cmd_sync()

    output = capsys.readouterr().out
    assert "skill-a" in output


def test_sync_detects_new_skills(env, source_repo, capsys):
    toml = env.home / ".claude" / "skillset.toml"
    # Only track skill-a, leaving skill-b as "new"
    toml.write_text('[skills."owner/repo"]\nskill-a = true\n')

    with patch("skillset.commands.clone_or_pull", return_value=source_repo):
        with patch("builtins.input", return_value="n"):
            cmd_sync()

    output = capsys.readouterr().out
    assert "New skills detected" in output
    assert "skill-b" in output


def test_sync_removes_excluded_skills(env, source_repo, capsys):
    skills_dir = env.home / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "skill-b").symlink_to(source_repo / "skill-b")

    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text('[skills."owner/repo"]\nskill-a = true\nskill-b = false\n')

    with patch("skillset.commands.clone_or_pull", return_value=source_repo):
        cmd_sync()

    assert not (skills_dir / "skill-b").exists()
    output = capsys.readouterr().out
    assert "excluded" in output


def test_sync_editable(env, source_repo, capsys):
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text(f'[skills."my-lib"]\neditable = true\nsource = "{source_repo}"\n')

    cmd_sync()
    output = capsys.readouterr().out
    assert "editable" in output


def test_sync_editable_missing_source(env, capsys):
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text('[skills."my-lib"]\neditable = true\n')

    cmd_sync()
    output = capsys.readouterr().out
    assert "requires 'source' path" in output


def test_sync_editable_source_not_found(env, capsys):
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text('[skills."my-lib"]\neditable = true\nsource = "/nonexistent"\n')

    cmd_sync()
    output = capsys.readouterr().out
    assert "Source not found" in output


def test_sync_invalid_value_type(env, capsys):
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text('[skills]\n"repo" = 42\n')

    cmd_sync()
    output = capsys.readouterr().out
    assert "invalid value type" in output


def test_sync_with_path(env, source_repo, capsys):
    sub = source_repo / "sub"
    skill = sub / "nested-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# nested\n")

    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text('[skills."owner/repo"]\npath = "sub"\n')

    with patch("skillset.commands.clone_or_pull", return_value=source_repo):
        cmd_sync()

    output = capsys.readouterr().out
    assert "nested-skill" in output


def test_sync_path_not_found_in_repo(env, source_repo, capsys):
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text('[skills."owner/repo"]\npath = "nonexistent"\n')

    with patch("skillset.commands.clone_or_pull", return_value=source_repo):
        cmd_sync()

    output = capsys.readouterr().out
    assert "Path not found in repo" in output


def test_sync_editable_path_not_found(env, source_repo, capsys):
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text(
        f'[skills."my-lib"]\neditable = true\nsource = "{source_repo}"\npath = "nonexistent"\n'
    )

    cmd_sync()
    output = capsys.readouterr().out
    assert "Path not found" in output


def test_sync_with_file_arg(env, source_repo, capsys):
    """Explicit file argument to cmd_sync."""
    toml = env.tmp / "custom.toml"
    toml.write_text(f'[skills]\n"{source_repo}" = true\n')

    with patch("builtins.input", return_value="y"):
        cmd_sync(file=str(toml))

    output = capsys.readouterr().out
    assert "Syncing" in output


def test_sync_global_flag(env, source_repo, capsys):
    """cmd_sync(g=True) uses global skillset.toml."""
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text(f'[skills]\n"{source_repo}" = true\n')

    with patch("builtins.input", return_value="y"):
        cmd_sync(g=True)

    output = capsys.readouterr().out
    assert "Syncing" in output


def test_sync_local_scope(env, source_repo, capsys, monkeypatch):
    """Sync with local skillset.toml found via find_skillset_root."""
    monkeypatch.setattr("skillset.commands.find_skillset_root", lambda: env.project)
    toml = env.project / "skillset.toml"
    toml.write_text(f'[skills]\n"{source_repo}" = true\n')

    project_skills = env.project / ".claude" / "skills"
    project_skills.mkdir(parents=True)
    (env.project / ".claude" / "commands").mkdir(parents=True)

    with patch("builtins.input", return_value="y"):
        cmd_sync()

    output = capsys.readouterr().out
    assert "Syncing" in output


def test_sync_local_file_not_found(env, capsys, monkeypatch):
    """Local sync file not found shows local hint."""
    monkeypatch.setattr("skillset.commands.find_skillset_root", lambda: env.project)

    with pytest.raises(SystemExit):
        cmd_sync()

    output = capsys.readouterr().out
    assert "Run 'skillset init' to create one." in output


def test_sync_dict_invalid_repo_spec(env, capsys):
    """Dict entry with invalid repo spec in non-editable mode."""
    toml = env.home / ".claude" / "skillset.toml"
    toml.write_text('[skills."invalid"]\ncopy = true\n')

    cmd_sync()
    output = capsys.readouterr().out
    assert "Invalid repo format" in output
