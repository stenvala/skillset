"""Tests for skillset.paths."""

import sys
from pathlib import Path

from skillset.paths import abbrev, add_to_global_skillset, get_cache_dir, require_project_dir


def test_get_cache_dir(home_dir):
    assert get_cache_dir() == home_dir / ".cache" / "skillset" / "repos"


def test_abbrev(home_dir):
    p = home_dir / ".claude" / "skills"
    assert abbrev(p) == "~/.claude/skills" or abbrev(p) == "~\\.claude\\skills"


def test_abbrev_non_home():
    assert abbrev("/other/path") == "/other/path"


def test_require_project_dir_returns_path():
    p = Path("/some/path")
    assert require_project_dir(p) is p


def test_require_project_dir_exits_on_none():
    import pytest

    with pytest.raises(SystemExit):
        require_project_dir(None)


def test_add_to_global_skillset_creates_entry(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("[skills]\n")

    result = add_to_global_skillset("owner/repo")
    assert result is True
    content = toml_path.read_text()
    assert '"owner/repo" = true' in content


def test_add_to_global_skillset_no_duplicate(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text('[skills]\n"owner/repo" = true\n')

    result = add_to_global_skillset("owner/repo")
    assert result is False


def test_add_to_global_skillset_no_file(home_dir):
    result = add_to_global_skillset("owner/repo")
    assert result is False


def test_add_to_global_skillset_with_skills(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("[skills]\n")

    result = add_to_global_skillset(
        "owner/repo", skills={"skill-a": True, "skill-b": False}
    )
    assert result is True
    content = toml_path.read_text()
    assert "skill-a = true" in content
    assert "skill-b = false" in content


def test_add_to_global_skillset_editable(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("[skills]\n")

    result = add_to_global_skillset(
        "my-skills", editable=True, source="~/local/skills"
    )
    assert result is True
    content = toml_path.read_text()
    assert "editable = true" in content
    assert 'source = "~/local/skills"' in content
