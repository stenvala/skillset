"""Tests for skillset.commands.cmd_update."""

from unittest.mock import patch

import pytest

from skillset.commands import cmd_update
from skillset.manifest import record_install


def test_update_specific_repo(env, source_repo, capsys):
    # Set up cached repo
    cache_dir = env.home / ".cache" / "skillset" / "repos" / "owner" / "repo"
    cache_dir.mkdir(parents=True)
    # Copy skills content into cache
    for name in ("skill-a", "skill-b"):
        d = cache_dir / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"# {name}\n")

    # Pre-install skills
    skills_dir = env.home / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "skill-a").symlink_to(cache_dir / "skill-a")

    with patch("skillset.commands.update.clone_or_pull"):
        cmd_update(repo="owner/repo")

    output = capsys.readouterr().out
    assert "Updated" in output


def test_update_repo_not_installed_exits(env):
    with pytest.raises(SystemExit):
        cmd_update(repo="owner/repo")


def test_update_invalid_repo_exits(env):
    with pytest.raises(SystemExit):
        cmd_update(repo="invalid")


def test_update_all_repos(env, source_repo, capsys):
    # Set up cached repo
    cache_dir = env.home / ".cache" / "skillset" / "repos" / "owner" / "repo"
    cache_dir.mkdir(parents=True)
    for name in ("skill-a",):
        d = cache_dir / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"# {name}\n")

    skills_dir = env.home / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "skill-a").symlink_to(cache_dir / "skill-a")

    with patch("skillset.commands.update.clone_or_pull"):
        cmd_update()

    output = capsys.readouterr().out
    assert "Updated" in output


def test_update_no_repos(env, capsys):
    cmd_update()
    output = capsys.readouterr().out
    assert "No repos installed" in output


def test_update_with_new_flag(env, source_repo, capsys):
    cache_dir = env.home / ".cache" / "skillset" / "repos" / "owner" / "repo"
    cache_dir.mkdir(parents=True)
    for name in ("skill-a", "skill-b"):
        d = cache_dir / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"# {name}\n")

    with patch("skillset.commands.update.clone_or_pull"):
        cmd_update(repo="owner/repo", new=True)

    output = capsys.readouterr().out
    assert "Updated" in output


def test_update_linked_repo_skips_pull(env, source_repo, capsys):
    cache_dir = env.home / ".cache" / "skillset" / "repos" / "owner"
    cache_dir.mkdir(parents=True)
    (cache_dir / "repo").symlink_to(source_repo)

    skills_dir = env.home / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "skill-a").symlink_to(source_repo / "skill-a")

    cmd_update(repo="owner/repo")

    output = capsys.readouterr().out
    assert "Updated" in output


def test_update_all_with_linked_repo(env, source_repo, capsys):
    cache_dir = env.home / ".cache" / "skillset" / "repos" / "owner"
    cache_dir.mkdir(parents=True)
    (cache_dir / "repo").symlink_to(source_repo)

    skills_dir = env.home / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "skill-a").symlink_to(source_repo / "skill-a")

    cmd_update()
    output = capsys.readouterr().out
    assert "Updated" in output


def test_update_local_scope_outside_git(env, source_repo, capsys, monkeypatch):
    cache_dir = env.home / ".cache" / "skillset" / "repos" / "owner" / "repo"
    cache_dir.mkdir(parents=True)
    d = cache_dir / "skill-a"
    d.mkdir()
    (d / "SKILL.md").write_text("# skill-a\n")

    record_install("owner/repo", scope="local")
    monkeypatch.setattr("skillset.commands.update.get_git_root", lambda: None)

    with patch("skillset.commands.update.clone_or_pull"):
        cmd_update()

    output = capsys.readouterr().out
    assert "Skipping" in output


def test_update_all_non_dir_in_cache(env, source_repo, capsys):
    """Files (non-directories) inside cache owner dirs are skipped."""
    cache_dir = env.home / ".cache" / "skillset" / "repos" / "owner"
    cache_dir.mkdir(parents=True)
    # Create a real repo dir
    repo = cache_dir / "repo"
    repo.mkdir()
    d = repo / "skill-a"
    d.mkdir()
    (d / "SKILL.md").write_text("# skill-a\n")
    # Create a stray file next to the repo dir
    (cache_dir / ".DS_Store").write_text("x")

    skills_dir = env.home / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "skill-a").symlink_to(d)

    with patch("skillset.commands.update.clone_or_pull"):
        cmd_update()

    output = capsys.readouterr().out
    assert "Updated" in output
