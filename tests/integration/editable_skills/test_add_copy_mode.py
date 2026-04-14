"""skillset add /path -e --copy -- copies instead of symlinking."""

from unittest.mock import patch

from skillset.commands import cmd_add

from .conftest import ALL_SKILLS, FIXTURES, installed_skills


class TestAddCopyMode:
    def test_copy_creates_real_dirs(self, local_env):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=str(FIXTURES), editable=True, copy=True)

        for skill in ALL_SKILLS:
            skill_dir = local_env.skills_dir / skill
            if skill_dir.exists():
                assert skill_dir.is_dir()
                assert not skill_dir.is_symlink()

    def test_copy_output_says_copied(self, local_env, capsys):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=str(FIXTURES), editable=True, copy=True)

        output = capsys.readouterr().out
        assert "Copied" in output

    def test_copy_installs_all_skills(self, local_env):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=str(FIXTURES), editable=True, copy=True)

        assert ALL_SKILLS.issubset(installed_skills(local_env.skills_dir))
