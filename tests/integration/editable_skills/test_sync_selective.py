"""Sync respects skill selections in editable entries."""

from skillset.commands import cmd_sync

from .conftest import FIXTURES, installed_skills


class TestSyncEditableSelective:
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

        installed = installed_skills(local_env.skills_dir)
        assert "alpha" in installed
        assert "gamma" in installed
        assert "beta" not in installed

    def test_sync_removes_disabled_skill(self, local_env):
        """If beta was previously linked, sync removes it when set to false."""
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
