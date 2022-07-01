# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import os
import platform
import re
import sys
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "Configuration",
    "configure",
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
        os=_canonicalize_os(kwargs.pop("os", None)),
        arch=_canonicalize_arch(kwargs.pop("arch", None)),
        vendor=kwargs.pop("vendor", None) or _default_vendor(),
        version=kwargs.pop("version", "") or "",
        cache_dir=kwargs.pop("cache_dir", None) or _default_cachedir(),
        index_url=kwargs.pop("index_url", None) or _default_index_url(),
        index_ttl=kwargs.pop("index_ttl", None),
        progress=kwargs.pop("progress", True),
        _allow_insecure_for_testing=kwargs.pop(
            "_allow_insecure_for_testing", False
        ),
    )

    if not isinstance(conf.cache_dir, Path):
        conf.cache_dir = Path(conf.cache_dir)

    if conf.index_ttl is None:
        conf.index_ttl = _default_index_ttl()

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


def _default_cachedir():
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

    if sys.platform == "win32":
        return _windows_cachedir()
    elif sys.platform == "darwin":
        return _macos_cachedir()
    else:
        return _xdg_cachedir()


def _windows_cachedir(*, create=True):
    cjdk_cache = _local_app_data(create=create) / "cjdk"
    if create:
        cjdk_cache.mkdir(mode=0o700, exist_ok=True)
    return cjdk_cache / "cache"


def _local_app_data(*, create=True):
    # https://docs.microsoft.com/en-us/windows/win32/shell/knownfolderid#FOLDERID_LocalAppData
    # https://docs.microsoft.com/en-us/windows/win32/msi/localappdatafolder
    # It is not clear, but I'm pretty sure it's safe to assume that the
    # directory exists.
    if "LOCALAPPDATA" in os.environ:
        return Path(os.environ["LOCALAPPDATA"])
    return Path.home() / "AppData" / "Local"


def _macos_cachedir(*, create=True):
    # ~/Library/Caches almost always already exists, and both dirs are 0o700.
    # Create them here if they don't exist to ensure correct permissions.
    caches = Path.home() / "Library" / "Caches"
    if create:
        caches.parent.mkdir(mode=0o700, exist_ok=True)
        caches.mkdir(mode=0o700, exist_ok=True)
    return caches / "cjdk"


def _xdg_cachedir(*, create=True):
    # https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    if "XDG_CACHE_HOME" in os.environ:
        caches = Path(os.environ["XDG_CACHE_HOME"])
    else:
        caches = Path.home() / ".cache"
    # The spec says that if the directory does not exist, it should be created
    # with 0o700; if it exists, permissions should not be changed.
    if create:
        caches.mkdir(mode=0o700, exist_ok=True)
    return caches / "cjdk"


def _default_index_url():
    # The Coursier JDK index is auto-generated, well curated, and clean.
    coursier_index_url = "https://raw.githubusercontent.com/coursier/jvm-index/master/index.json"
    return os.environ.get("CJDK_INDEX_URL", None) or coursier_index_url

    # There is also an older index from the jabba project, but it is manually
    # maintained and would benefit from some data cleaning. Noting down the URL
    # here in case we ever need an alternative. Note that it won't work without
    # some normalization of arch names.
    # "https://raw.githubusercontent.com/shyiko/jabba/master/index.json"


def _default_index_ttl():
    return int(os.environ.get("CJDK_INDEX_TTL", "86400"))


def _canonicalize_os(osname):
    if not osname:
        osname = os.environ.get("CJDK_OS", sys.platform)
    osname = osname.lower()

    if osname == "win32":
        osname = "windows"
    elif osname == "macos":
        osname = "darwin"
    elif osname.startswith("aix"):
        osname = "aix"
    elif osname.startswith("solaris"):
        osname = "solaris"

    return osname


def _canonicalize_arch(arch):
    if not arch:
        arch = os.environ.get("CJDK_ARCH", platform.machine())
    arch = arch.lower()

    if arch in ("x86_64", "x86-64", "x64"):
        arch = "amd64"
    elif arch == "aarch64":
        arch = "arm64"
    elif re.fullmatch(r"i?[356]86", arch):
        arch = "x86"

    return arch


def _default_vendor():
    """
    Return the default vendor.

    This is either from the environment variable CJDK_VENDOR, or "adoptium".
    """
    if "CJDK_VENDOR" in os.environ:
        return os.environ["CJDK_VENDOR"]
    return "adoptium"
