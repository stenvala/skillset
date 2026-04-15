"""Shared templates and constants for command handlers."""

GLOBAL_SKILLSET_TEMPLATE = """\
# Global skillset configuration (~/.claude/skillset.toml)
# Skills are installed to ~/.claude/skills/
#
# Each entry is a sub-table keyed by "owner/repo":
#
#   [skills."owner/repo"]
#   enabled = ["*"]                         # link every skill in the repo
#
#   [skills."owner/repo"]
#   enabled = ["skill-a", "skill-b"]        # link only these
#   disabled = ["skill-c"]                  # explicitly skip (sync won't re-prompt)
#
#   [skills."owner/repo"]
#   path = "subdir"                         # skills live in a subdirectory
#   editable = true                         # source is a local checkout
#   source = "~/code/my-skills"
#   enabled = ["*"]
#
# Run 'skillset sync' to install/update skills.

[skills]
"""

LOCAL_SKILLSET_TEMPLATE = """\
# Project skillset configuration (skillset.toml)
# Skills are installed to .claude/skills/
#
# Each entry is a sub-table keyed by "owner/repo":
#
#   [skills."owner/repo"]
#   enabled = ["*"]                         # link every skill in the repo
#
#   [skills."owner/repo"]
#   enabled = ["skill-a", "skill-b"]        # link only these
#   disabled = ["skill-c"]                  # explicitly skip (sync won't re-prompt)
#
#   [skills."owner/repo"]
#   path = "subdir"                         # skills live in a subdirectory
#
# Run 'skillset sync' to install skills.

[skills]
"""
