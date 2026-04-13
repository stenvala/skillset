"""Tests for skillset.repo."""

import pytest

from skillset.repo import parse_github_url, parse_repo_spec


def test_parse_repo_spec_valid():
    assert parse_repo_spec("owner/repo") == ("owner", "repo")


def test_parse_repo_spec_whitespace():
    assert parse_repo_spec("  owner/repo  ") == ("owner", "repo")


def test_parse_repo_spec_invalid():
    with pytest.raises(ValueError, match="Invalid repo format"):
        parse_repo_spec("just-a-name")


def test_parse_repo_spec_too_many_parts():
    with pytest.raises(ValueError, match="Invalid repo format"):
        parse_repo_spec("a/b/c")


def test_parse_github_url_simple():
    result = parse_github_url("https://github.com/owner/repo")
    assert result == ("owner", "repo", None, None)


def test_parse_github_url_with_tree():
    result = parse_github_url("https://github.com/owner/repo/tree/main/skills")
    assert result == ("owner", "repo", "main", "skills")


def test_parse_github_url_deep_path():
    result = parse_github_url(
        "https://github.com/owner/repo/tree/main/a/b/c"
    )
    assert result == ("owner", "repo", "main", "a/b/c")


def test_parse_github_url_strips_git_suffix():
    result = parse_github_url("https://github.com/owner/repo.git")
    assert result == ("owner", "repo", None, None)


def test_parse_github_url_trailing_slash():
    result = parse_github_url("https://github.com/owner/repo/")
    assert result == ("owner", "repo", None, None)


def test_parse_github_url_invalid():
    assert parse_github_url("https://gitlab.com/owner/repo") is None


def test_parse_github_url_not_url():
    assert parse_github_url("owner/repo") is None
