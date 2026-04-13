"""CLI for managing AI skills and permissions across projects."""

import argparse

from skillset.commands import (
    cmd_add,
    cmd_allow,
    cmd_apply,
    cmd_clean,
    cmd_init,
    cmd_list,
    cmd_remove,
    cmd_sync,
    cmd_update,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="skillset",
        description="Manage AI skills and permissions across projects",
    )
    from skillset import __version__

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = subparsers.add_parser("list", help="list installed skills")
    p_list.add_argument("--prune", action="store_true", help="remove broken links")

    # allow
    p_apply = subparsers.add_parser("allow", help="allow permission presets")
    p_apply.add_argument("presets", nargs="*", help="preset name(s) to allow (default: developer)")

    # add
    p_add = subparsers.add_parser("add", help="add skills from a GitHub repo")
    p_add.add_argument("repo", nargs="?", help="repo in owner/repo format")
    p_add.add_argument(
        "-l", "--local", dest="local", action="store_true", help="install skills in project scope"
    )
    p_add.add_argument(
        "-i", "--interactive", action="store_true", help="select skills interactively with fzf"
    )
    p_add.add_argument(
        "-s",
        "--skill",
        dest="skills",
        metavar="SKILL",
        action="append",
        help="add only this skill by name (can be repeated)",
    )
    p_add.add_argument(
        "-p",
        "--path",
        dest="subpath",
        metavar="PATH",
        help="subdirectory within the repo to use as root",
    )
    p_add.add_argument(
        "--copy",
        action="store_true",
        help="copy files instead of symlinking (for Windows without admin)",
    )
    p_add.add_argument(
        "--no-cache",
        dest="no_cache",
        action="store_true",
        help="clone to a temp dir, copy skills, then clean up (no persistent repo cache)",
    )
    p_add.add_argument(
        "-e",
        "--editable",
        action="store_true",
        help="add from a local editable path (or look up skill name in registered sources)",
    )
    p_add.add_argument(
        "--try",
        dest="trial",
        action="store_true",
        help="install skills on a trial basis (remove later with 'skillset clean')",
    )

    # apply
    p_apply_cmd = subparsers.add_parser("apply", help="install skills declared in skills.toml")
    p_apply_cmd.add_argument(
        "--file", metavar="PATH", help="path to skillset.toml (default: ./skillset.toml)"
    )

    # update
    p_update = subparsers.add_parser("update", help="update repo(s) and refresh links")
    p_update.add_argument("repo", nargs="?", help="specific repo to update (optional)")
    p_update.add_argument(
        "-g", "--global", dest="g", action="store_true", help="update global skills"
    )
    p_update.add_argument(
        "--copy",
        action="store_true",
        help="copy files instead of symlinking (for Windows without admin)",
    )
    p_update.add_argument(
        "--new", action="store_true", help="also link new skills/commands not currently linked"
    )

    # init
    p_init = subparsers.add_parser("init", help="create a skillset.toml file")
    p_init.add_argument("scope", choices=["global"], help="scope (global)")

    # sync
    p_sync = subparsers.add_parser("sync", help="sync skills from global skillset.toml")
    p_sync.add_argument(
        "--file", metavar="PATH", help="path to skillset.toml (default: ~/.claude/skillset.toml)"
    )

    # clean
    subparsers.add_parser("clean", help="remove all trial skills")

    # remove
    p_remove = subparsers.add_parser("remove", help="remove a skill by name")
    p_remove.add_argument("name", nargs="?", help="skill name or glob pattern (e.g. bs-*)")
    p_remove.add_argument(
        "-l", "--local", dest="local", action="store_true", help="remove from project skills"
    )
    p_remove.add_argument(
        "-i", "--interactive", action="store_true", help="select skills to remove with fzf"
    )

    args = parser.parse_args()

    handlers = {
        "list": cmd_list,
        "allow": cmd_allow,
        "add": cmd_add,
        "apply": cmd_apply,
        "update": cmd_update,
        "init": cmd_init,
        "sync": cmd_sync,
        "clean": cmd_clean,
        "remove": cmd_remove,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
