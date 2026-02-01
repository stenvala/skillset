"""Built-in permission presets."""


def _perms(*commands: str) -> dict:
    """Create permissions dict allowing Bash for given commands."""
    return {"permissions": {"allow": [f"Bash({cmd} *)" for cmd in commands]}}


PRESETS: dict[str, dict] = {
    "developer": _perms(
        "git", "gh",
        "npm", "npx", "yarn", "pnpm", "node",
        "uv", "pip", "python", "pytest", "ruff",
        "docker", "docker-compose",
        "kubectl", "helm",
        "make", "cargo", "go",
    ),
}
