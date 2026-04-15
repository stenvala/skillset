"""skillset add /path -e -s alpha -- selective editable add."""

from skillset.commands import cmd_add

from .conftest import FIXTURES, installed_skills


class TestAddEditableWithSelection:
    def test_only_selected_skill_linked(self, local_env):
        cmd_add(repo=str(FIXTURES), skills=["alpha"])

        assert installed_skills(local_env.skills_dir) == {"alpha"}

    def test_toml_has_all_skills_listed(self, local_env):
        cmd_add(repo=str(FIXTURES), skills=["alpha"])

        content = local_env.toml_path.read_text()
        assert "alpha = true" in content
        assert "beta = false" in content
        assert "gamma = false" in content

    def test_toml_has_editable_and_source(self, local_env):
        cmd_add(repo=str(FIXTURES), skills=["alpha"])

        content = local_env.toml_path.read_text()
        assert "editable = true" in content
        assert f'source = "{FIXTURES}"' in content

    def test_multiple_selected(self, local_env):
        cmd_add(repo=str(FIXTURES), skills=["alpha", "gamma"])

        assert installed_skills(local_env.skills_dir) == {"alpha", "gamma"}
        content = local_env.toml_path.read_text()
        assert "alpha = true" in content
        assert "beta = false" in content
        assert "gamma = true" in content
