"""Tests for skillset.paths.add_to_global_skillset."""

from skillset.paths import add_to_global_skillset, load_skillset


def test_creates_entry(home_dir):
    toml_path = home_dir / ".claude" / "skillset.yaml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("skills: {}\n")

    result = add_to_global_skillset("owner/repo", enabled=["*"])
    assert result is True

    data = load_skillset(toml_path)
    assert "owner/repo" in data["skills"]
    assert list(data["skills"]["owner/repo"]["enabled"]) == ["*"]


def test_no_duplicate(home_dir):
    toml_path = home_dir / ".claude" / "skillset.yaml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("skills:\n  owner/repo:\n    enabled: ['*']\n")

    result = add_to_global_skillset("owner/repo", enabled=["*"])
    assert result is False


def test_no_file(home_dir):
    result = add_to_global_skillset("owner/repo", enabled=["*"])
    assert result is False


def test_with_skills(home_dir):
    toml_path = home_dir / ".claude" / "skillset.yaml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("skills: {}\n")

    result = add_to_global_skillset(
        "owner/repo", enabled=["skill-a"], disabled=["skill-b"]
    )
    assert result is True

    data = load_skillset(toml_path)
    entry = data["skills"]["owner/repo"]
    assert list(entry["enabled"]) == ["skill-a"]
    assert list(entry["disabled"]) == ["skill-b"]


def test_editable(home_dir):
    toml_path = home_dir / ".claude" / "skillset.yaml"
    toml_path.parent.mkdir(parents=True)
    toml_path.write_text("skills: {}\n")

    result = add_to_global_skillset(
        "my-skills", editable=True, source="~/local/skills", enabled=["*"]
    )
    assert result is True

    data = load_skillset(toml_path)
    entry = data["skills"]["my-skills"]
    assert entry["editable"] is True
    assert entry["source"] == "~/local/skills"
