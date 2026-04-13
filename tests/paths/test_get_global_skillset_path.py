"""Tests for skillset.paths.get_global_skillset_path."""

from skillset.paths import get_global_skillset_path


def test_returns_skillset_toml_under_home(home_dir):
    assert get_global_skillset_path() == home_dir / ".claude" / "skillset.toml"
