"""Command handlers -- dispatched from cli.py."""

from skillset.commands.add import cmd_add, cmd_init
from skillset.commands.list import cmd_list
from skillset.commands.remove import cmd_clean, cmd_remove
from skillset.commands.sync import cmd_sync
from skillset.commands.update import cmd_apply, cmd_update

__all__ = [
    "cmd_add",
    "cmd_apply",
    "cmd_clean",
    "cmd_init",
    "cmd_list",
    "cmd_remove",
    "cmd_sync",
    "cmd_update",
]
