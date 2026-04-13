"""Tests for skillset.repo.parse_repo_spec."""

import pytest

from skillset.repo import parse_repo_spec


def test_valid():
    assert parse_repo_spec("owner/repo") == ("owner", "repo")


def test_strips_whitespace():
    assert parse_repo_spec("  owner/repo  ") == ("owner", "repo")


def test_rejects_single_name():
    with pytest.raises(ValueError, match="Invalid repo format"):
        parse_repo_spec("just-a-name")


def test_rejects_too_many_parts():
    with pytest.raises(ValueError, match="Invalid repo format"):
        parse_repo_spec("a/b/c")
