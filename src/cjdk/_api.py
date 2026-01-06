# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import os
import shutil
from contextlib import contextmanager
from typing import TYPE_CHECKING

from . import _cache, _conf, _index, _install, _jdk
from ._exceptions import (
    CjdkError,
    ConfigError,
    InstallError,
    UnsupportedFormatError,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from typing_extensions import Unpack

    from ._conf import ConfigKwargs

__all__ = [
    "cache_file",
    "cache_jdk",
    "cache_package",
    "clear_cache",
    "java_env",
    "java_home",
    "list_jdks",
    "list_vendors",
]


def list_vendors(**kwargs: Unpack[ConfigKwargs]) -> list[str]:
    """
    Return the list of available JDK vendors.

    Parameters
    ----------
    None

    Other Parameters
    ----------------
    cache_dir : pathlib.Path or str, optional
        Override the root cache directory.
    index_url : str, optional
        Alternative URL for the JDK index.

    Returns
    -------
    list[str]
        The available JDK vendors.

    Raises
    ------
    ConfigError
        If configuration is invalid.
    InstallError
        If fetching the index fails.
    """
    return sorted(_get_vendors(**kwargs))


def list_jdks(  # type: ignore [misc]  # overlap with kwargs
    *,
    vendor: str | None = None,
    version: str | None = None,
    cached_only: bool = True,
    **kwargs: Unpack[ConfigKwargs],
) -> list[str]:
    """
    Return the list of JDKs matching the given criteria.

    Parameters
    ----------
    vendor : str, optional
        JDK vendor name, such as "adoptium".
    version : str, optional
        JDK version expression, such as "17+".
    cached_only : bool, optional
        If True, list only already-cached JDKs.
        If False, list all matching JDKs in the index.

    Other Parameters
    ----------------
    jdk : str, optional
        JDK vendor and version, such as "adoptium:17+". Cannot be specified
        together with `vendor` or `version`.
    cache_dir : pathlib.Path or str, optional
        Override the root cache directory.
    index_url : str, optional
        Alternative URL for the JDK index.
    os : str, optional
        Operating system for the JDK (default: current operating system).
    arch : str, optional
        CPU architecture for the JDK (default: current architecture).

    Returns
    -------
    list[str]
        JDKs (vendor:version) matching the criteria.

    Raises
    ------
    ConfigError
        If configuration is invalid.
    InstallError
        If fetching the index fails.
    """
    return _get_jdks(
        vendor=vendor, version=version, cached_only=cached_only, **kwargs
    )


def clear_cache(**kwargs: Unpack[ConfigKwargs]) -> Path:
    """
    Remove all cached files and directories.

    This should not be called when other processes may be using cjdk or the
    JDKs and files installed by cjdk.

    Other Parameters
    ----------------
    cache_dir : pathlib.Path or str, optional
        Override the root cache directory.

    Returns
    -------
    pathlib.Path
        The cache directory that was cleared.

    Raises
    ------
    CjdkError
        If the cache directory could not be removed.
    """
    conf = _conf.configure(**kwargs)
    cache_path = conf.cache_dir
    if cache_path.exists():
        try:
            shutil.rmtree(cache_path)
        except OSError as e:
            raise CjdkError(
                f"Failed to remove cache directory {cache_path}: {e}"
            ) from e
    return cache_path


def cache_jdk(  # type: ignore [misc]  # overlap with kwargs
    *,
    vendor: str | None = None,
    version: str | None = None,
    **kwargs: Unpack[ConfigKwargs],
) -> None:
    """
    Download and extract the given JDK if it is not already cached.

    Parameters
    ----------
    vendor : str, optional
        JDK vendor name, such as "adoptium".
    version : str, optional
        JDK version expression, such as "17+".

    Other Parameters
    ----------------
    jdk : str, optional
        JDK vendor and version, such as "adoptium:17+". Cannot be specified
        together with `vendor` or `version`.
    cache_dir : pathlib.Path or str, optional
        Override the root cache directory.
    index_url : str, optional
        Alternative URL for the JDK index.
    index_ttl : int or float, optional
        Time to live (in seconds) for the cached index.
    os : str, optional
        Operating system for the JDK (default: current operating system).
    arch : str, optional
        CPU architecture for the JDK (default: current architecture).
    progress : bool, default: True
        Whether to show progress bars.

    Returns
    -------
    None

    Raises
    ------
    ConfigError
        If configuration is invalid.
    JdkNotFoundError
        If no matching JDK is available.
    InstallError
        If download or extraction fails.
    """
    conf = _conf.configure(vendor=vendor, version=version, **kwargs)
    _jdk.install_jdk(conf)


def java_home(  # type: ignore [misc]  # overlap with kwargs
    *,
    vendor: str | None = None,
    version: str | None = None,
    **kwargs: Unpack[ConfigKwargs],
) -> Path:
    """
    Return the JDK home directory for the given JDK, installing if necessary.

    Parameters are the same as for cache_jdk().

    Returns
    -------
    pathlib.Path
        The JDK home directory satisfying the requested parameters.

    Raises
    ------
    ConfigError
        If configuration is invalid.
    JdkNotFoundError
        If no matching JDK is available.
    InstallError
        If download or extraction fails.
    """
    conf = _conf.configure(vendor=vendor, version=version, **kwargs)
    path = _jdk.install_jdk(conf)
    return _jdk.find_home(path)


@contextmanager
def java_env(  # type: ignore [misc]  # overlap with kwargs
    *,
    vendor: str | None = None,
    version: str | None = None,
    add_bin: bool = True,
    **kwargs: Unpack[ConfigKwargs],
) -> Iterator[Path]:
    """
    Context manager to set environment variables for the given JDK, installing
    if necessary.

    Parameters are the same as for cache_jdk(), with the following addition.

    Parameters
    ----------
    add_bin : bool, default: True
        Whether to prepend the Java "bin" directory to `PATH`, in addition to
        setting `JAVA_HOME`. If false, `PATH` is not modified.

    Returns
    -------
    ContextManager[pathlib.Path]
        Context manager that temporarily sets the `JAVA_HOME` and (optionally)
        `PATH` environment variables for the JDK satisfying the requested
        parameters. Its value is the JDK home directory.

    Raises
    ------
    ConfigError
        If configuration is invalid.
    JdkNotFoundError
        If no matching JDK is available.
    InstallError
        If download or extraction fails.
    """
    home = java_home(vendor=vendor, version=version, **kwargs)
    with _env_var_set("JAVA_HOME", str(home)):
        if add_bin:
            path = str(home / "bin") + os.pathsep + os.environ.get("PATH", "")
            with _env_var_set("PATH", path):
                yield home
        else:
            yield home


def cache_file(
    name: str,
    url: str,
    filename: str,
    ttl: float | None = None,
    *,
    sha1: str | None = None,
    sha256: str | None = None,
    sha512: str | None = None,
    **kwargs: Unpack[ConfigKwargs],
) -> Path:
    """
    Install any file resource into the cache, downloading if necessary.

    Parameters are the same as for cache_jdk() (JDK-specific parameters are
    ignored), with the following additions.

    Parameters
    ----------
    name : str
        Name to display in case of showing progress.
    url : str
        The URL of the file resource. The scheme must be https.
    filename : str
        The filename under which the file will be stored.
    ttl : int or float, optional
        Time to live (in seconds) for the cached file resource.
    sha1 : str, optional
        SHA-1 hash that the downloaded file must match.
    sha256 : str, optional
        SHA-256 hash that the downloaded file must match.
    sha512 : str, optional
        SHA-512 hash that the downloaded file must match.

    Returns
    -------
    pathlib.Path
        Path to the cached file resource, whose final component is the given
        filename.

    Raises
    ------
    ConfigError
        If configuration or URL is invalid.
    InstallError
        If download or hash check fails.

    Notes
    -----
    The check for SHA-1/SHA-256/SHA-512 hashes is only performed after a
    download; it is not performed if the file already exists in the cache.
    """
    _conf.check_str("name", name)
    _conf.check_str("url", url, allow_empty=False)
    _conf.check_str("filename", filename, allow_empty=False)
    if ttl is None:
        ttl = 2**63
    check_hashes = _make_hash_checker(
        dict(sha1=sha1, sha256=sha256, sha512=sha512)
    )
    conf = _conf.configure(**kwargs)

    return _install.install_file(
        "misc-files",
        name,
        url,
        filename,
        conf,
        ttl=ttl,
        checkfunc=check_hashes,
    )


def cache_package(
    name: str,
    url: str,
    *,
    sha1: str | None = None,
    sha256: str | None = None,
    sha512: str | None = None,
    **kwargs: Unpack[ConfigKwargs],
) -> Path:
    """
    Install any package into the cache, downloading and extracting if
    necessary.

    Parameters are the same as for cache_jdk() (JDK-specific parameters are
    ignored), with the following additions.

    Parameters
    ----------
    name : str
        Name to display in case of showing progress.
    url : str
        The URL of the file resource. The scheme must be tgz+https or
        zip+https.
    sha1 : str, optional
        SHA-1 hash that the downloaded file must match.
    sha256 : str, optional
        SHA-256 hash that the downloaded file must match.
    sha512 : str, optional
        SHA-512 hash that the downloaded file must match.

    Returns
    -------
    pathlib.Path
        Path to the cached directory into which the package was extracted.

    Raises
    ------
    ConfigError
        If configuration or URL is invalid.
    InstallError
        If download, hash check, or extraction fails.

    Notes
    -----
    The check for SHA-1/SHA-256/SHA-512 hashes is only performed (on the
    unextracted archive) after a download; it is not performed if the directory
    already exists in the cache.
    """
    _conf.check_str("name", name)
    _conf.check_str("url", url, allow_empty=False)
    check_hashes = _make_hash_checker(
        dict(sha1=sha1, sha256=sha256, sha512=sha512)
    )
    conf = _conf.configure(**kwargs)

    if not url.startswith(("tgz+http", "zip+http")):
        if url.endswith(".tgz"):
            url = "tgz+http" + url.removeprefix("http")
        elif url.endswith(".zip"):
            url = "zip+http" + url.removeprefix("http")
        else:
            raise ConfigError(
                f"Cannot handle {url!r} URL (must be tgz+https or zip+https)"
            )

    try:
        return _install.install_dir(
            "misc-dirs", name, url, conf, checkfunc=check_hashes
        )
    except UnsupportedFormatError as e:
        raise ConfigError(str(e)) from e


def _get_vendors(**kwargs: Unpack[ConfigKwargs]) -> set[str]:
    conf = _conf.configure(**kwargs)
    index = _index.jdk_index(conf)
    return {
        vendor.replace("jdk@", "")
        for osys in index
        for arch in index[osys]
        for vendor in index[osys][arch]
    }


def _get_jdks(
    *,
    vendor: str | None = None,
    version: str | None = None,
    cached_only: bool = True,
    **kwargs: Unpack[ConfigKwargs],
) -> list[str]:
    jdk = kwargs.pop("jdk", None)
    if jdk:
        parsed_vendor, parsed_version = _conf.parse_vendor_version(jdk)
        vendor = vendor or parsed_vendor or None
        version = version or parsed_version or None

    # Handle "all vendors" before creating Configuration.
    if vendor is None:
        return [
            jdk
            for v in sorted(_get_vendors())
            for jdk in _get_jdks(
                vendor=v,
                version=version,
                cached_only=cached_only,
                **kwargs,
            )
        ]

    conf = _conf.configure(vendor=vendor, version=version, **kwargs)
    index = _index.jdk_index(conf)
    jdks = _index.available_jdks(index, conf)
    versions = _index._get_versions(jdks, conf)
    matched = _index._match_versions(conf.vendor, versions, conf.version)

    if cached_only:
        # Filter matches by existing key directories.
        def is_cached(v: str) -> bool:
            url = _index.jdk_url(index, conf, v)
            key = (_jdk._JDK_KEY_PREFIX, _cache._key_for_url(url))
            keydir = _cache._key_directory(conf.cache_dir, key)
            return keydir.exists()

        matched = {k: v for k, v in matched.items() if is_cached(v)}

    class VersionElement:
        def __init__(self, value: int | str) -> None:
            self.value = value

        def __eq__(self, other: VersionElement) -> bool:  # type: ignore[override]
            if isinstance(self.value, int) and isinstance(other.value, int):
                return self.value == other.value
            return str(self.value) == str(other.value)

        def __lt__(self, other: VersionElement) -> bool:
            if isinstance(self.value, int) and isinstance(other.value, int):
                return self.value < other.value
            return str(self.value) < str(other.value)

    def version_key(
        version_tuple: tuple[tuple[int | str, ...], str],
    ) -> tuple[VersionElement, ...]:
        return tuple(VersionElement(elem) for elem in version_tuple[0])

    return [
        f"{conf.vendor}:{v}"
        for k, v in sorted(matched.items(), key=version_key)
    ]


def _make_hash_checker(
    hashes: dict[str, str | None],
) -> Callable[[Path], None]:
    checks = [
        (hashes.pop("sha1", None), hashlib.sha1),
        (hashes.pop("sha256", None), hashlib.sha256),
        (hashes.pop("sha512", None), hashlib.sha512),
    ]

    def check(filepath: Path) -> None:
        for hash, hasher in checks:
            if hash:
                _hasher = hasher()
                try:
                    with open(filepath, "rb") as infile:
                        while True:
                            chunk = infile.read(16384)
                            if not len(chunk):
                                break
                            _hasher.update(chunk)
                except OSError as e:
                    raise InstallError(
                        f"Failed to read file for hash verification: {e}"
                    ) from e
                if _hasher.hexdigest().lower() != hash.lower():
                    raise InstallError("Hash does not match")

    return check


@contextmanager
def _env_var_set(name: str, value: str) -> Iterator[None]:
    old_value = os.environ.get(name, None)
    os.environ[name] = value
    try:
        yield
    finally:
        if old_value is not None:
            os.environ[name] = old_value
        else:
            del os.environ[name]
