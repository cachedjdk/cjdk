# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import os
import platform
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from . import _index

__all__ = [
    "Configuration",
    "configure",
    "default_cachedir",
    "default_index_url",
    "canonicalize_os",
    "canonicalize_arch",
    "default_vendor",
]


@dataclass
class Configuration:
    os: str
    arch: str
    vendor: str
    version: str
    cache_dir: Path
    index_url: str
    index_ttl: int
    progress: bool
    _allow_insecure_for_testing: bool


def configure(**kwargs):
    # kwargs must have API-specific items removed before passing here.

    jdk = kwargs.pop("jdk", None)
    if jdk:
        if kwargs.get("vendor", None):
            raise ValueError("Cannot specify jdk= together with vendor=")
        if kwargs.get("version", None):
            raise ValueError("Cannot specify jdk= together with version=")
        kwargs["vendor"], kwargs["version"] = _parse_vendor_version(jdk)

    conf = Configuration(
        os=canonicalize_os(kwargs.pop("os", None)),
        arch=canonicalize_arch(kwargs.pop("arch", None)),
        vendor=kwargs.pop("vendor", None) or default_vendor(),
        version=kwargs.pop("version", "") or "",
        cache_dir=kwargs.pop("cache_dir", None) or default_cachedir(),
        index_url=kwargs.pop("index_url", None) or default_index_url(),
        index_ttl=kwargs.pop("index_ttl", 86400),
        progress=kwargs.pop("progress", True),
        _allow_insecure_for_testing=kwargs.pop(
            "_allow_insecure_for_testing", False
        ),
    )

    if not isinstance(conf.cache_dir, Path):
        conf.cache_dir = Path(conf.cache_dir)

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


def canonicalize_os(os):
    if not os:
        os = sys.platform
    os = os.lower()

    if os == "win32":
        os = "windows"
    elif os == "macos":
        os = "darwin"
    elif os.startswith("aix"):
        os = "aix"
    elif os.startswith("solaris"):
        os = "solaris"

    return os


def canonicalize_arch(arch):
    if not arch:
        arch = platform.machine()
    arch = arch.lower()

    if arch in ("x86_64", "x86-64", "x64"):
        arch = "amd64"
    elif arch == "aarch64":
        arch = "arm64"
    elif re.fullmatch(r"i?[356]86", arch):
        arch = "x86"

    return arch


def default_vendor():
    """
    Return the default vendor.

    This is either from the environment variable CJDK_DEFAULT_VENDOR, or
    "adoptium".
    """
    if "CJDK_DEFAULT_VENDOR" in os.environ:
        return os.environ["CJDK_DEFAULT_VENDOR"]
    return "adoptium"
