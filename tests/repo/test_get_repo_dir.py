"""Tests for skillset.repo.get_repo_dir."""

from skillset.repo import get_repo_dir


def test_returns_path_under_cache(home_dir):
    result = get_repo_dir("owner", "repo")
    assert result == home_dir / ".cache" / "skillset" / "repos" / "owner" / "repo"
