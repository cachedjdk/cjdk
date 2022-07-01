# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import os
from contextlib import contextmanager

from . import _conf, _jdk

__all__ = [
    "install_jdk",
    "java_env",
    "java_home",
]


def install_jdk(*, vendor=None, version=None, **kwargs):
    """
    Download and install the given JDK if it is not already cached.

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

    Parameters are the same as for install_jdk().

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

    Parameters are the same as for install_jdk(), with the following addition.

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


@contextmanager
def _env_var_set(name, value):
    old_value = os.environ.get(name, None)
    os.environ[name] = value
    yield
    if old_value:
        os.environ[name] = old_value
    else:
        del os.environ[name]
