"""New skills appear in the editable directory; sync offers a/i/s menu.

Simulates the scenario where someone adds new skills to a shared
editable skills repo and the user runs `skillset sync`.
"""

import shutil
import tomllib
from unittest.mock import patch

import pytest

from skillset.commands import cmd_sync

from .conftest import FIXTURES, installed_skills


class TestSyncNewSkillAddedToEditableDir:
    @pytest.fixture
    def editable_dir(self, tmp_path):
        """Copy fixtures to a mutable dir and return it."""
        d = tmp_path / "editable-skills"
        shutil.copytree(FIXTURES, d)
        return d

    def _setup(self, local_env, editable_dir):
        """Install all three original skills, then add two new ones to the dir."""
        local_env.toml_path.write_text(
            f"[skills]\n"
            f'[skills."editable-skills"]\n'
            f"editable = true\n"
            f'source = "{editable_dir}"\n'
            f"alpha = true\n"
            f"beta = true\n"
            f"gamma = true\n"
        )

        cmd_sync(file=str(local_env.toml_path))
        assert installed_skills(local_env.skills_dir) == {"alpha", "beta", "gamma"}

        for name in ("delta", "epsilon"):
            skill_dir = editable_dir / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"# {name}\n")

    def test_add_all(self, local_env, editable_dir, capsys):
        """User chooses 'a' -- both new skills linked and toml updated as true."""
        self._setup(local_env, editable_dir)

        with patch("builtins.input", return_value="a"):
            cmd_sync(file=str(local_env.toml_path))

        installed = installed_skills(local_env.skills_dir)
        assert "delta" in installed
        assert "epsilon" in installed

        content = local_env.toml_path.read_text()
        assert "delta = true" in content
        assert "epsilon = true" in content

        output = capsys.readouterr().out
        assert "New skills detected" in output
        assert "2 new skill(s)" in output

    def test_ignore_all(self, local_env, editable_dir, capsys):
        """User chooses 'i' -- neither new skill linked, toml updated as false."""
        self._setup(local_env, editable_dir)

        with patch("builtins.input", return_value="i"):
            cmd_sync(file=str(local_env.toml_path))

        installed = installed_skills(local_env.skills_dir)
        assert "delta" not in installed
        assert "epsilon" not in installed

        content = local_env.toml_path.read_text()
        assert "delta = false" in content
        assert "epsilon = false" in content

        output = capsys.readouterr().out
        assert "skipped" in output

    def test_select_individually(self, local_env, editable_dir, capsys):
        """User chooses 's', then accepts delta and rejects epsilon."""
        self._setup(local_env, editable_dir)

        responses = iter(["s", "y", "n"])
        with patch("builtins.input", side_effect=responses):
            cmd_sync(file=str(local_env.toml_path))

        installed = installed_skills(local_env.skills_dir)
        assert "delta" in installed
        assert "epsilon" not in installed

        content = local_env.toml_path.read_text()
        assert "delta = true" in content
        assert "epsilon = false" in content

    def test_original_skills_preserved(self, local_env, editable_dir):
        """Original skills remain linked regardless of new skill decisions."""
        self._setup(local_env, editable_dir)

        with patch("builtins.input", return_value="i"):
            cmd_sync(file=str(local_env.toml_path))

        for skill in ("alpha", "beta", "gamma"):
            assert (local_env.skills_dir / skill).exists()

    def test_toml_remains_valid_after_add_all(self, local_env, editable_dir):
        """Toml is valid after adding all new skills."""
        self._setup(local_env, editable_dir)

        with patch("builtins.input", return_value="a"):
            cmd_sync(file=str(local_env.toml_path))

        with open(local_env.toml_path, "rb") as f:
            config = tomllib.load(f)
        entry = config["skills"]["editable-skills"]
        assert entry["delta"] is True
        assert entry["epsilon"] is True
        assert entry["alpha"] is True

    def test_toml_remains_valid_after_ignore_all(self, local_env, editable_dir):
        """Toml is valid after ignoring all new skills."""
        self._setup(local_env, editable_dir)

        with patch("builtins.input", return_value="i"):
            cmd_sync(file=str(local_env.toml_path))

        with open(local_env.toml_path, "rb") as f:
            config = tomllib.load(f)
        entry = config["skills"]["editable-skills"]
        assert entry["delta"] is False
        assert entry["epsilon"] is False
