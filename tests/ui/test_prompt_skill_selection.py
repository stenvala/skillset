"""Tests for skillset.ui.prompt_skill_selection."""

from unittest.mock import patch

from skillset.ui import prompt_skill_selection


def test_add_all(tmp_path):
    skills = [tmp_path / "skill-a", tmp_path / "skill-b"]
    for s in skills:
        s.mkdir(parents=True)

    with patch("builtins.input", return_value="y"):
        filter_set, selections = prompt_skill_selection(skills)

    assert filter_set is None
    assert selections is None


def test_select_individual(tmp_path):
    skills = [tmp_path / "skill-a", tmp_path / "skill-b"]
    for s in skills:
        s.mkdir(parents=True)

    with patch("builtins.input", side_effect=["s", "y", "n"]):
        filter_set, selections = prompt_skill_selection(skills)

    assert "skill-a" in filter_set
    assert "skill-b" not in filter_set
    assert selections == {"skill-a": True, "skill-b": False}


def test_default_adds_all(tmp_path):
    skills = [tmp_path / "skill-a"]
    skills[0].mkdir(parents=True)

    with patch("builtins.input", return_value=""):
        filter_set, selections = prompt_skill_selection(skills)

    assert filter_set is None
    assert selections is None
