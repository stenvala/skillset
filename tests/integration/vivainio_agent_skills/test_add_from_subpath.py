"""skillset add vivainio/agent-skills -p extra-skills -- skills from subdirectory."""

from unittest.mock import patch

from skillset.commands import cmd_add

from .conftest import EXTRA_SKILLS, MAIN_SKILLS, REPO


class TestAddFromSubpath:
    def test_subpath_installs_extra_skills(self, env):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=REPO, subpath="extra-skills")

        skills_dir = env.home / ".claude" / "skills"
        installed = {p.name for p in skills_dir.iterdir() if p.is_dir()}
        assert EXTRA_SKILLS.issubset(installed), f"Missing: {EXTRA_SKILLS - installed}"

    def test_subpath_does_not_install_main_skills(self, env):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=REPO, subpath="extra-skills")

        skills_dir = env.home / ".claude" / "skills"
        installed = {p.name for p in skills_dir.iterdir() if p.is_dir()}
        assert not (MAIN_SKILLS & installed), (
            f"Main skills should not be installed: {MAIN_SKILLS & installed}"
        )
