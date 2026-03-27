# skillset

Manage AI skills and permissions across projects for Claude Code.

## Install

```bash
uv tool install skillset
```

Or with pip:

```bash
pip install skillset
```

## Usage

### Allow permission presets

```bash
skillset allow              # apply developer preset (default)
skillset allow python git   # apply specific presets
```

Built-in presets: `developer`, `git`, `node`, `python`, `docker`, `k8s`

### Add skills from GitHub

```bash
skillset add owner/repo         # add to global ~/.claude/skills/
skillset add owner/repo --local # add to project .claude/skills/
skillset add --interactive      # select skills with fzf
```

### Try skills temporarily

```bash
skillset add --try owner/repo    # install as trial
skillset list                    # trial skills shown with (trial) tag
skillset clean                   # remove all trial skills and their cached repos
skillset add owner/repo          # re-add without --try to keep permanently
```

### Remove skills

```bash
skillset remove skill-name          # remove from global skills
skillset remove skill-name --local  # remove from project skills
skillset remove --interactive       # select skills to remove with fzf
```

### List installed skills

```bash
skillset list           # list all installed skills
skillset list --prune   # list and remove broken links
```

### Declarative setup with skillset.toml

Declare all skills and symlinks in a `skillset.toml` file and apply in one command:

```toml
[skills]
"owner/claude-skills" = ["commit", "review-pr"]  # specific skills
"owner/tools" = true                              # all skills
"myorg/internal" = { skills = ["auth"], local = true }  # project-scoped

[links]
"specs" = "../project-docs/specs"  # create local symlink → sibling repo path
```

```bash
skillset apply            # apply ./skillset.toml
skillset apply --file path/to/skillset.toml
```

`[links]` creates symlinks for cross-repo paths (e.g. shared specs from a sibling repo). Warns if a link target is not in `.gitignore`.

### Update cached repos

```bash
skillset update             # pull all cached repos
skillset update owner/repo  # update specific repo
```

### Prerequisites

`fzf` is required for `--interactive` mode (`skillset add -i`, `skillset remove -i`).

## How it works

- Permissions are written to `.claude/settings.local.json` (project-local, not committed)
- Skills are symlinked (Linux/Mac) or junctioned (Windows) from cached repos
- Repo cache in `~/.cache/skillset/repos/`

## Comparison with Vercel's `npx skills`

Vercel's [`skills`](https://github.com/vercel-labs/skills) CLI is a cross-agent package manager with a central registry at [skills.sh](https://skills.sh). Both tools manage SKILL.md-based skills from GitHub repos, but they differ in scope and focus.

| | **skillset** | **Vercel `npx skills`** |
|---|---|---|
| Target agents | Claude Code | 40+ (Claude, Cursor, Codex, Copilot…) |
| Permission management | Yes — presets, `settings.local.json` | No |
| Slash commands | Links `/commands` from repos | No |
| Skill discovery | Browse repos with fzf | Central registry (89K+ skills) |
| Install method | `pip` / `uv tool install` / `uvx` | `npx` |
| Scope default | Global | Project |

**skillset** is a Claude Code power-user tool that manages both skills and permissions. Vercel's CLI is a cross-agent marketplace with no permission management. The two are complementary — discover skills via Vercel's registry, install them with proper permissions via skillset.

## License

MIT
