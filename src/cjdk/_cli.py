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
@click.option("--jdk", "-j", help="JDK vendor:version specifier.")
@click.option("--cache-dir", help="Override root cache directory.")
@click.option(
    "--progress/--no-progress",
    default=True,
    help="Show progress bars.",
)
@click.version_option()
def main(ctx, jdk, cache_dir, progress):
    ctx.ensure_object(dict)
    ctx.obj.update(dict(jdk=jdk, cache_dir=cache_dir, progress=progress))


@click.command()
@click.pass_context
def java_home(ctx):
    print(_api.java_home(**ctx.obj))


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.pass_context
@click.argument("prog", nargs=1)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def exec(ctx, prog, args):
    with _api.java_env(**ctx.obj):
        # os.exec*() do not work well on Windows
        if sys.platform == "win32":
            r = subprocess.run((prog,) + tuple(args))
            sys.exit(r.returncode)
        else:
            os.execvp(prog, (prog,) + tuple(args))


main.add_command(java_home)
main.add_command(exec)
