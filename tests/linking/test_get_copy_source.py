"""Tests for skillset.linking.get_copy_source."""

from skillset.linking import SKILLSET_SOURCE_MARKER, get_copy_source


def test_reads_source_from_marker(tmp_path):
    d = tmp_path / "skill"
    d.mkdir()
    (d / SKILLSET_SOURCE_MARKER).write_text("/original/path\n")
    assert get_copy_source(d) == "/original/path"


def test_returns_none_when_missing(tmp_path):
    assert get_copy_source(tmp_path / "nope") is None
