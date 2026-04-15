"""Tests for skillset.paths.add_to_global_skillset."""

from skillset.paths import add_to_global_skillset


def test_creates_entry(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("[skills]\n")

    result = add_to_global_skillset("owner/repo", enabled=["*"])
    assert result is True
    content = toml_path.read_text()
    assert '[skills."owner/repo"]' in content
    assert 'enabled = ["*"]' in content


def test_no_duplicate(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text('[skills."owner/repo"]\nenabled = ["*"]\n')

    result = add_to_global_skillset("owner/repo", enabled=["*"])
    assert result is False


def test_no_file(home_dir):
    result = add_to_global_skillset("owner/repo", enabled=["*"])
    assert result is False


def test_with_skills(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("[skills]\n")

    result = add_to_global_skillset("owner/repo", enabled=["skill-a"], disabled=["skill-b"])
    assert result is True
    content = toml_path.read_text()
    assert 'enabled = ["skill-a"]' in content
    assert 'disabled = ["skill-b"]' in content


def test_editable(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("[skills]\n")

    result = add_to_global_skillset(
        "my-skills", editable=True, source="~/local/skills", enabled=["*"]
    )
    assert result is True
    content = toml_path.read_text()
    assert "editable = true" in content
    assert 'source = "~/local/skills"' in content
