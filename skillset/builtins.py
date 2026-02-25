"""Built-in permission presets."""


def _perms(*commands: str) -> dict:
    """Create permissions dict allowing Bash for given commands."""
    return {"permissions": {"allow": [f"Bash({cmd} *)" for cmd in commands]}}


PRESETS: dict[str, dict] = {
    "developer": _perms(
        # unix essentials
        "cat", "head", "tail", "wc", "sort", "uniq", "cut", "tr",
        "find", "xargs", "diff", "sed", "awk",
        "ls", "tree", "file", "stat", "du", "df",
        "mkdir", "cp", "mv", "ln", "chmod", "touch",
        # version control & github
        "git", "gh",
        # node / js
        "npm", "npx", "yarn", "pnpm", "node",
        # python
        "uv", "pip", "python", "pytest", "ruff",
        # containers & orchestration
        "docker", "docker-compose",
        "kubectl", "helm",
        # build tools
        "make", "cargo", "go",
        # aws (read-only)
        "aws logs", "aws cloudwatch", "aws events",
    ),
}
