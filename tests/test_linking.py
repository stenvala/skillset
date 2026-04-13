"""Tests for skillset.linking."""

import sys
from pathlib import Path

from skillset.linking import (
    SKILLSET_SOURCE_MARKER,
    copy_dir,
    fuzzy_match,
    get_copy_source,
    is_managed,
    is_managed_copy,
    link_commands,
    link_skills,
    remove_managed,
)


def test_fuzzy_match_exact():
    assert fuzzy_match("brainstorming", ["brainstorming", "other"]) == "brainstorming"


def test_fuzzy_match_close():
    result = fuzzy_match("brainstormin", ["brainstorming", "other"])
    assert result == "brainstorming"


def test_fuzzy_match_none():
    assert fuzzy_match("xyz", ["abc", "def"]) is None


def test_is_managed_copy(tmp_path):
    d = tmp_path / "skill"
    d.mkdir()
    (d / SKILLSET_SOURCE_MARKER).write_text("/some/path\n")
    assert is_managed_copy(d) is True


def test_is_managed_copy_no_marker(tmp_path):
    d = tmp_path / "skill"
    d.mkdir()
    assert is_managed_copy(d) is False


def test_get_copy_source(tmp_path):
    d = tmp_path / "skill"
    d.mkdir()
    (d / SKILLSET_SOURCE_MARKER).write_text("/original/path\n")
    assert get_copy_source(d) == "/original/path"


def test_get_copy_source_missing(tmp_path):
    assert get_copy_source(tmp_path / "nope") is None


def test_copy_dir(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "file.txt").write_text("hello")

    dst = tmp_path / "dst"
    copy_dir(src, dst, source_label="test/repo")

    assert (dst / "file.txt").read_text() == "hello"
    assert (dst / SKILLSET_SOURCE_MARKER).read_text().strip() == "test/repo"
    assert is_managed_copy(dst) is True


def test_remove_managed_copy(tmp_path):
    d = tmp_path / "skill"
    d.mkdir()
    (d / SKILLSET_SOURCE_MARKER).write_text("x\n")
    (d / "content.md").write_text("x")

    remove_managed(d)
    assert not d.exists()


def test_link_skills_copy_mode(skill_repo, tmp_path):
    target = tmp_path / "skills"
    linked = link_skills(skill_repo, target, copy=True)
    assert sorted(linked) == ["skill-a", "skill-b"]
    assert (target / "skill-a" / "SKILL.md").exists()
    assert is_managed_copy(target / "skill-a")


def test_link_skills_with_filter(skill_repo, tmp_path):
    target = tmp_path / "skills"
    linked = link_skills(skill_repo, target, only={"skill-a"}, copy=True)
    assert linked == ["skill-a"]
    assert not (target / "skill-b").exists()


def test_link_skills_glob_filter(skill_repo, tmp_path):
    target = tmp_path / "skills"
    linked = link_skills(skill_repo, target, only={"skill-*"}, copy=True)
    assert sorted(linked) == ["skill-a", "skill-b"]


def test_link_skills_existing_only(skill_repo, tmp_path):
    target = tmp_path / "skills"
    target.mkdir(parents=True)
    # Pre-create skill-a as a managed copy
    copy_dir(skill_repo / "skill-a", target / "skill-a")

    linked = link_skills(skill_repo, target, existing_only=True, copy=True)
    assert linked == ["skill-a"]


def test_link_commands_copy_mode(skill_repo, tmp_path):
    target = tmp_path / "commands"
    linked = link_commands(skill_repo, target, copy=True)
    assert "do-thing.md" in linked
    assert (target / "do-thing.md").exists()
