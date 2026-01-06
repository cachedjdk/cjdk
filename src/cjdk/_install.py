# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT
from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from . import _cache, _download

if TYPE_CHECKING:
    from collections.abc import Callable

    from ._conf import Configuration

__all__ = [
    "install_file",
    "install_dir",
]


def install_file(
    prefix: str,
    name: str,
    url: str,
    filename: str,
    conf: Configuration,
    *,
    ttl: float,
    checkfunc: Callable[[Path], None] | None = None,
) -> Path:
    def fetch(dest: Path) -> None:
        _print_progress_header(conf, name)
        _download.download_file(
            dest,
            url,
            checkfunc=checkfunc,
            progress=conf.progress,
            _allow_insecure_for_testing=conf._allow_insecure_for_testing,
        )

    return _cache.atomic_file(
        prefix,
        url,
        filename,
        fetch,
        ttl=ttl,
        cache_dir=conf.cache_dir,
    )


def install_dir(
    prefix: str,
    name: str,
    url: str,
    conf: Configuration,
    *,
    checkfunc: Callable[[Path], None] | None = None,
) -> Path:
    def fetch(destdir: Path) -> None:
        _print_progress_header(conf, name)
        _download.download_and_extract(
            destdir,
            url,
            checkfunc=checkfunc,
            progress=conf.progress,
            _allow_insecure_for_testing=conf._allow_insecure_for_testing,
        )

    return _cache.permanent_directory(
        prefix,
        url,
        fetch,
        cache_dir=conf.cache_dir,
        timeout_for_fetch_elsewhere=300,
    )


def _print_progress_header(conf: Configuration, name: str) -> None:
    if conf.progress:
        print(
            f"cjdk: Installing {name} to {conf.cache_dir}",
            file=sys.stderr,
        )
