"""Skillset - Manage AI skills and permissions across projects."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("skillset")
except PackageNotFoundError:
    __version__ = "0.0.0"
