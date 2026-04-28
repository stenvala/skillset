"""After removing a skill entry from yaml, sync detects it and prompts."""

from unittest.mock import patch

from skillset.commands import cmd_add, cmd_update
from skillset.paths import load_skillset

from .conftest import FIXTURES, remove_skill_from_toml


class TestSyncEditableNewSkillPrompt:
    def _setup(self, local_env):
        """Add two editable skills (gamma marked disabled), then drop gamma from yaml."""
        cmd_add(repo=str(FIXTURES), skills=["alpha", "beta"])

        data = load_skillset(local_env.toml_path)
        entry = data["skills"]["editable_skills/fixtures"]
        assert "alpha" in entry["enabled"] and "beta" in entry["enabled"]
        assert "gamma" in entry["disabled"]

        remove_skill_from_toml(local_env.toml_path, "gamma")
        data = load_skillset(local_env.toml_path)
        entry = data["skills"]["editable_skills/fixtures"]
        assert "gamma" not in entry.get("enabled", [])
        assert "gamma" not in entry.get("disabled", [])

    def test_accept_new_skill(self, local_env, capsys):
        """User says 'y' -- gamma gets linked and appended to enabled."""
        self._setup(local_env)

        with patch("builtins.input", return_value="y"):
            cmd_update(file=str(local_env.toml_path))

        assert (local_env.skills_dir / "gamma").exists()
        data = load_skillset(local_env.toml_path)
        entry = data["skills"]["editable_skills/fixtures"]
        assert "gamma" in entry["enabled"]

        output = capsys.readouterr().out
        assert "New skills detected" in output

    def test_reject_new_skill(self, local_env, capsys):
        """User says 'n' -- gamma stays unlinked and appended to disabled."""
        self._setup(local_env)

        with patch("builtins.input", return_value="n"):
            cmd_update(file=str(local_env.toml_path))

        assert not (local_env.skills_dir / "gamma" / "SKILL.md").exists()
        data = load_skillset(local_env.toml_path)
        entry = data["skills"]["editable_skills/fixtures"]
        assert "gamma" in entry.get("disabled", [])

        output = capsys.readouterr().out
        assert "skipped" in output

    def test_yaml_remains_valid(self, local_env):
        """After sync updates the yaml, it's still valid YAML."""
        self._setup(local_env)

        with patch("builtins.input", return_value="y"):
            cmd_update(file=str(local_env.toml_path))

        data = load_skillset(local_env.toml_path)
        entry = data["skills"]["editable_skills/fixtures"]
        assert entry["editable"] is True
        assert "alpha" in entry["enabled"]
        assert "gamma" in entry["enabled"]

    def test_existing_skills_preserved(self, local_env):
        """Alpha and beta remain linked regardless of gamma decision."""
        self._setup(local_env)

        with patch("builtins.input", return_value="n"):
            cmd_update(file=str(local_env.toml_path))

        assert (local_env.skills_dir / "alpha").exists()
        assert (local_env.skills_dir / "beta").exists()
