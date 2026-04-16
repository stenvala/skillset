"""Tests for skillset.commands.cmd_sync."""

from unittest.mock import patch

import pytest

from skillset.commands import cmd_sync


def test_no_file_exits(env):
    with pytest.raises(SystemExit):
        cmd_sync()


def test_empty_skills_section(env, capsys):
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text("skills: {}\n")

    cmd_sync()
    output = capsys.readouterr().out
    assert "No skills entries" in output


def test_sync_wildcard_entry(env, source_repo, capsys):
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text("skills:\n  owner/repo:\n    enabled: ['*']\n")

    with patch("skillset.commands.sync.clone_or_pull", return_value=source_repo):
        cmd_sync()

    output = capsys.readouterr().out
    assert "Syncing owner/repo" in output
    assert "skill-a" in output


def test_sync_glob_pattern_matches(env, source_repo, capsys):
    """enabled = ["skill-*"] expands to every skill in source (both skill-a and skill-b)."""
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text("skills:\n  owner/repo:\n    enabled: ['skill-*']\n")

    with patch("skillset.commands.sync.clone_or_pull", return_value=source_repo):
        cmd_sync()

    output = capsys.readouterr().out
    assert "+ skill-a" in output
    assert "+ skill-b" in output


def test_sync_glob_with_disabled_subtraction(env, source_repo, capsys):
    """Pattern on enabled minus an explicit disabled entry."""
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text(
        "skills:\n  owner/repo:\n    enabled: ['skill-*']\n    disabled: [skill-b]\n"
    )

    with patch("skillset.commands.sync.clone_or_pull", return_value=source_repo):
        cmd_sync()

    output = capsys.readouterr().out
    assert "+ skill-a" in output
    assert "+ skill-b" not in output


def test_sync_glob_does_not_cover_unrelated_new_skills(env, source_repo, capsys):
    """enabled=['skill-a*'] only covers skill-a; skill-b is still new and prompts."""
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text("skills:\n  owner/repo:\n    enabled: ['skill-a*']\n")

    with patch("skillset.commands.sync.clone_or_pull", return_value=source_repo):
        with patch("builtins.input", return_value="n"):
            cmd_sync()

    output = capsys.readouterr().out
    assert "+ skill-a" in output
    assert "New skills detected" in output
    assert "skill-b" in output


def test_sync_all_disabled_links_nothing(env, source_repo, capsys):
    """enabled=[] with every source skill in disabled links nothing and does not prompt."""
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text(
        "skills:\n  owner/repo:\n    enabled: []\n    disabled: [skill-a, skill-b]\n"
    )

    with patch("skillset.commands.sync.clone_or_pull", return_value=source_repo):
        cmd_sync()

    output = capsys.readouterr().out
    assert "Sync complete (0 skill(s) linked)" in output
    assert "New skills detected" not in output


def test_sync_invalid_repo_spec(env, capsys):
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text("skills:\n  invalid:\n    enabled: ['*']\n")

    cmd_sync()
    output = capsys.readouterr().out
    assert "Invalid repo format" in output


def test_sync_dict_entry_all_skills(env, source_repo, capsys):
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text("skills:\n  owner/repo:\n    enabled: ['*']\n")

    with patch("skillset.commands.sync.clone_or_pull", return_value=source_repo):
        cmd_sync()

    output = capsys.readouterr().out
    assert "Syncing owner/repo" in output


def test_sync_selective_skills(env, source_repo, capsys):
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text(
        "skills:\n  owner/repo:\n    enabled: [skill-a]\n    disabled: [skill-b]\n"
    )

    with patch("skillset.commands.sync.clone_or_pull", return_value=source_repo):
        cmd_sync()

    output = capsys.readouterr().out
    assert "skill-a" in output


def test_sync_detects_new_skills(env, source_repo, capsys):
    yaml_file = env.home / ".claude" / "skillset.yaml"
    # Only track skill-a, leaving skill-b as "new"
    yaml_file.write_text("skills:\n  owner/repo:\n    enabled: [skill-a]\n")

    with patch("skillset.commands.sync.clone_or_pull", return_value=source_repo):
        with patch("builtins.input", return_value="n"):
            cmd_sync()

    output = capsys.readouterr().out
    assert "New skills detected" in output
    assert "skill-b" in output


def test_sync_removes_excluded_skills(env, source_repo, capsys):
    skills_dir = env.home / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "skill-b").symlink_to(source_repo / "skill-b")

    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text(
        "skills:\n  owner/repo:\n    enabled: [skill-a]\n    disabled: [skill-b]\n"
    )

    with patch("skillset.commands.sync.clone_or_pull", return_value=source_repo):
        cmd_sync()

    assert not (skills_dir / "skill-b").exists()
    output = capsys.readouterr().out
    assert "excluded" in output


def test_sync_editable(env, source_repo, capsys):
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text(
        f"skills:\n  my-lib:\n    editable: true\n    source: {source_repo}\n"
    )

    cmd_sync()
    output = capsys.readouterr().out
    assert "editable" in output


def test_sync_editable_missing_source(env, capsys):
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text("skills:\n  my-lib:\n    editable: true\n")

    cmd_sync()
    output = capsys.readouterr().out
    assert "requires 'source' path" in output


def test_sync_editable_source_not_found(env, capsys):
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text(
        "skills:\n  my-lib:\n    editable: true\n    source: /nonexistent\n"
    )

    cmd_sync()
    output = capsys.readouterr().out
    assert "Source not found" in output


def test_sync_invalid_value_type(env, capsys):
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text("skills:\n  repo: 42\n")

    cmd_sync()
    output = capsys.readouterr().out
    assert "must be a sub-table" in output


def test_sync_with_path(env, source_repo, capsys):
    sub = source_repo / "sub"
    skill = sub / "nested-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# nested\n")

    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text(f"skills:\n  owner/repo:\n    path: sub\n")

    with patch("skillset.commands.sync.clone_or_pull", return_value=source_repo):
        cmd_sync()

    output = capsys.readouterr().out
    assert "nested-skill" in output


def test_sync_path_not_found_in_repo(env, source_repo, capsys):
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text("skills:\n  owner/repo:\n    path: nonexistent\n")

    with patch("skillset.commands.sync.clone_or_pull", return_value=source_repo):
        cmd_sync()

    output = capsys.readouterr().out
    assert "Path not found in repo" in output


def test_sync_editable_path_not_found(env, source_repo, capsys):
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text(
        f"skills:\n  my-lib:\n    editable: true\n    source: {source_repo}\n    path: nonexistent\n"
    )

    cmd_sync()
    output = capsys.readouterr().out
    assert "Path not found" in output


def test_sync_with_file_arg(env, source_repo, capsys):
    """Explicit file argument to cmd_sync."""
    yaml_file = env.tmp / "custom.yaml"
    yaml_file.write_text(f"skills:\n  {source_repo}:\n    enabled: ['*']\n")

    with patch("builtins.input", return_value="y"):
        cmd_sync(file=str(yaml_file))

    output = capsys.readouterr().out
    assert "Syncing" in output


def test_sync_global_flag(env, source_repo, capsys):
    """cmd_sync(g=True) uses global skillset.yaml."""
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text(f"skills:\n  {source_repo}:\n    enabled: ['*']\n")

    with patch("builtins.input", return_value="y"):
        cmd_sync(g=True)

    output = capsys.readouterr().out
    assert "Syncing" in output


def test_sync_local_scope(env, source_repo, capsys, monkeypatch):
    """Sync with local skillset.yaml found via find_skillset_root."""
    monkeypatch.setattr("skillset.commands.update.find_skillset_root", lambda: env.project)
    yaml_file = env.project / "skillset.yaml"
    yaml_file.write_text(f"skills:\n  {source_repo}:\n    enabled: ['*']\n")

    project_skills = env.project / ".claude" / "skills"
    project_skills.mkdir(parents=True)
    (env.project / ".claude" / "commands").mkdir(parents=True)

    with patch("builtins.input", return_value="y"):
        cmd_sync()

    output = capsys.readouterr().out
    assert "Syncing" in output


def test_sync_local_file_not_found(env, capsys, monkeypatch):
    """Local sync file not found shows local hint."""
    monkeypatch.setattr("skillset.commands.update.find_skillset_root", lambda: env.project)

    with pytest.raises(SystemExit):
        cmd_sync()

    output = capsys.readouterr().out
    assert "Run 'skillset init' to create one." in output


def test_sync_dict_invalid_repo_spec(env, capsys):
    """Dict entry with invalid repo spec in non-editable mode."""
    yaml_file = env.home / ".claude" / "skillset.yaml"
    yaml_file.write_text("skills:\n  invalid:\n    copy: true\n")

    cmd_sync()
    output = capsys.readouterr().out
    assert "Invalid repo format" in output
