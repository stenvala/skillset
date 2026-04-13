"""Skill and command discovery — find SKILL.md and commands/ in repos."""

from pathlib import Path


def find_skills(repo_dir: Path) -> list[Path]:
    """Find skill directories in a repo. A skill is a dir containing SKILL.md."""
    skills = []
    for skill_file in repo_dir.glob("**/SKILL.md"):
        if any(part.startswith(".") for part in skill_file.relative_to(repo_dir).parts):
            continue
        skill_dir = skill_file.parent
        if skill_dir not in skills:
            skills.append(skill_dir)
    return skills


def find_commands(repo_dir: Path) -> list[Path]:
    """Find command files in a repo. Commands are .md files in commands/ directories (nested ok)."""
    commands = []
    for cmd_file in repo_dir.glob("**/commands/**/*.md"):
        if any(part.startswith(".") for part in cmd_file.relative_to(repo_dir).parts):
            continue
        commands.append(cmd_file)
    # Also check direct children of commands/
    for cmd_file in repo_dir.glob("**/commands/*.md"):
        if any(part.startswith(".") for part in cmd_file.relative_to(repo_dir).parts):
            continue
        if cmd_file not in commands:
            commands.append(cmd_file)
    return commands
