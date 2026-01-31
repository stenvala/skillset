"""Built-in permission presets."""


def _perms(*commands: str) -> dict:
    """Create permissions dict allowing Bash for given commands."""
    return {"permissions": {"allow": [f"Bash({cmd} *)" for cmd in commands]}}


PRESETS: dict[str, dict] = {
    "developer": _perms("git", "gh", "npm", "npx", "yarn", "pnpm", "uv", "pip", "python", "node", "make", "cargo", "go"),
    "node": _perms("npm", "npx", "yarn", "pnpm", "node"),
    "python": _perms("uv", "pip", "python", "pytest", "ruff"),
    "docker": _perms("docker", "docker-compose"),
    "k8s": _perms("kubectl", "helm"),
}
