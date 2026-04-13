"""Tests for skillset.paths.get_cache_dir."""

from skillset.paths import get_cache_dir


def test_returns_cache_dir_under_home(home_dir):
    assert get_cache_dir() == home_dir / ".cache" / "skillset" / "repos"
