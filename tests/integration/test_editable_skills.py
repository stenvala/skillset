"""Integration tests for editable skill directories with selective skills.

Uses test fixture skills in tests/integration/fixtures/editable-skills/
with three skills: alpha, beta, gamma.
"""

import re
import shutil
import tomllib
from pathlib import Path
from unittest.mock import patch

import pytest

from skillset.commands import cmd_add, cmd_sync

FIXTURES = Path(__file__).parent / "fixtures" / "editable-skills"
ALL_SKILLS = {"alpha", "beta", "gamma"}


@pytest.fixture
def local_env(tmp_path, monkeypatch):
    """Isolated environment with a local skillset.toml (project scope)."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()

    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    monkeypatch.setattr("skillset.paths.get_git_root", lambda: project)
    monkeypatch.setattr("skillset.commands.find_skillset_root", lambda: project)

    (home / ".claude").mkdir(parents=True)
    (home / ".cache" / "skillset" / "repos").mkdir(parents=True)

    toml_path = project / "skillset.toml"
    toml_path.write_text("[skills]\n")

    return type(
        "Env",
        (),
        {
            "home": home,
            "project": project,
            "tmp": tmp_path,
            "toml_path": toml_path,
            "skills_dir": project / ".claude" / "skills",
        },
    )()


def _installed_skills(skills_dir: Path) -> set[str]:
    if not skills_dir.exists():
        return set()
    return {p.name for p in skills_dir.iterdir() if p.is_dir()}


def _remove_skill_from_toml(toml_path: Path, skill_name: str) -> None:
    """Remove a single skill entry from skillset.toml (multi-line or inline)."""
    content = toml_path.read_text()
    content = re.sub(
        rf"^{re.escape(skill_name)}\s*=\s*(true|false)\n",
        "",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(rf",\s*{re.escape(skill_name)}\s*=\s*(true|false)", "", content)
    content = re.sub(rf"{re.escape(skill_name)}\s*=\s*(true|false),\s*", "", content)
    toml_path.write_text(content)


class TestAddEditableWithSelection:
    """skillset add /path -e -s alpha — selective editable add."""

    def test_only_selected_skill_linked(self, local_env):
        cmd_add(repo=str(FIXTURES), editable=True, skills=["alpha"])

        assert _installed_skills(local_env.skills_dir) == {"alpha"}

    def test_toml_has_all_skills_listed(self, local_env):
        cmd_add(repo=str(FIXTURES), editable=True, skills=["alpha"])

        content = local_env.toml_path.read_text()
        assert "alpha = true" in content
        assert "beta = false" in content
        assert "gamma = false" in content

    def test_toml_has_editable_and_source(self, local_env):
        cmd_add(repo=str(FIXTURES), editable=True, skills=["alpha"])

        content = local_env.toml_path.read_text()
        assert "editable = true" in content
        assert f'source = "{FIXTURES}"' in content

    def test_multiple_selected(self, local_env):
        cmd_add(repo=str(FIXTURES), editable=True, skills=["alpha", "gamma"])

        assert _installed_skills(local_env.skills_dir) == {"alpha", "gamma"}
        content = local_env.toml_path.read_text()
        assert "alpha = true" in content
        assert "beta = false" in content
        assert "gamma = true" in content


class TestAddEditableAllSkills:
    """skillset add /path -e — add all, then toml lists every skill as true."""

    def test_all_skills_linked(self, local_env):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=str(FIXTURES), editable=True)

        assert ALL_SKILLS.issubset(_installed_skills(local_env.skills_dir))

    def test_toml_lists_all_as_true(self, local_env):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=str(FIXTURES), editable=True)

        content = local_env.toml_path.read_text()
        for skill in ALL_SKILLS:
            assert f"{skill} = true" in content


class TestSyncEditableSelective:
    """Sync respects skill selections in editable entries."""

    def test_sync_only_links_enabled(self, local_env):
        """Write toml manually with alpha=true, beta=false, gamma=true."""
        local_env.toml_path.write_text(
            f"[skills]\n"
            f'[skills."editable-skills"]\n'
            f"editable = true\n"
            f'source = "{FIXTURES}"\n'
            f"alpha = true\n"
            f"beta = false\n"
            f"gamma = true\n"
        )

        cmd_sync(file=str(local_env.toml_path))

        installed = _installed_skills(local_env.skills_dir)
        assert "alpha" in installed
        assert "gamma" in installed
        assert "beta" not in installed

    def test_sync_removes_disabled_skill(self, local_env):
        """If beta was previously linked, sync removes it when set to false."""
        # Pre-link beta
        local_env.skills_dir.mkdir(parents=True, exist_ok=True)
        (local_env.skills_dir / "beta").symlink_to(FIXTURES / "beta")

        local_env.toml_path.write_text(
            f"[skills]\n"
            f'[skills."editable-skills"]\n'
            f"editable = true\n"
            f'source = "{FIXTURES}"\n'
            f"alpha = true\n"
            f"beta = false\n"
            f"gamma = true\n"
        )

        cmd_sync(file=str(local_env.toml_path))

        assert not (local_env.skills_dir / "beta").exists()


class TestSyncEditableNewSkillPrompt:
    """After removing a skill entry from toml, sync detects it and prompts."""

    def _setup(self, local_env):
        """Add all editable skills, then remove gamma from toml."""
        cmd_add(repo=str(FIXTURES), editable=True, skills=["alpha", "beta"])

        content = local_env.toml_path.read_text()
        assert "alpha = true" in content
        assert "beta = true" in content
        assert "gamma = false" in content

        # Remove gamma entry — sync should detect it as new
        _remove_skill_from_toml(local_env.toml_path, "gamma")
        content = local_env.toml_path.read_text()
        assert "gamma" not in content

    def test_accept_new_skill(self, local_env, capsys):
        """User says 'y' — gamma gets linked and toml updated with true."""
        self._setup(local_env)

        with patch("builtins.input", return_value="y"):
            cmd_sync(file=str(local_env.toml_path))

        assert (local_env.skills_dir / "gamma").exists()
        content = local_env.toml_path.read_text()
        assert "gamma = true" in content

        output = capsys.readouterr().out
        assert "New skills detected" in output

    def test_reject_new_skill(self, local_env, capsys):
        """User says 'n' — gamma stays unlinked and toml updated with false."""
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
        skills_config = config["skills"]["editable-skills"]
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


class TestSyncNewSkillAddedToEditableDir:
    """New skills appear in the editable directory; sync offers a/i/s menu.

    Simulates the scenario where someone adds new skills to a shared
    editable skills repo and the user runs `skillset sync`.
    """

    @pytest.fixture
    def editable_dir(self, tmp_path):
        """Copy fixtures to a mutable dir and return it."""
        d = tmp_path / "editable-skills"
        shutil.copytree(FIXTURES, d)
        return d

    def _setup(self, local_env, editable_dir):
        """Install all three original skills, then add two new ones to the dir."""
        # Write toml with all three original skills tracked
        local_env.toml_path.write_text(
            f"[skills]\n"
            f'[skills."editable-skills"]\n'
            f"editable = true\n"
            f'source = "{editable_dir}"\n'
            f"alpha = true\n"
            f"beta = true\n"
            f"gamma = true\n"
        )

        # Initial sync to link the originals
        cmd_sync(file=str(local_env.toml_path))
        assert _installed_skills(local_env.skills_dir) == {"alpha", "beta", "gamma"}

        # Simulate upstream adding two new skills
        for name in ("delta", "epsilon"):
            skill_dir = editable_dir / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"# {name}\n")

    def test_add_all(self, local_env, editable_dir, capsys):
        """User chooses 'a' — both new skills linked and toml updated as true."""
        self._setup(local_env, editable_dir)

        with patch("builtins.input", return_value="a"):
            cmd_sync(file=str(local_env.toml_path))

        installed = _installed_skills(local_env.skills_dir)
        assert "delta" in installed
        assert "epsilon" in installed

        content = local_env.toml_path.read_text()
        assert "delta = true" in content
        assert "epsilon = true" in content

        output = capsys.readouterr().out
        assert "New skills detected" in output
        assert "2 new skill(s)" in output

    def test_ignore_all(self, local_env, editable_dir, capsys):
        """User chooses 'i' — neither new skill linked, toml updated as false."""
        self._setup(local_env, editable_dir)

        with patch("builtins.input", return_value="i"):
            cmd_sync(file=str(local_env.toml_path))

        installed = _installed_skills(local_env.skills_dir)
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

        # First call: menu → "s"; then "y" for delta, "n" for epsilon
        responses = iter(["s", "y", "n"])
        with patch("builtins.input", side_effect=responses):
            cmd_sync(file=str(local_env.toml_path))

        installed = _installed_skills(local_env.skills_dir)
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
