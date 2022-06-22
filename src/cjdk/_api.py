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
    os -- operating system for the JDK
    arch -- architecture for the JDK
    progress -- show progress if true
    """
    conf = _conf.configure(vendor=vendor, version=version, **kwargs)
    index = _index.jdk_index(conf)
    url = _index.jdk_url(index, conf)
    key = ("jdks",) + _cache.key_for_url(url)

    def fetch(destdir):
        _download.download_jdk(
            destdir,
            url,
            progress=conf.progress,
            _allow_insecure_for_testing=conf._allow_insecure_for_testing,
        )

    path = _cache.permanent_directory(
        key,
        fetch,
        cache_dir=conf.cache_dir,
        timeout_for_fetch_elsewhere=300,
    )

    return _jdk.find_home(path)


@contextmanager
def java_env(*, vendor=None, version=None, add_bin=True, **kwargs):
    """
    Context manager to set environment for the given JDK, installing if
    necessary.

    Keyword arguments: Same as java_home(), plus
    add_bin -- if False, do not modify PATH; set only JAVA_HOME
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
