# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path

from . import _index, _install
from ._conf import Configuration
from ._exceptions import InstallError, JdkNotFoundError, UnsupportedFormatError

__all__ = [
    "install_jdk",
    "find_home",
]


_JDK_KEY_PREFIX = "jdks"


def install_jdk(conf: Configuration) -> Path:
    """
    Install a JDK if it is not already installed.
    """
    index = _index.jdk_index(conf)
    conf.version = _index.resolve_jdk_version(index, conf)
    name = f"JDK {conf.vendor}:{conf.version}"
    url = _index.jdk_url(index, conf)

    try:
        return _install.install_dir(_JDK_KEY_PREFIX, name, url, conf)
    except UnsupportedFormatError as e:
        raise JdkNotFoundError(
            f"Unsupported archive format for {name}: {e}"
        ) from e


def find_home(path: Path, _recursion_depth: int = 2) -> Path:
    """
    Find the Java home directory within path.

    The path may point to the Java home, or a directory containing it, or (for
    macOS) a directory containing Contents/Home.
    """

    if _looks_like_java_home(path):
        return path
    macos_extra = Path("Contents", "Home")
    if _looks_like_java_home(path / macos_extra):
        return path / macos_extra
    if _recursion_depth > 0:
        subdir = _contains_single_subdir(path)
        if subdir:
            return find_home(subdir, _recursion_depth=_recursion_depth - 1)
    raise InstallError(f"{path} does not look like it contains a JDK or JRE")


def _looks_like_java_home(path: Path) -> bool:
    return (path / "bin").is_dir() and (
        (path / "bin" / "java").is_file()
        or (path / "bin" / "java.exe").is_file()
    )


def _contains_single_subdir(path: Path) -> Path | None:
    try:
        items = list(i for i in path.iterdir() if i.is_dir())
    except OSError as e:
        raise InstallError(f"Cannot read directory {path}: {e}") from e
    if len(items) == 1:
        return items[0]
    return None
