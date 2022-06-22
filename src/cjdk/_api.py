# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import os
from contextlib import contextmanager

from . import _cache, _download, _index, _jdk, _conf

__all__ = [
    "java_env",
    "java_home",
]


def java_home(*, vendor=None, version=None, **kwargs):
    """
    Return the JDK home directory for the given JDK, installing if necessary.

    Keyword arguments:
    vendor -- JDK vendor name
    version -- JDK version expression
    jdk -- string with format vendor:version
    cache_dir -- override the root cache directory
    index_url -- alternative URL for JDK index
    """
    conf = _conf.configure(vendor, version, **kwargs)
    index = _index.jdk_index(
        cachedir=conf.cache_dir,
        url=conf.index_url,
        _allow_insecure_for_testing=conf._allow_insecure_for_testing,
    )
    url = _index.jdk_url(
        index, conf.vendor, conf.version, os=conf.os, arch=conf.arch
    )
    key = ("jdks",) + _cache.url_to_key(url)

    def fetch(destdir, progress=None, **kwargs):
        _download.download_jdk(
            destdir,
            url,
            progress=progress,
            _allow_insecure_for_testing=conf._allow_insecure_for_testing,
        )

    path = _cache.permanent_directory(
        key,
        fetch,
        cachedir=conf.cache_dir,
        timeout_for_fetch_elsewhere=300,
        progress=conf.progress,
    )

    return _jdk.find_home(path)


@contextmanager
def java_env(*, vendor=None, version=None, add_bin=True, **kwargs):
    """
    Context manager to set environment for the given JDK, installing if
    necessary.

    Keyword arguments:
    vendor -- JDK vendor name
    version -- JDK version expression
    jdk -- string with format vendor:version
    add_bin -- if False, do not modify PATH; only JAVA_HOME
    cache_dir -- override the root cache directory
    index_url -- alternative URL for JDK index
    """
    home = java_home(vendor=vendor, version=version, **kwargs)
    with _env_var_set("JAVA_HOME", str(home)):
        if add_bin:
            path = (
                str(home / "bin") + os.pathsep + os.environ.get("PATH", None)
            )
            with _env_var_set("PATH", path):
                yield home
        else:
            yield home


@contextmanager
def _env_var_set(name, value):
    old_value = os.environ.get(name, None)
    os.environ[name] = value
    yield
    if old_value:
        os.environ[name] = old_value
    else:
        del os.environ[name]
