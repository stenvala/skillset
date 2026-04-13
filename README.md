# skillset

Manage AI skills across projects for Claude Code.

## Install

```bash
uv tool install skillset
```

Or with pip:

```bash
pip install skillset
```

### Install as developer

```bash
uv tool install . -e
```

## Usage

By default, commands detect scope automatically: if a `skillset.toml` is found in the current directory or any parent, skills install to the project (`.claude/skills/`). Otherwise, they install globally (`~/.claude/skills/`). Use `-g` / `--global` to force global scope.

### Add skills from GitHub

```bash
skillset add vivainio/agent-skills                    # all skills from repo
skillset add vivainio/agent-skills -g                 # force global install even if local skillset.toml file is found
skillset add vivainio/agent-skills -s zaira           # only the zaira skill
skillset add vivainio/agent-skills -s zaira -s other  # multiple specific skills
skillset add vivainio/agent-skills -p extra-skills    # skills from extra-skills/ subdirectory only
```

You can also pass a full GitHub URL:

```bash
skillset add https://github.com/vivainio/agent-skills
skillset add https://github.com/vivainio/agent-skills/tree/main/extra-skills
```

### Copy instead of symlink

```bash
skillset add vivainio/agent-skills --copy       # copy files instead of symlinking
skillset add vivainio/agent-skills --no-cache   # clone to temp dir, copy, then clean up
```

`--copy` is useful on Windows without admin privileges. `--no-cache` avoids keeping a local clone.

### Add editable skills from a local path

```bash
skillset add /path/to/skills-dir -e              # all editable skills from dir
skillset add /path/to/skills-dir -e -s zaira     # specific editable skill
skillset add zaira -e                            # look up in registered editable sources
```

Editable skills link directly from a local directory (no cache). The source is registered in `~/.claude/skillset.toml` so `skillset sync` can find it later. Once a source is registered, you can add individual skills by name with `-e`.

### Try skills temporarily

```bash
skillset add --try vivainio/agent-skills    # install as trial
skillset list                               # trial skills shown with (trial) tag
skillset clean                              # remove all trial skills and their cached repos
skillset clean -g                           # clean global trial skills
skillset add vivainio/agent-skills          # re-add without --try to keep permanently
```

### Remove skills

```bash
skillset remove zaira          # remove from detected scope (local or global)
skillset remove zaira -g       # remove from global skills
skillset remove "ai-*"         # glob patterns supported
```

### List installed skills

```bash
skillset list           # list all installed skills, commands, and cached repos
skillset list --prune   # also remove broken links
```

### Initialize skillset.toml

```bash
skillset init           # create skillset.toml at git root (local)
skillset init -g        # create ~/.claude/skillset.toml (global)
```

### Sync (global skillset.toml)

Manage your global skills declaratively with `~/.claude/skillset.toml`:

```toml
[skills]
# all skills from repo
"vivainio/agent-skills" = true

# selective: enable zaira, disable others explicitly
"vivainio/agent-skills" = {zaira = true, some-other = false}

# skills from a subdirectory
"vivainio/agent-skills" = {path = "extra-skills"}

# copy files instead of symlinking
"vivainio/agent-skills" = {copy = true}

# editable: point to a local checkout instead of cache
"vivainio/agent-skills" = {path = "extra-skills", editable = true, source = "~/repos/agent-skills"}
```

```bash
skillset sync                          # sync local skillset.toml if found, otherwise global
skillset sync -g                       # force sync global ~/.claude/skillset.toml
skillset sync --file path/to/skillset.toml  # sync a specific file
```

`sync` pulls each repo, links skills marked `true`, removes those marked `false`, and reports any new skills in the repo that aren't yet listed in your toml.

**Editable skills** point to a local checkout instead of the cache. Set `editable = true` with `source` pointing to the local path. Use `path` to select a subdirectory within it.

### Apply (project skillset.toml)

Declare project-scoped skills and symlinks in a `skillset.toml` file in your repo:

```toml
[skills]
"vivainio/agent-skills" = true                                         # all skills
"vivainio/agent-skills" = {skills = ["zaira"], local = true}           # specific skills, project scope
"vivainio/agent-skills" = {path = "extra-skills"}                      # from subdirectory

[links]
"specs" = "../project-docs/specs"  # create local symlink → sibling repo path
```

```bash
skillset apply                          # apply local skillset.toml if found, otherwise global
skillset apply -g                       # force apply global ~/.claude/skillset.toml
skillset apply --file path/to/skillset.toml  # apply a specific file
```

`[links]` creates symlinks for cross-repo paths (e.g. shared specs from a sibling repo). Warns if a link target is not in `.gitignore`.

### Update cached repos

```bash
skillset update                              # pull all cached repos and refresh links
skillset update vivainio/agent-skills        # update a specific repo
skillset update --copy                       # refresh as copies instead of symlinks
skillset update --new                        # also link new skills not previously installed
skillset update -g                           # update global skills
```

By default, `update` only refreshes skills that are already linked. Use `--new` to also pick up new skills added to the repo since the last install.

## How it works

- Skills are symlinked (Linux/Mac) or junctioned (Windows) from cached repos
- Repo cache in `~/.cache/skillset/repos/`

## Comparison with Vercel's `npx skills`

Vercel's [`skills`](https://github.com/vercel-labs/skills) CLI is a cross-agent package manager with a central registry at [skills.sh](https://skills.sh). Both tools manage SKILL.md-based skills from GitHub repos, but they differ in scope and focus.

|                 | **skillset**                           | **Vercel `npx skills`**               |
| --------------- | -------------------------------------- | ------------------------------------- |
| Target agents   | Claude Code                            | 40+ (Claude, Cursor, Codex, Copilot…) |
| Slash commands  | Links `/commands` from repos           | No                                    |
| Skill discovery | n/a                                    | Central registry (89K+ skills)        |
| Install method  | `pip` / `uv tool install` / `uvx`      | `npx`                                 |
| Scope default   | Project if available, Global otherwise | Project                               |

**skillset** is a Claude Code power-user tool for managing skills. Vercel's CLI is a cross-agent marketplace. The two are complementary — discover skills via Vercel's registry, install and manage them via skillset.

## License

MIT
