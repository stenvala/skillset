"""skillset add /path -e -- add all, then toml lists every skill as true."""

from unittest.mock import patch

from skillset.commands import cmd_add

from .conftest import ALL_SKILLS, FIXTURES, installed_skills


class TestAddEditableAllSkills:
    def test_all_skills_linked(self, local_env):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=str(FIXTURES), editable=True)

        assert ALL_SKILLS.issubset(installed_skills(local_env.skills_dir))

    def test_toml_lists_all_as_true(self, local_env):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=str(FIXTURES), editable=True)

        content = local_env.toml_path.read_text()
        for skill in ALL_SKILLS:
            assert f"{skill} = true" in content
