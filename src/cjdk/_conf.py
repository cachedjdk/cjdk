# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT
from __future__ import annotations

import os
import platform
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ._exceptions import ConfigError

if TYPE_CHECKING:
    from typing import TypedDict

    from typing_extensions import Unpack

    class ConfigKwargs(TypedDict, total=False):
        jdk: str | None
        os: str | None
        arch: str | None
        vendor: str | None
        version: str | None
        cache_dir: str | Path | None
        index_url: str | None
        index_ttl: float | None
        progress: bool
        _allow_insecure_for_testing: bool


__all__ = [
    "Configuration",
    "configure",
    "parse_vendor_version",
]


@dataclass
class Configuration:
    os: str
    arch: str
    vendor: str
    version: str
    cache_dir: Path
    index_url: str
    index_ttl: float
    progress: bool
    _allow_insecure_for_testing: bool


def check_str(
    name: str,
    value: object,
    *,
    allow_none: bool = False,
    allow_empty: bool = True,
) -> None:
    if value is None:
        if allow_none:
            return
        raise TypeError(f"{name} must be a string, got None")
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string, got {type(value).__name__}")
    if not allow_empty and value == "":
        raise ConfigError(f"{name} must not be empty")


def configure(**kwargs: Unpack[ConfigKwargs]) -> Configuration:
    # kwargs must have API-specific items removed before passing here.

    for name in ("jdk", "os", "arch", "vendor", "version"):
        check_str(name, kwargs.get(name), allow_none=True)

    jdk = kwargs.pop("jdk", None)
    if jdk:
        if kwargs.get("vendor"):
            raise ConfigError("Cannot specify jdk= together with vendor=")
        if kwargs.get("version"):
            raise ConfigError("Cannot specify jdk= together with version=")
        kwargs["vendor"], kwargs["version"] = parse_vendor_version(jdk)

    index_ttl = kwargs.pop("index_ttl", None)
    if not index_ttl and index_ttl != 0:
        index_ttl = _default_index_ttl()

    cache_dir = kwargs.pop("cache_dir", None) or _default_cachedir()
    if not isinstance(cache_dir, Path):
        cache_dir = Path(cache_dir)

    conf = Configuration(
        os=_canonicalize_os(kwargs.pop("os", None)),
        arch=_canonicalize_arch(kwargs.pop("arch", None)),
        vendor=kwargs.pop("vendor", None) or _default_vendor(),
        version=kwargs.pop("version", "") or "",
        cache_dir=cache_dir,
        index_url=kwargs.pop("index_url", None) or _default_index_url(),
        index_ttl=index_ttl,
        progress=kwargs.pop("progress", True),
        _allow_insecure_for_testing=kwargs.pop(
            "_allow_insecure_for_testing", False
        ),
    )

    if kwargs:
        raise ConfigError(f"Unrecognized kwargs: {tuple(kwargs.keys())}")
    return conf


def parse_vendor_version(spec: str) -> tuple[str, str]:
    # Actually we don't fully parse here; we only disambiguate between vendor
    # and version when only one is given.
    if ":" in spec:
        parts = spec.split(":")
        if len(parts) != 2:
            raise ConfigError(f"Cannot parse JDK spec '{spec}'")
        vendor, version = parts
        return (vendor, version)
    if len(spec) == 0:
        return "", ""
    if re.fullmatch(r"[a-z][a-z0-9-]*", spec):
        return spec, ""
    if re.fullmatch(r"[0-9+.-]*", spec):
        return "", spec
    raise ConfigError(f"Cannot parse JDK spec '{spec}'")


def _default_cachedir() -> Path:
    """
    Return the cache directory path to be used by default.

    This is either from the environment variable CJDK_CACHE_DIR, or in the
    default user cache directory.
    """
    if v := os.environ.get("CJDK_CACHE_DIR"):
        ret = Path(v)
        if not ret.is_absolute():
            raise ConfigError(
                f"CJDK_CACHE_DIR must be an absolute path (found '{ret}')"
            )
        return ret

    if sys.platform == "win32":
        return _windows_cachedir()
    elif sys.platform == "darwin":
        return _macos_cachedir()
    else:
        return _xdg_cachedir()


def _windows_cachedir(*, create: bool = True) -> Path:
    cjdk_cache = _local_app_data(create=create) / "cjdk"
    if create:
        try:
            cjdk_cache.mkdir(mode=0o700, exist_ok=True)
        except OSError as e:
            raise ConfigError(
                f"Failed to create cache directory {cjdk_cache}: {e}"
            ) from e
    return cjdk_cache / "cache"


def _local_app_data(*, create: bool = True) -> Path:
    # https://docs.microsoft.com/en-us/windows/win32/shell/knownfolderid#FOLDERID_LocalAppData
    # https://docs.microsoft.com/en-us/windows/win32/msi/localappdatafolder
    # It is not clear, but I'm pretty sure it's safe to assume that the
    # directory exists.
    if v := os.environ.get("LOCALAPPDATA"):
        return Path(v)
    try:
        return Path.home() / "AppData" / "Local"
    except RuntimeError as e:
        raise ConfigError(f"Cannot determine home directory: {e}") from e


def _macos_cachedir(*, create: bool = True) -> Path:
    # ~/Library/Caches almost always already exists, and both dirs are 0o700.
    # Create them here if they don't exist to ensure correct permissions.
    try:
        caches = Path.home() / "Library" / "Caches"
    except RuntimeError as e:
        raise ConfigError(f"Cannot determine home directory: {e}") from e
    if create:
        try:
            caches.parent.mkdir(mode=0o700, exist_ok=True)
            caches.mkdir(mode=0o700, exist_ok=True)
        except OSError as e:
            raise ConfigError(
                f"Failed to create cache directory {caches}: {e}"
            ) from e
    return caches / "cjdk"


def _xdg_cachedir(*, create: bool = True) -> Path:
    # https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    if v := os.environ.get("XDG_CACHE_HOME"):
        caches = Path(v)
    else:
        try:
            caches = Path.home() / ".cache"
        except RuntimeError as e:
            raise ConfigError(f"Cannot determine home directory: {e}") from e
    # The spec says that if the directory does not exist, it should be created
    # with 0o700; if it exists, permissions should not be changed.
    if create:
        try:
            caches.mkdir(mode=0o700, exist_ok=True)
        except OSError as e:
            raise ConfigError(
                f"Failed to create cache directory {caches}: {e}"
            ) from e
    return caches / "cjdk"


def _default_index_url() -> str:
    # The Coursier JDK index is auto-generated, well curated, and clean.
    coursier_index_url = "https://raw.githubusercontent.com/coursier/jvm-index/master/index.json"
    return os.environ.get("CJDK_INDEX_URL") or coursier_index_url

    # There is also an older index from the jabba project, but it is manually
    # maintained and would benefit from some data cleaning. Noting down the URL
    # here in case we ever need an alternative. Note that it won't work without
    # some normalization of arch names.
    # "https://raw.githubusercontent.com/shyiko/jabba/master/index.json"


def _default_index_ttl() -> float:
    ttl_str = os.environ.get("CJDK_INDEX_TTL") or "86400"
    try:
        return float(ttl_str)
    except ValueError as e:
        raise ConfigError(
            f"Invalid value for CJDK_INDEX_TTL: '{ttl_str}' (must be a number)"
        ) from e


def _canonicalize_os(osname: str | None) -> str:
    if not osname:
        osname = os.environ.get("CJDK_OS") or sys.platform
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


def _canonicalize_arch(arch: str | None) -> str:
    if not arch:
        arch = os.environ.get("CJDK_ARCH") or platform.machine()
    arch = arch.lower()

    if arch in ("x86_64", "x86-64", "x64"):
        arch = "amd64"
    elif arch == "aarch64":
        arch = "arm64"
    elif re.fullmatch(r"i?[356]86", arch):
        arch = "x86"

    return arch


def _default_vendor() -> str:
    """
    Return the default vendor.

    This is either from the environment variable CJDK_VENDOR, or "adoptium".
    """
    return os.environ.get("CJDK_VENDOR") or "adoptium"
