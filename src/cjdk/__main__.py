# This file is part of cjdk.
# Copyright 2022 Board of Regents of the University of Wisconsin System
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


@click.command(short_help="Ensure the requested JDK is cached.")
@click.pass_context
def cache_jdk(ctx):
    """
    Download and extract the requested JDK if it is not already cached.

    Usually there is no need to invoke this command on its own, but it may be
    useful if you want any potentil JDK download to happen at a controlled
    point in time.

    See 'cjdk --help' for the common options used to specify the JDK and how it
    is obtained.
    """
    _api.cache_jdk(**ctx.obj)


@click.command(
    short_help="Print the Java home directory for the requested JDK."
)
@click.pass_context
def java_home(ctx):
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
def exec(ctx, prog, args):
    """
    Run PROG with the environment variables set for the requested JDK.

    The JDK is download if not already cached.

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
def cache_file(ctx, url, filename, name, ttl, sha1, sha256, sha512):
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
def cache_package(ctx, url, name, sha1, sha256, sha512):
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


main.add_command(java_home)
main.add_command(exec)
main.add_command(cache_jdk)
main.add_command(cache_file)
main.add_command(cache_package)


if __name__ == "__main__":
    main()
