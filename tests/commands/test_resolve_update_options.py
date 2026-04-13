"""Tests for skillset.commands._resolve_update_options."""

from skillset.commands import _resolve_update_options
from skillset.manifest import record_install


def test_defaults_when_no_manifest(home_dir):
    subpath, use_copy, scope = _resolve_update_options("owner/repo")
    assert subpath is None
    assert use_copy is False
    assert scope == "global"


def test_reads_from_manifest(home_dir):
    record_install("owner/repo", subpath="skills", copy=True, scope="local")
    subpath, use_copy, scope = _resolve_update_options("owner/repo")
    assert subpath == "skills"
    assert use_copy is True
    assert scope == "local"


def test_global_flag_overrides_scope(home_dir):
    record_install("owner/repo", scope="local")
    _, _, scope = _resolve_update_options("owner/repo", g=True)
    assert scope == "global"


def test_copy_flag_overrides(home_dir):
    record_install("owner/repo")
    _, use_copy, _ = _resolve_update_options("owner/repo", copy=True)
    assert use_copy is True
