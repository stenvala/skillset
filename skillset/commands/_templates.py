"""Shared templates and constants for command handlers."""

GLOBAL_SKILLSET_TEMPLATE = """\
# Global skillset configuration (~/.claude/skillset.toml)
# Skills are installed to ~/.claude/skills/
#
# Examples:
#   "owner/repo" = true                                        # all skills from repo
#   "owner/repo" = {skill-a = true, skill-b = false}           # selective per skill
#   "owner/repo" = {path = "subdir"}                           # skills from subdirectory
#   "owner/repo" = {path = "sub", editable = true, source = "~/local/checkout"}
#
# Run 'skillset sync' to install/update skills.

[skills]
"""

LOCAL_SKILLSET_TEMPLATE = """\
# Project skillset configuration (skillset.toml)
# Skills are installed to .claude/skills/
#
# Examples:
#   "owner/repo" = true                                        # all skills from repo
#   "owner/repo" = {skill-a = true, skill-b = false}           # selective per skill
#   "owner/repo" = {path = "subdir"}                           # skills from subdirectory
#   "owner/repo" = {local = true}                              # install to project scope
#
# Run 'skillset apply' to install skills.

[skills]
"""

SYNC_META_KEYS = {"editable", "path", "source", "copy"}
