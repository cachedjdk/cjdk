# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import hashlib
import os
from contextlib import contextmanager

from . import _conf, _install, _jdk

__all__ = [
    "cache_jdk",
    "java_env",
    "java_home",
    "cache_file",
    "cache_package",
]


def cache_jdk(*, vendor=None, version=None, **kwargs):
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
    """
    conf = _conf.configure(vendor=vendor, version=version, **kwargs)
    _jdk.install_jdk(conf)


def java_home(*, vendor=None, version=None, **kwargs):
    """
    Return the JDK home directory for the given JDK, installing if necessary.

    Parameters are the same as for cache_jdk().

    Returns
    -------
    pathlib.Path
        The JDK home directory satisfying the requested parameters.
    """
    conf = _conf.configure(vendor=vendor, version=version, **kwargs)
    path = _jdk.install_jdk(conf)
    return _jdk.find_home(path)


@contextmanager
def java_env(*, vendor=None, version=None, add_bin=True, **kwargs):
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


def cache_file(name, url, filename, **kwargs):
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
    ttl : int
        Time to live (in seconds) for the cached file resource.
    sha1 : str
        SHA-1 hash that the downloaded file must match.
    sha256 : str
        SHA-256 hash that the downloaded file must match.
    sha512 : str
        SHA-512 hash that the downloaded file must match.

    Returns
    -------
    pathlib.Path
        Path to the cached file resource, whose final component is the given
        filename.

    Notes
    -----
    The check for SHA-1/SHA-256/SHA-512 hashes is only performed after a
    download; it is not performed if the file already exists in the cache.
    """
    ttl = kwargs.pop("ttl", None)
    if ttl is None:
        ttl = 2**63
    check_hashes = _make_hash_checker(kwargs)
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


def cache_package(name, url, **kwargs):
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
    sha1 : str
        SHA-1 hash that the downloaded file must match.
    sha256 : str
        SHA-256 hash that the downloaded file must match.
    sha512 : str
        SHA-512 hash that the downloaded file must match.

    Returns
    -------
    pathlib.Path
        Path to the cached directory into which the package was extracted.

    Notes
    -----
    The check for SHA-1/SHA-256/SHA-512 hashes is only performed (on the
    unextracted archive) after a download; it is not performed if the directory
    already exists in the cache.
    """
    check_hashes = _make_hash_checker(kwargs)
    conf = _conf.configure(**kwargs)

    return _install.install_dir(
        "misc-dirs", name, url, conf, checkfunc=check_hashes
    )


def _make_hash_checker(hashes):
    checks = [
        (hashes.pop("sha1", None), hashlib.sha1),
        (hashes.pop("sha256", None), hashlib.sha256),
        (hashes.pop("sha512", None), hashlib.sha512),
    ]

    def check(filepath):
        for hash, hasher in checks:
            if hash:
                hasher = hasher()
                with open(filepath, "rb") as infile:
                    while True:
                        bytes = infile.read(16384)
                        if not len(bytes):
                            break
                        hasher.update(bytes)
                if hasher.hexdigest().lower() != hash.lower():
                    raise ValueError("Hash does not match")

    return check


@contextmanager
def _env_var_set(name, value):
    old_value = os.environ.get(name, None)
    os.environ[name] = value
    try:
        yield
    finally:
        if old_value:
            os.environ[name] = old_value
        else:
            del os.environ[name]
