"""Tests for skillset.discovery.find_skills."""

from skillset.discovery import find_skills


def test_finds_skill_directories(skill_repo):
    skills = find_skills(skill_repo)
    names = sorted(s.name for s in skills)
    assert names == ["skill-a", "skill-b"]


def test_excludes_hidden_directories(skill_repo):
    skills = find_skills(skill_repo)
    names = [s.name for s in skills]
    assert "secret-skill" not in names


def test_finds_nested_skills(tmp_path):
    nested = tmp_path / "group" / "my-skill"
    nested.mkdir(parents=True)
    (nested / "SKILL.md").write_text("# nested\n")

    skills = find_skills(tmp_path)
    assert len(skills) == 1
    assert skills[0].name == "my-skill"


def test_returns_empty_for_no_skills(tmp_path):
    assert find_skills(tmp_path) == []
