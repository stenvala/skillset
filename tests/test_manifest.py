"""Tests for skillset.manifest."""

from skillset.manifest import (
    get_install_options,
    load_manifest,
    record_install,
    save_manifest,
)


def test_load_manifest_empty(home_dir):
    assert load_manifest() == {}


def test_save_and_load_round_trip(home_dir):
    data = {"owner/repo": {"subpath": None, "copy": False, "scope": "global"}}
    save_manifest(data)
    assert load_manifest() == data


def test_record_install_basic(home_dir):
    record_install("owner/repo", subpath="skills", scope="global")
    opts = get_install_options("owner/repo")
    assert opts["subpath"] == "skills"
    assert opts["copy"] is False
    assert opts["scope"] == "global"
    assert opts["trial"] is False


def test_record_install_trial(home_dir):
    record_install("owner/repo", trial=True)
    assert get_install_options("owner/repo")["trial"] is True


def test_record_install_trial_preserve(home_dir):
    record_install("owner/repo", trial=True)
    # Re-record without explicit trial — should preserve
    record_install("owner/repo", trial=None)
    assert get_install_options("owner/repo")["trial"] is True


def test_record_install_trial_clear(home_dir):
    record_install("owner/repo", trial=True)
    record_install("owner/repo", trial=False)
    assert get_install_options("owner/repo")["trial"] is False


def test_get_install_options_missing(home_dir):
    assert get_install_options("nonexistent") is None
