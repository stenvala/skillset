"""Tests for skillset.paths.abbrev."""

from skillset.paths import abbrev


def test_abbreviates_home_path(home_dir):
    p = home_dir / ".claude" / "skills"
    assert abbrev(p) == "~/.claude/skills" or abbrev(p) == "~\\.claude\\skills"


def test_leaves_non_home_path_unchanged():
    assert abbrev("/other/path") == "/other/path"
