"""Tests for skillset.paths.find_skillset_root."""

from skillset.paths import find_skillset_root


def test_finds_skillset_toml_in_cwd(tmp_path, monkeypatch):
    (tmp_path / "skillset.toml").write_text("[skills]\n")
    monkeypatch.chdir(tmp_path)

    result = find_skillset_root()
    assert result == tmp_path


def test_finds_skillset_toml_in_parent(tmp_path, monkeypatch):
    (tmp_path / "skillset.toml").write_text("[skills]\n")
    child = tmp_path / "sub" / "deep"
    child.mkdir(parents=True)
    monkeypatch.chdir(child)

    result = find_skillset_root()
    assert result == tmp_path


def test_returns_none_when_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = find_skillset_root()
    assert result is None
