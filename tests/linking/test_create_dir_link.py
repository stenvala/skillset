"""Tests for skillset.linking.create_dir_link."""

from skillset.linking import create_dir_link


def test_creates_symlink(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"

    create_dir_link(link, target)
    assert link.is_symlink()
    assert link.resolve() == target.resolve()
