"""Tests for skillset.ui.find_editable_skill."""

from skillset.ui import find_editable_skill


def test_finds_skill_in_editable_source(home_dir, tmp_path):
    # Create editable source with a skill
    source = tmp_path / "skills-repo"
    skill = source / "my-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# my-skill\n")

    # Set up skillset.toml pointing to the source
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text(
        f'[skills]\n"my-lib" = {{editable = true, source = "{source}"}}\n'
    )

    result = find_editable_skill("my-skill")
    assert result is not None
    found_dir, toml_key = result
    assert toml_key == "my-lib"


def test_returns_none_when_not_found(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("[skills]\n")

    assert find_editable_skill("nonexistent") is None


def test_returns_none_when_no_toml(home_dir):
    assert find_editable_skill("anything") is None


def test_skips_non_editable_entries(home_dir, tmp_path):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text('[skills]\n"owner/repo" = true\n')

    assert find_editable_skill("some-skill") is None


def test_skips_missing_source_dir(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text(
        '[skills]\n"lib" = {editable = true, source = "/nonexistent/path"}\n'
    )

    assert find_editable_skill("skill") is None


def test_with_subpath(home_dir, tmp_path):
    source = tmp_path / "mono"
    skill = source / "sub" / "my-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# my-skill\n")

    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text(
        f'[skills]\n"lib" = {{editable = true, source = "{source}", path = "sub"}}\n'
    )

    result = find_editable_skill("my-skill")
    assert result is not None


def test_skips_editable_without_source(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text('[skills]\n"lib" = {editable = true}\n')

    assert find_editable_skill("skill") is None
