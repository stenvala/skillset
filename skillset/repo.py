"""Git repository operations — clone, pull, parse specs."""

import subprocess
import tempfile
from pathlib import Path

from skillset.paths import get_cache_dir


def parse_repo_spec(spec: str) -> tuple[str, str]:
    """Parse 'owner/repo' into (owner, repo)."""
    parts = spec.strip().split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid repo format: {spec}. Use 'owner/repo'")
    return parts[0], parts[1]


def parse_github_url(url: str) -> tuple[str, str, str | None, str | None] | None:
    """Parse a GitHub tree URL into (owner, repo, branch, subpath) or None.

    Handles:
      https://github.com/owner/repo
      https://github.com/owner/repo/tree/branch/path/to/subdir
    """
    import re

    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+)(?:/(.+))?)?/?$", url)
    if not m:
        return None
    return m.group(1), m.group(2).removesuffix(".git"), m.group(3), m.group(4)


def get_repo_dir(owner: str, repo: str) -> Path:
    """Get the cache directory for a repo."""
    return get_cache_dir() / owner / repo


def clone_or_pull(owner: str, repo: str, ref: str | None = None) -> Path:
    """Clone repo if not exists, or pull if it does. Returns repo path.

    If ref is set, checks out that branch/tag/sha after cloning or fetching.
    """
    repo_dir = get_repo_dir(owner, repo)
    https_url = f"https://github.com/{owner}/{repo}.git"
    ssh_url = f"git@github.com:{owner}/{repo}.git"

    if repo_dir.exists():
        label = f"{owner}/{repo}" + (f"@{ref}" if ref else "")
        print(f"Updating {label}...")
        try:
            subprocess.run(
                ["git", "fetch", "--all", "--tags", "--prune"],
                cwd=repo_dir,
                check=True,
                capture_output=True,
            )
            if ref:
                _checkout_ref(repo_dir, ref)
            else:
                subprocess.run(["git", "pull"], cwd=repo_dir, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else ""
            stdout = e.stdout.decode() if e.stdout else ""
            msg = stderr or stdout or "(no output)"
            print(f"Warning: git update failed in {repo_dir}:\n{msg}")
    else:
        print(f"Cloning {owner}/{repo}...")
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["git", "clone", https_url, str(repo_dir)], check=True, capture_output=True
            )
        except subprocess.CalledProcessError as e:
            # If HTTPS fails (e.g., auth failed for private repo), try SSH
            stderr = e.stderr.decode() if e.stderr else ""
            if "Authentication failed" in stderr or e.returncode == 128:
                print("HTTPS failed, trying SSH...")
                subprocess.run(
                    ["git", "clone", ssh_url, str(repo_dir)], check=True, capture_output=True
                )
            else:
                raise
        if ref:
            _checkout_ref(repo_dir, ref)

    return repo_dir


def _checkout_ref(repo_dir: Path, ref: str) -> None:
    """Check out ref and fast-forward if it tracks a remote branch."""
    subprocess.run(["git", "checkout", ref], cwd=repo_dir, check=True, capture_output=True)
    # No-op for detached HEAD (tags/SHAs); fast-forwards a tracking branch.
    subprocess.run(
        ["git", "merge", "--ff-only"],
        cwd=repo_dir,
        check=False,
        capture_output=True,
    )


def clone_to_temp(owner: str, repo: str, ref: str | None = None) -> Path:
    """Clone repo to a temp directory (caller must clean up). Returns repo path."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="skillset-"))
    repo_dir = tmp_dir / repo
    https_url = f"https://github.com/{owner}/{repo}.git"
    ssh_url = f"git@github.com:{owner}/{repo}.git"

    label = f"{owner}/{repo}" + (f"@{ref}" if ref else "")
    print(f"Cloning {label} (no-cache)...")
    clone_args = ["git", "clone", "--depth", "1"]
    if ref:
        clone_args += ["--branch", ref]
    try:
        subprocess.run(
            [*clone_args, https_url, str(repo_dir)],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if e.stderr else ""
        if "Authentication failed" in stderr or e.returncode == 128:
            print("HTTPS failed, trying SSH...")
            subprocess.run(
                [*clone_args, ssh_url, str(repo_dir)],
                check=True,
                capture_output=True,
            )
        else:
            raise
    return repo_dir
