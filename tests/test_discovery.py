"""Tests for skillset.discovery."""

from skillset.discovery import find_commands, find_skills


def test_find_skills(skill_repo):
    skills = find_skills(skill_repo)
    names = sorted(s.name for s in skills)
    assert names == ["skill-a", "skill-b"]


def test_find_skills_excludes_hidden(skill_repo):
    skills = find_skills(skill_repo)
    names = [s.name for s in skills]
    assert "secret-skill" not in names


def test_find_skills_nested(tmp_path):
    nested = tmp_path / "group" / "my-skill"
    nested.mkdir(parents=True)
    (nested / "SKILL.md").write_text("# nested\n")

    skills = find_skills(tmp_path)
    assert len(skills) == 1
    assert skills[0].name == "my-skill"


def test_find_skills_empty(tmp_path):
    assert find_skills(tmp_path) == []


def test_find_commands(skill_repo):
    commands = find_commands(skill_repo)
    names = [c.name for c in commands]
    assert "do-thing.md" in names


def test_find_commands_nested(tmp_path):
    nested = tmp_path / "commands" / "sub"
    nested.mkdir(parents=True)
    (nested / "nested-cmd.md").write_text("# cmd\n")
    (tmp_path / "commands" / "top-cmd.md").write_text("# cmd\n")

    commands = find_commands(tmp_path)
    names = sorted(c.name for c in commands)
    assert "nested-cmd.md" in names
    assert "top-cmd.md" in names


def test_find_commands_empty(tmp_path):
    assert find_commands(tmp_path) == []
