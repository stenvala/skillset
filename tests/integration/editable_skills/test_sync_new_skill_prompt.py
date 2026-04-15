"""After removing a skill entry from toml, sync detects it and prompts."""

import tomllib
from unittest.mock import patch

from skillset.commands import cmd_add, cmd_sync

from .conftest import FIXTURES, remove_skill_from_toml


class TestSyncEditableNewSkillPrompt:
    def _setup(self, local_env):
        """Add all editable skills, then remove gamma from toml."""
        cmd_add(repo=str(FIXTURES), skills=["alpha", "beta"])

        content = local_env.toml_path.read_text()
        assert "alpha = true" in content
        assert "beta = true" in content
        assert "gamma = false" in content

        remove_skill_from_toml(local_env.toml_path, "gamma")
        content = local_env.toml_path.read_text()
        assert "gamma" not in content

    def test_accept_new_skill(self, local_env, capsys):
        """User says 'y' -- gamma gets linked and toml updated with true."""
        self._setup(local_env)

        with patch("builtins.input", return_value="y"):
            cmd_sync(file=str(local_env.toml_path))

        assert (local_env.skills_dir / "gamma").exists()
        content = local_env.toml_path.read_text()
        assert "gamma = true" in content

        output = capsys.readouterr().out
        assert "New skills detected" in output

    def test_reject_new_skill(self, local_env, capsys):
        """User says 'n' -- gamma stays unlinked and toml updated with false."""
        self._setup(local_env)

        with patch("builtins.input", return_value="n"):
            cmd_sync(file=str(local_env.toml_path))

        assert not (local_env.skills_dir / "gamma" / "SKILL.md").exists()
        content = local_env.toml_path.read_text()
        assert "gamma = false" in content

        output = capsys.readouterr().out
        assert "skipped" in output

    def test_toml_remains_valid(self, local_env):
        """After sync updates the toml, it's still valid TOML."""
        self._setup(local_env)

        with patch("builtins.input", return_value="y"):
            cmd_sync(file=str(local_env.toml_path))

        with open(local_env.toml_path, "rb") as f:
            config = tomllib.load(f)
        skills_config = config["skills"]["editable_skills/fixtures"]
        assert skills_config["editable"] is True
        assert skills_config["alpha"] is True
        assert skills_config["gamma"] is True

    def test_existing_skills_preserved(self, local_env):
        """Alpha and beta remain linked regardless of gamma decision."""
        self._setup(local_env)

        with patch("builtins.input", return_value="n"):
            cmd_sync(file=str(local_env.toml_path))

        assert (local_env.skills_dir / "alpha").exists()
        assert (local_env.skills_dir / "beta").exists()
