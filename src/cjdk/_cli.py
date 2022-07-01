# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import os
import subprocess
import sys

import click

from . import __version__, _api

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
def main(ctx, jdk, cache_dir, index_url, index_ttl, os, arch, progress):
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


@click.command(short_help="Install the requested JDK.")
@click.pass_context
def install(ctx):
    """
    Install the requested JDK, but do not do anything with it.

    The JDK is downloaded if not already cached.

    Usually there is no need to invoke this command on its own, but it may be
    useful if you want any potentil JDK download to happen at a controlled
    point in time.

    See `cjdk --help` for the common options used to specify the JDK and how it
    is obtained.
    """
    _api.install_jdk(**ctx.obj)


@click.command(
    short_help="Print the Java home directory for the requested JDK."
)
@click.pass_context
def java_home(ctx):
    """
    Print the path that is suitable as the value of JAVA_HOME for the requested
    JDK.

    The JDK is downloaded if not already cached.

    See `cjdk --help` for the common options used to specify the JDK and how it
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
def exec(ctx, prog, args):
    """
    Run PROG with the environment variables set for the requested JDK.

    The JDK is download if not already cached.

    See `cjdk --help` for the common options used to specify the JDK and how it
    is obtained.
    """
    with _api.java_env(**ctx.obj):
        # os.exec*() do not work well on Windows
        if sys.platform == "win32":
            r = subprocess.run((prog,) + tuple(args))
            sys.exit(r.returncode)
        else:
            os.execvp(prog, (prog,) + tuple(args))


main.add_command(java_home)
main.add_command(exec)
main.add_command(install)
