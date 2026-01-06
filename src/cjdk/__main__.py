# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT
from __future__ import annotations

import os
import subprocess
import sys

import click

from . import __version__, _api
from ._exceptions import CjdkError

__all__ = [
    "main",
]


@click.group()
@click.pass_context
@click.option(
    "--jdk",
    "-j",
    metavar="VENDOR:VERSION",
    help="Specify JDK vendor and version.",
)
@click.option(
    "--cache-dir", metavar="DIR", help="Override root cache directory."
)
@click.option(
    "--index-url", metavar="URL", help="Use alternative JDK index URL."
)
@click.option(
    "--index-ttl",
    type=int,
    metavar="SECONDS",
    help="Time to live for cached JDK index.",
)
@click.option("--os", metavar="NAME", help="Operating system for JDK.")
@click.option("--arch", metavar="NAME", help="Architecture for JDK.")
@click.option(
    "--progress/--no-progress",
    default=True,
    help="Show or do not show progress bars.",
)
@click.version_option(version=__version__)
def _cli(
    ctx: click.Context,
    jdk: str | None,
    cache_dir: str | None,
    index_url: str | None,
    index_ttl: int | None,
    os: str | None,
    arch: str | None,
    progress: bool,
) -> None:
    """
    Download, cache, and run JDK or JRE distributions.

    Use 'cjdk COMMAND --help' to see usage of each command.
    The common options shown here must be given before COMMAND.
    """
    ctx.ensure_object(dict)
    ctx.obj.update(
        dict(
            jdk=jdk,
            cache_dir=cache_dir,
            index_url=index_url,
            index_ttl=index_ttl,
            os=os,
            arch=arch,
            progress=progress,
        )
    )


@click.command(short_help="List available JDK vendors.")
@click.pass_context
def ls_vendors(ctx: click.Context) -> None:
    """
    Print the list of available JDK vendors.
    """
    vendors = _api.list_vendors(**ctx.obj)
    if vendors:
        print("\n".join(vendors))


@click.command(short_help="List cached or available JDKs matching criteria.")
@click.pass_context
@click.option(
    "--cached/--available",
    default=True,
    help="Show only already-cached JDKs, or show all available JDKs from the index (default cached only).",
)
def ls(ctx: click.Context, cached: bool) -> None:
    """
    Print the list of JDKs matching the given criteria.

    See 'cjdk --help' for the common options used to specify the criteria.
    """
    jdks = _api.list_jdks(**ctx.obj, cached_only=cached)
    if jdks:
        print("\n".join(jdks))


@click.command(short_help="Ensure the requested JDK is cached.")
@click.pass_context
def cache(ctx: click.Context) -> None:
    """
    Download and extract the requested JDK if it is not already cached.

    Usually there is no need to invoke this command on its own, but it may be
    useful if you want any potential JDK download to happen at a controlled
    point in time.

    See 'cjdk --help' for the common options used to specify the JDK and how it
    is obtained.
    """
    _api.cache_jdk(**ctx.obj)


@click.command(hidden=True)
@click.pass_context
def cache_jdk(ctx: click.Context) -> None:
    """
    Deprecated. Use cache function instead.
    """
    _api.cache_jdk(**ctx.obj)


@click.command(
    short_help="Print the Java home directory for the requested JDK."
)
@click.pass_context
def java_home(ctx: click.Context) -> None:
    """
    Print the path that is suitable as the value of JAVA_HOME for the requested
    JDK.

    The JDK is downloaded if not already cached.

    See 'cjdk --help' for the common options used to specify the JDK and how it
    is obtained.
    """
    print(_api.java_home(**ctx.obj))


@click.command(
    context_settings=dict(ignore_unknown_options=True),
    short_help="Run a program using the requested JDK.",
)
@click.pass_context
@click.argument("prog", nargs=1)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def exec(ctx: click.Context, prog: str, args: tuple[str, ...]) -> None:
    """
    Run PROG with the environment variables set for the requested JDK.

    The JDK is downloaded if not already cached.

    See 'cjdk --help' for the common options used to specify the JDK and how it
    is obtained.

    Pass '--' before PROG to prevent any of ARGS to be interpreted by cjdk.
    """
    with _api.java_env(**ctx.obj):
        # os.exec*() do not work well on Windows
        if sys.platform == "win32":
            r = subprocess.run((prog,) + tuple(args))
            sys.exit(r.returncode)
        else:
            os.execvp(prog, (prog,) + tuple(args))


@click.command(short_help="Cache an arbitrary file.")
@click.pass_context
@click.argument("url", nargs=1)
@click.argument("filename", nargs=1)
@click.option(
    "--name", metavar="NAME", help="Name to display in progress message."
)
@click.option(
    "--ttl",
    type=int,
    metavar="SECONDS",
    help="Time to live for the cached file.",
)
@click.option(
    "--sha1",
    metavar="HASH",
    help="Check the downloaded file against the given SHA-1 hash.",
)
@click.option(
    "--sha256",
    metavar="HASH",
    help="Check the downloaded file against the given SHA-256 hash.",
)
@click.option(
    "--sha512",
    metavar="HASH",
    help="Check the downloaded file against the given SHA-512 hash.",
)
def cache_file(
    ctx: click.Context,
    url: str,
    filename: str,
    name: str | None,
    ttl: int | None,
    sha1: str | None,
    sha256: str | None,
    sha512: str | None,
) -> None:
    """
    Download and store an arbitrary file if it is not already cached.

    The file at URL (whose scheme must be https) is stored in the cache with
    the given FILENAME, and the full path to it is printed to standard output.

    See 'cjdk --help' for the common options (JDK-specific options are
    ignored).
    """
    print(
        _api.cache_file(
            name if name else "file",
            url,
            filename,
            ttl=ttl,
            sha1=sha1,
            sha256=sha256,
            sha512=sha512,
            **ctx.obj,
        )
    )


@click.command(short_help="Cache an arbitrary package.")
@click.pass_context
@click.argument("url", nargs=1)
@click.option(
    "--name", metavar="NAME", help="Name to display in progress message."
)
@click.option(
    "--sha1",
    metavar="HASH",
    help="Check the downloaded file against the given SHA-1 hash.",
)
@click.option(
    "--sha256",
    metavar="HASH",
    help="Check the downloaded file against the given SHA-256 hash.",
)
@click.option(
    "--sha512",
    metavar="HASH",
    help="Check the downloaded file against the given SHA-512 hash.",
)
def cache_package(
    ctx: click.Context,
    url: str,
    name: str | None,
    sha1: str | None,
    sha256: str | None,
    sha512: str | None,
) -> None:
    """
    Download, extract, and store an arbitrary .zip or .tar.gz package if it is
    not already cached.

    The file at URL (whose scheme must be tgz+https or zip+https) is extracted
    into a directory in the cache, and the full path to the directory is
    printed to standard output.

    See 'cjdk --help' for the common options (JDK-specific options are
    ignored).
    """
    print(
        _api.cache_package(
            name if name else "package",
            url,
            sha1=sha1,
            sha256=sha256,
            sha512=sha512,
            **ctx.obj,
        )
    )


@click.command(short_help="Remove all cached files.")
@click.pass_context
def clear_cache(ctx: click.Context) -> None:
    """
    Remove all cached JDKs, files, and packages from the cache directory.

    This permanently deletes everything in the cache. Subsequent commands will
    re-download any needed files.

    When clearing the cache, ensure that no other processes are using cjdk or
    the JDKs, files, or packages installed by cjdk.

    See 'cjdk --help' for the common options (only --cache-dir is relevant).
    """
    cleared = _api.clear_cache(**ctx.obj)
    click.echo(f"Cleared cache: {cleared}")


# Register current commands.
_cli.add_command(java_home)
_cli.add_command(exec)
_cli.add_command(ls_vendors)
_cli.add_command(ls)
_cli.add_command(cache)
_cli.add_command(cache_file)
_cli.add_command(cache_package)
_cli.add_command(clear_cache)

# Register hidden/deprecated commands, for backwards compatibility.
_cli.add_command(cache_jdk)


def main() -> None:
    try:
        _cli()
    except CjdkError as e:
        print(f"cjdk: Error: {e}", file=sys.stderr)
        sys.exit(e.exit_code)


if __name__ == "__main__":
    main()
