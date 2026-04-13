"""Tests for skillset.manifest.record_install."""

from skillset.manifest import get_install_options, record_install


def test_basic(home_dir):
    record_install("owner/repo", subpath="skills", scope="global")
    opts = get_install_options("owner/repo")
    assert opts["subpath"] == "skills"
    assert opts["copy"] is False
    assert opts["scope"] == "global"
    assert opts["trial"] is False


def test_trial_flag(home_dir):
    record_install("owner/repo", trial=True)
    assert get_install_options("owner/repo")["trial"] is True


def test_trial_preserve(home_dir):
    record_install("owner/repo", trial=True)
    # Re-record without explicit trial — should preserve
    record_install("owner/repo", trial=None)
    assert get_install_options("owner/repo")["trial"] is True


def test_trial_clear(home_dir):
    record_install("owner/repo", trial=True)
    record_install("owner/repo", trial=False)
    assert get_install_options("owner/repo")["trial"] is False


