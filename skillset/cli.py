"""CLI for managing AI skills across projects."""

from typing import Annotated

import typer

from skillset.commands import (
    cmd_add,
    cmd_apply,
    cmd_clean,
    cmd_init,
    cmd_list,
    cmd_remove,
    cmd_sync,
    cmd_update,
)

app = typer.Typer(
    name="skillset",
    help="Manage AI skills across projects",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        from skillset import __version__

        print(f"skillset {__version__}")
        raise typer.Exit()


@app.callback()
def _main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version"),
    ] = None,
) -> None:
    """Manage AI skills across projects."""


@app.command("list")
def list_cmd(
    prune: Annotated[bool, typer.Option(help="Remove broken links")] = False,
) -> None:
    """List installed skills and commands."""
    cmd_list(prune=prune)


@app.command()
def add(
    repo: Annotated[str | None, typer.Argument(help="Repo in owner/repo format")] = None,
    global_: Annotated[
        bool,
        typer.Option("-g", "--global", help="Install skills globally"),
    ] = False,
    skill: Annotated[
        list[str] | None,
        typer.Option("-s", "--skill", help="Add only this skill by name (repeatable)"),
    ] = None,
    subpath: Annotated[
        str | None,
        typer.Option("-p", "--path", help="Subdirectory within the repo to use as root"),
    ] = None,
    copy: Annotated[
        bool,
        typer.Option("--copy", help="Copy files instead of symlinking (for Windows without admin)"),
    ] = False,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Clone to a temp dir, copy skills, then clean up"),
    ] = False,
    trial: Annotated[
        bool,
        typer.Option("--try", help="Install on trial basis (remove with 'clean')"),
    ] = False,
    interactive: Annotated[
        bool,
        typer.Option("-i", "--interactive", help="Select skills interactively with fzf"),
    ] = False,
) -> None:
    """Add skills from a GitHub repo. Installs locally if skillset.toml is found in path."""
    cmd_add(
        repo=repo,
        g=global_,
        skills=skill,
        subpath=subpath,
        copy=copy,
        no_cache=no_cache,
        trial=trial,
        interactive=interactive,
    )


@app.command()
def apply(
    file: Annotated[
        str | None,
        typer.Option(help="Path to skillset.toml"),
    ] = None,
    global_: Annotated[
        bool, typer.Option("-g", "--global", help="Apply global ~/.claude/skillset.toml")
    ] = False,
) -> None:
    """Install skills declared in skillset.toml. Uses local if found, otherwise global."""
    cmd_apply(file=file, g=global_)


@app.command()
def update(
    repo: Annotated[str | None, typer.Argument(help="Specific repo to update (optional)")] = None,
    global_: Annotated[bool, typer.Option("-g", "--global", help="Update global skills")] = False,
    copy: Annotated[bool, typer.Option("--copy", help="Copy files instead of symlinking")] = False,
    new: Annotated[
        bool, typer.Option("--new", help="Also link new skills/commands not currently linked")
    ] = False,
) -> None:
    """Update repo(s) and refresh links."""
    cmd_update(repo=repo, g=global_, copy=copy, new=new)


@app.command()
def init(
    global_: Annotated[
        bool, typer.Option("-g", "--global", help="Create global ~/.claude/skillset.toml")
    ] = False,
) -> None:
    """Create a skillset.toml file. Default: local at git root. --global for ~/.claude/."""
    cmd_init(g=global_)


@app.command()
def sync(
    file: Annotated[
        str | None,
        typer.Option(help="Path to skillset.toml"),
    ] = None,
    global_: Annotated[
        bool, typer.Option("-g", "--global", help="Sync global ~/.claude/skillset.toml")
    ] = False,
) -> None:
    """Sync skills from skillset.toml. Uses local if found, otherwise global."""
    cmd_sync(file=file, g=global_)


@app.command()
def clean(
    global_: Annotated[
        bool, typer.Option("-g", "--global", help="Clean global trial skills")
    ] = False,
) -> None:
    """Remove all trial skills."""
    cmd_clean(g=global_)


@app.command()
def remove(
    name: Annotated[
        str | None, typer.Argument(help="Skill name or glob pattern (e.g. bs-*)")
    ] = None,
    global_: Annotated[
        bool,
        typer.Option("-g", "--global", help="Remove from global skills"),
    ] = False,
    interactive: Annotated[
        bool,
        typer.Option("-i", "--interactive", help="Select skills to remove with fzf"),
    ] = False,
) -> None:
    """Remove a skill by name. Removes from local scope if skillset.toml is found in path."""
    cmd_remove(name=name, g=global_, interactive=interactive)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
