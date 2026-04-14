"""Integration tests using vivainio/agent-skills repository.

These tests exercise the full add and sync workflows against the real GitHub repo.
They require network access and will clone/pull vivainio/agent-skills.
"""

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from skillset.commands import cmd_add, cmd_sync

REPO = "vivainio/agent-skills"

# Known skills in vivainio/agent-skills/skills/ (update if repo changes)
MAIN_SKILLS = {
    "chat-transcript",
    "github-release",
    "public-github",
    "python-project",
    "tasks-py",
    "zaira",
}
EXTRA_SKILLS = {"mspec", "vp-code-review", "zipget"}


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Isolated environment with redirected home and project dirs."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()

    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    monkeypatch.setattr("skillset.paths.get_git_root", lambda: project)
    monkeypatch.setattr("skillset.commands.find_skillset_root", lambda: None)

    (home / ".claude").mkdir(parents=True)
    (home / ".cache" / "skillset" / "repos").mkdir(parents=True)

    return type("Env", (), {"home": home, "project": project, "tmp": tmp_path})()


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

    # Create local skillset.toml
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
        },
    )()


class TestAddAllSkills:
    """skillset add vivainio/agent-skills — all skills from repo."""

    def test_add_all_skills(self, env, capsys):
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


class TestAddGlobalForce:
    """skillset add vivainio/agent-skills -g — force global install."""

    def test_global_flag_installs_to_global_dir(self, local_env, capsys):
        """With -g, skills go to global dir even when local skillset.toml exists."""
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=REPO, g=True)

        global_skills = local_env.home / ".claude" / "skills"
        installed = {p.name for p in global_skills.iterdir() if p.is_dir()}
        assert MAIN_SKILLS.issubset(installed)

        # Should NOT be in project skills
        local_skills = local_env.project / ".claude" / "skills"
        assert not local_skills.exists() or not any(local_skills.iterdir())


class TestAddSingleSkill:
    """skillset add vivainio/agent-skills -s zaira — only the zaira skill."""

    def test_only_zaira_linked(self, env, capsys):
        cmd_add(repo=REPO, skills=["zaira"])

        skills_dir = env.home / ".claude" / "skills"
        installed = {p.name for p in skills_dir.iterdir() if p.is_dir()}
        assert "zaira" in installed
        assert installed == {"zaira"}, f"Expected only zaira, got {installed}"

    def test_zaira_is_symlink(self, env, capsys):
        cmd_add(repo=REPO, skills=["zaira"])

        skills_dir = env.home / ".claude" / "skills"
        assert (skills_dir / "zaira").is_symlink()

    def test_zaira_has_skill_md(self, env, capsys):
        cmd_add(repo=REPO, skills=["zaira"])

        skills_dir = env.home / ".claude" / "skills"
        assert (skills_dir / "zaira" / "SKILL.md").exists()


class TestAddMultipleSkills:
    """skillset add vivainio/agent-skills -s zaira -s public-github — multiple specific skills."""

    def test_only_selected_skills_linked(self, env, capsys):
        cmd_add(repo=REPO, skills=["zaira", "public-github"])

        skills_dir = env.home / ".claude" / "skills"
        installed = {p.name for p in skills_dir.iterdir() if p.is_dir()}
        assert installed == {"zaira", "public-github"}

    def test_output_mentions_linked_count(self, env, capsys):
        cmd_add(repo=REPO, skills=["zaira", "public-github"])

        output = capsys.readouterr().out
        assert "Linked 2 skill(s)" in output


class TestAddFromSubpath:
    """skillset add vivainio/agent-skills -p extra-skills — skills from subdirectory."""

    def test_subpath_installs_extra_skills(self, env, capsys):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=REPO, subpath="extra-skills")

        skills_dir = env.home / ".claude" / "skills"
        installed = {p.name for p in skills_dir.iterdir() if p.is_dir()}
        assert EXTRA_SKILLS.issubset(installed), f"Missing: {EXTRA_SKILLS - installed}"

    def test_subpath_does_not_install_main_skills(self, env, capsys):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=REPO, subpath="extra-skills")

        skills_dir = env.home / ".claude" / "skills"
        installed = {p.name for p in skills_dir.iterdir() if p.is_dir()}
        assert not (MAIN_SKILLS & installed), (
            f"Main skills should not be installed: {MAIN_SKILLS & installed}"
        )


class TestAddWithGitHubUrl:
    """skillset add https://github.com/vivainio/agent-skills."""

    def test_full_url(self, env, capsys):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo="https://github.com/vivainio/agent-skills")

        skills_dir = env.home / ".claude" / "skills"
        installed = {p.name for p in skills_dir.iterdir() if p.is_dir()}
        assert MAIN_SKILLS.issubset(installed)

    def test_url_with_tree_subpath(self, env, capsys):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo="https://github.com/vivainio/agent-skills/tree/main/extra-skills")

        skills_dir = env.home / ".claude" / "skills"
        installed = {p.name for p in skills_dir.iterdir() if p.is_dir()}
        assert EXTRA_SKILLS.issubset(installed)


class TestAddCopyMode:
    """skillset add vivainio/agent-skills --copy."""

    def test_copy_creates_real_dirs(self, env, capsys):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=REPO, copy=True)

        skills_dir = env.home / ".claude" / "skills"
        for skill in MAIN_SKILLS:
            skill_dir = skills_dir / skill
            if skill_dir.exists():
                assert skill_dir.is_dir()
                assert not skill_dir.is_symlink()

    def test_copy_output_says_copied(self, env, capsys):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=REPO, copy=True)

        output = capsys.readouterr().out
        assert "Copied" in output


class TestAddLocalScope:
    """Tests that add writes selections to local skillset.toml."""

    def test_single_skill_writes_to_local_toml(self, local_env, capsys):
        cmd_add(repo=REPO, skills=["zaira"])

        content = local_env.toml_path.read_text()
        assert f'"{REPO}"' in content
        assert "zaira = true" in content

    def test_single_skill_marks_others_false(self, local_env, capsys):
        cmd_add(repo=REPO, skills=["zaira"])

        content = local_env.toml_path.read_text()
        # All other main skills should be marked false
        for skill in MAIN_SKILLS - {"zaira"}:
            assert f"{skill} = false" in content, f"{skill} should be false in toml"

    def test_skills_installed_to_project_dir(self, local_env, capsys):
        cmd_add(repo=REPO, skills=["zaira"])

        project_skills = local_env.project / ".claude" / "skills"
        assert (project_skills / "zaira").exists()

    def test_multiple_skills_written_to_toml(self, local_env, capsys):
        cmd_add(repo=REPO, skills=["zaira", "public-github"])

        content = local_env.toml_path.read_text()
        assert "zaira = true" in content
        assert "public-github = true" in content
        for skill in MAIN_SKILLS - {"zaira", "public-github"}:
            assert f"{skill} = false" in content

    def test_all_skills_no_selection_dict(self, local_env, capsys):
        """When adding all skills (no -s), toml gets simple true entry."""
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=REPO)

        content = local_env.toml_path.read_text()
        assert f'"{REPO}"' in content


class TestAddTrial:
    """skillset add --try vivainio/agent-skills."""

    def test_trial_does_not_write_to_toml(self, local_env, capsys):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=REPO, trial=True)

        content = local_env.toml_path.read_text()
        assert f'"{REPO}"' not in content

    def test_trial_still_links_skills(self, local_env, capsys):
        with patch("builtins.input", return_value="y"):
            cmd_add(repo=REPO, trial=True)

        project_skills = local_env.project / ".claude" / "skills"
        installed = {p.name for p in project_skills.iterdir() if p.is_dir()}
        assert MAIN_SKILLS.issubset(installed)


def _remove_skill_from_toml(toml_path: Path, skill_name: str) -> None:
    """Remove a single skill entry from skillset.toml (inline or multi-line)."""
    content = toml_path.read_text()
    # Multi-line: remove "skill_name = true/false\n" on its own line
    pattern = rf"^{re.escape(skill_name)}\s*=\s*(true|false)\n"
    content = re.sub(pattern, "", content, flags=re.MULTILINE)
    # Inline: remove ", skill_name = true/false" or "skill_name = true/false, "
    content = re.sub(rf",\s*{re.escape(skill_name)}\s*=\s*(true|false)", "", content)
    content = re.sub(rf"{re.escape(skill_name)}\s*=\s*(true|false),\s*", "", content)
    toml_path.write_text(content)


class TestSyncDetectsRemovedSkill:
    """After add -s zaira, remove a skill from toml, then sync detects it as new."""

    REMOVED_SKILL = "public-github"

    def _setup_and_remove(self, local_env):
        """Add zaira, then remove public-github entry from toml."""
        cmd_add(repo=REPO, skills=["zaira"])

        # Verify the toml has the removed skill before we edit
        content = local_env.toml_path.read_text()
        assert f"{self.REMOVED_SKILL} = false" in content

        # Remove the skill entry from toml
        _remove_skill_from_toml(local_env.toml_path, self.REMOVED_SKILL)

        # Verify it's gone
        content = local_env.toml_path.read_text()
        assert self.REMOVED_SKILL not in content

        # Verify zaira is still there
        assert "zaira = true" in content

    def test_sync_accept_new_skill(self, local_env, capsys):
        """User says 'y' to new skill: it gets linked and toml updated with true."""
        self._setup_and_remove(local_env)

        with patch("builtins.input", return_value="y"):
            cmd_sync(file=str(local_env.toml_path))

        # Skill should be linked
        project_skills = local_env.project / ".claude" / "skills"
        assert (project_skills / self.REMOVED_SKILL).exists()

        # Toml should have the skill as true
        content = local_env.toml_path.read_text()
        assert f"{self.REMOVED_SKILL} = true" in content

        output = capsys.readouterr().out
        assert "New skills detected" in output
        assert self.REMOVED_SKILL in output

    def test_sync_reject_new_skill(self, local_env, capsys):
        """User says 'n' to new skill: it stays unlinked and toml updated with false."""
        self._setup_and_remove(local_env)

        with patch("builtins.input", return_value="n"):
            cmd_sync(file=str(local_env.toml_path))

        # Skill should NOT be linked
        project_skills = local_env.project / ".claude" / "skills"
        assert not (project_skills / self.REMOVED_SKILL / "SKILL.md").exists()

        # Toml should have the skill as false
        content = local_env.toml_path.read_text()
        assert f"{self.REMOVED_SKILL} = false" in content

        output = capsys.readouterr().out
        assert "New skills detected" in output
        assert f"{self.REMOVED_SKILL}" in output
        assert "skipped" in output

    def test_sync_accept_links_skill_with_content(self, local_env, capsys):
        """Accepted skill has actual SKILL.md content from the repo."""
        self._setup_and_remove(local_env)

        with patch("builtins.input", return_value="y"):
            cmd_sync(file=str(local_env.toml_path))

        skill_md = local_env.project / ".claude" / "skills" / self.REMOVED_SKILL / "SKILL.md"
        assert skill_md.exists()
        content = skill_md.read_text()
        assert len(content) > 0

    def test_sync_preserves_existing_skills(self, local_env, capsys):
        """Sync keeps zaira linked regardless of the new skill decision."""
        self._setup_and_remove(local_env)

        with patch("builtins.input", return_value="n"):
            cmd_sync(file=str(local_env.toml_path))

        # zaira should still be linked
        project_skills = local_env.project / ".claude" / "skills"
        assert (project_skills / "zaira").exists()

    def test_sync_toml_remains_valid(self, local_env, capsys):
        """After sync updates the toml, it should still be valid TOML."""
        import tomllib

        self._setup_and_remove(local_env)

        with patch("builtins.input", return_value="y"):
            cmd_sync(file=str(local_env.toml_path))

        with open(local_env.toml_path, "rb") as f:
            config = tomllib.load(f)
        assert REPO in config.get("skills", {})
