"""Tests for skillset.paths.add_to_global_skillset."""

from skillset.paths import add_to_global_skillset


def test_creates_entry(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("[skills]\n")

    result = add_to_global_skillset("owner/repo")
    assert result is True
    content = toml_path.read_text()
    assert '"owner/repo" = true' in content


def test_no_duplicate(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text('[skills]\n"owner/repo" = true\n')

    result = add_to_global_skillset("owner/repo")
    assert result is False


def test_no_file(home_dir):
    result = add_to_global_skillset("owner/repo")
    assert result is False


def test_with_skills(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("[skills]\n")

    result = add_to_global_skillset("owner/repo", skills={"skill-a": True, "skill-b": False})
    assert result is True
    content = toml_path.read_text()
    assert "skill-a = true" in content
    assert "skill-b = false" in content


def test_editable(home_dir):
    toml_path = home_dir / ".claude" / "skillset.toml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("[skills]\n")

    result = add_to_global_skillset("my-skills", editable=True, source="~/local/skills")
    assert result is True
    content = toml_path.read_text()
    assert "editable = true" in content
    assert 'source = "~/local/skills"' in content
