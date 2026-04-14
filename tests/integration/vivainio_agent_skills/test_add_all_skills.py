"""skillset add vivainio/agent-skills -- all skills from repo."""

from unittest.mock import patch

from skillset.commands import cmd_add

from .conftest import MAIN_SKILLS, REPO


class TestAddAllSkills:
    def test_add_all_skills(self, env):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=REPO)

        skills_dir = env.home / ".claude" / "skills"
        installed = {p.name for p in skills_dir.iterdir() if p.is_dir()}
        assert MAIN_SKILLS.issubset(installed), f"Missing skills: {MAIN_SKILLS - installed}"

    def test_add_all_reports_linked(self, env, capsys):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=REPO)

        output = capsys.readouterr().out
        assert "Linked" in output
