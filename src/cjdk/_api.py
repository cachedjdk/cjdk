# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import os
import re

from . import _cache
from . import _download
from . import _index
from . import _jdk

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
    conf = _check_kwargs(vendor, version, **kwargs)
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


@dataclass
class _Config:
    vendor: str
    version: str
    cache_dir: Path = _cache.default_cachedir()
    index_url: str = _index.default_index_url()
    os: str = None
    arch: str = None
    progress: bool = True
    _allow_insecure_for_testing = False


def _check_kwargs(vendor=None, version=None, **kwargs):
    # kwargs must have API-specific items removed before passing here.

    if "jdk" in kwargs:
        if vendor is not None or version is not None:
            raise ValueError(
                "Cannot specify jdk= together with vendor= or version="
            )
        vendor, version = _parse_vendor_version(kwargs.pop("jdk"))

    conf = _Config(vendor=vendor, version=version)

    cache_dir = kwargs.pop("cache_dir", None)
    if cache_dir:
        conf.cache_dir = Path(cache_dir)

    index_url = kwargs.pop("index_url", None)
    if index_url:
        conf.index_url = index_url

    conf.os = kwargs.pop("os", None)
    conf.arch = kwargs.pop("arch", None)
    conf.progress = kwargs.pop("progress", True)

    conf._allow_insecure_for_testing = kwargs.pop(
        "_allow_insecure_for_testing", False
    )

    if kwargs:
        raise ValueError(f"Unrecognized kwargs: {tuple(kwargs.keys())}")
    return conf


def _parse_vendor_version(spec):
    # Actually we don't fully parse here; we only disambiguate between vendor
    # and version when only one is given.
    if ":" in spec:
        parts = spec.split(":")
        if len(parts) != 2:
            raise ValueError(f"Cannot parse JDK spec '{spec}'")
        return tuple(parts)
    if len(spec) == 0:
        return "", ""
    if re.fullmatch(r"[a-z][a-z0-9-]*", spec):
        return spec, ""
    if re.fullmatch(r"[0-9+.-]*", spec):
        return "", spec
    raise ValueError(f"Cannot parse JDK spec '{spec}'")
