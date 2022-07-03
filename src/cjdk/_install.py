# This file is part of cjdk.
# Copyright 2022 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import sys

from . import _cache, _download

__all__ = [
    "install_file",
    "install_dir",
]


def install_file(prefix, name, url, filename, conf, *, ttl, checkfunc=None):
    def fetch(dest):
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


def install_dir(prefix, name, url, conf, *, checkfunc=None):
    def fetch(destdir):
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


def _print_progress_header(conf, name):
    if conf.progress:
        print(
            f"cjdk: Installing {name} to {conf.cache_dir}",
            file=sys.stderr,
        )
