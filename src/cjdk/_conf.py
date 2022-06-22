# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from . import _index

__all__ = [
    "configure",
    "default_cachedir",
    "default_index_url",
    "Configuration",
]


def configure(vendor=None, version=None, **kwargs):
    # kwargs must have API-specific items removed before passing here.

    if "jdk" in kwargs:
        if vendor is not None or version is not None:
            raise ValueError(
                "Cannot specify jdk= together with vendor= or version="
            )
        vendor, version = _parse_vendor_version(kwargs.pop("jdk"))

    conf = Configuration(vendor=vendor, version=version)

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


def default_cachedir():
    """
    Return the cache directory path to be used by default.

    This is either from the environment variable CJDK_CACHE_DIR, or in the
    default user cache directory.
    """
    if "CJDK_CACHE_DIR" in os.environ:
        ret = Path(os.environ["CJDK_CACHE_DIR"])
        if not ret.is_absolute():
            raise ValueError(
                f"CJDK_CACHE_DIR must be an absolute path (found '{ret}')"
            )
        return ret
    return _default_cachedir()


def _default_cachedir():
    if sys.platform == "win32":
        return _windows_cachedir()
    elif sys.platform == "darwin":
        return _macos_cachedir()
    else:
        return _xdg_cachedir()


def _windows_cachedir():
    return _local_app_data() / "cjdk" / "cache"


def _local_app_data():
    if "LOCALAPPDATA" in os.environ:
        return Path(os.environ["LOCALAPPDATA"])
    return Path.home() / "AppData" / "Local"


def _macos_cachedir():
    return Path.home() / "Library" / "Caches" / "cjdk"


def _xdg_cachedir():
    if "XDG_CACHE_HOME" in os.environ:
        return Path(os.environ["XDG_CACHE_HOME"]) / "cjdk"
    return Path.home() / ".cache" / "cjdk"


def default_index_url():
    # The Coursier JDK index is auto-generated, well curated, and clean.
    return "https://raw.githubusercontent.com/coursier/jvm-index/master/index.json"

    # There is also an older index from the jabba project, but it is manually
    # maintained and would benefit from some data cleaning. Noting down the URL
    # here in case we ever need an alternative. Note that it won't work without
    # some normalization of arch names.
    # "https://raw.githubusercontent.com/shyiko/jabba/master/index.json"


@dataclass
class Configuration:
    vendor: str
    version: str
    cache_dir: Path = default_cachedir()
    index_url: str = default_index_url()
    os: str = None
    arch: str = None
    progress: bool = True
    _allow_insecure_for_testing: bool = False
