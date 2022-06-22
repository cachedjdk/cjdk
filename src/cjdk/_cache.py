# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import contextlib
import os
import shutil
import sys
import time
import urllib
from pathlib import Path

from tqdm.auto import tqdm

__all__ = [
    "default_cachedir",
    "url_to_key",
    "atomic_file",
    "permanent_directory",
]


_FOREVER = 2**63  # seconds


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


def url_to_key(url):
    """
    Return a cache key suitable to cache content retrieved from the given URL.

    For example, https://example.com/a/b.json -> ("example.com", "a", "b.json")
    """
    if not isinstance(url, tuple):
        url = urllib.parse.urlparse(url, allow_fragments=False)
    if url.params or url.query or url.fragment:
        raise ValueError(
            f"URL should not have parameters, query, or fragment: {url}"
        )
    items = (url.netloc,) + tuple(url.path.strip("/").split("/"))

    # Sometimes URL components contain percent-encoded characters. While this
    # is not usually an issue for file naming, let's normalize by decoding and
    # re-encoding only problem characters.
    # Windows disallows < > : " / \ | ? * in filenames; Unix disallows /
    # The only likely non-alphanumeric characters occurring in JDK URL path
    # components are + - . _
    # And urllib never encodes - . _ ~
    # In practice, this usually serves only to normalize '+' and the case of
    # percent encoding hex digits.
    def percent_reencode(item):
        decoded = urllib.parse.unquote(item, errors="strict")
        return urllib.parse.quote(decoded, safe="+-._", errors="strict")

    return tuple(percent_reencode(i) for i in items)


def atomic_file(
    key,
    filename,
    fetchfunc,
    ttl=None,
    cachedir=None,
    timeout_for_fetch_elsewhere=10,
    timeout_for_read_elsewhere=2.5,
):
    """
    Retrieve cached file for key, fetching with fetchfunc if necessary.

    Arguments:
    key -- The cache key; must be a tuple of strings, each safe as a URL path
           component.
    fetchfunc -- A function taking a single positional argument (the
                 destination file path). The function must populate the given
                 path with the desired file content.

    Keyword arguments:
    ttl -- Time to live for the cached file, in seconds. If the cached file
           exists but is older than the TTL, it will be re-fetched and
           replaced (default: for ever).
    cachedir -- The root cache directory (default: default_cachedir()).
    """
    if ttl is None:
        ttl = _FOREVER
    if not cachedir:
        cachedir = default_cachedir()
    elif not isinstance(cachedir, Path):
        cachedir = Path(cachedir)

    _check_key(key)
    cachedir.mkdir(parents=True, exist_ok=True)

    keydir = _key_directory(cachedir, key)
    target = keydir / filename
    if not _file_exists_and_is_fresh(target, ttl):
        with _create_key_tmpdir(cachedir, key) as tmpdir:
            if tmpdir:
                fetchfunc(tmpdir / filename)
                _swap_in_fetched_file(
                    target,
                    tmpdir / filename,
                    timeout=timeout_for_read_elsewhere,
                )
            else:  # Somebody else is currently fetching
                _wait_for_dir_to_vanish(
                    _key_tmpdir(cachedir, key),
                    timeout=timeout_for_fetch_elsewhere,
                )
                if not _file_exists_and_is_fresh(target, ttl=_FOREVER):
                    raise Exception(
                        f"Fetching of file {target} appears to have been completed elsewhere, but file does not exist"
                    )
    return target


def permanent_directory(
    key,
    fetchfunc,
    cachedir=None,
    timeout_for_fetch_elsewhere=60,
):
    """
    Retrieve cached directory for key, fetching with fetchfunc if necessary.

    Arguments:
    key -- The cache key; must be a tuple of strings, each safe as a URL path
           component.
    fetchfunc -- A function taking a single positional argument (the
                 destination directory as a pathlib.Path). The function must
                 populate the given directory with the desired cached content.

    Keyword arguments:
    cachedir -- The root cache directory (default: default_cachedir()).
    """
    if not cachedir:
        cachedir = default_cachedir()
    if not isinstance(cachedir, Path):
        cachedir = Path(cachedir)

    _check_key(key)
    cachedir.mkdir(parents=True, exist_ok=True)

    keydir = _key_directory(cachedir, key)
    if not keydir.is_dir():
        with _create_key_tmpdir(cachedir, key) as tmpdir:
            if tmpdir:
                fetchfunc(tmpdir)
                _move_in_fetched_directory(keydir, tmpdir)
            else:  # Somebody else is currently fetching
                _wait_for_dir_to_vanish(
                    _key_tmpdir(cachedir, key),
                    timeout=timeout_for_fetch_elsewhere,
                )
                if not keydir.is_dir():
                    raise Exception(
                        f"Fetching of directory {keydir} appears to have been completed elsewhere, but directory does not exist"
                    )
    return keydir


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


def _file_exists_and_is_fresh(file, ttl):
    if not file.is_file():
        return False
    now = time.time()
    mtime = file.stat().st_mtime
    expiration = mtime + ttl
    return now < expiration


@contextlib.contextmanager
def _create_key_tmpdir(cachedir, key):
    tmpdir = _key_tmpdir(cachedir, key)
    tmpdir.parent.mkdir(parents=True, exist_ok=True)

    already_exists = False
    try:
        tmpdir.mkdir()
    except FileExistsError as e:
        # Avoid yielding here, because that would mean doing stuff "while
        # handling an exception". If the stuff has an error (including
        # KeyboardInterrupt), we have a problem.
        already_exists = True

    if already_exists:
        yield None
    else:
        try:
            yield tmpdir
        finally:
            if tmpdir.is_dir():
                shutil.rmtree(tmpdir)


def _key_directory(cachedir, key):
    return cachedir / Path(*key)


def _key_tmpdir(cachedir, key):
    return cachedir / Path("fetching", *key)


def _check_key(key):
    if not key:
        raise ValueError(f"Invalid cache key: {key}")
    for item in key:
        if "/" in item or "\\" in item:
            raise ValueError(f"Invalid cache key: {key}")


def _swap_in_fetched_file(target, tmpfile, timeout):
    # On POSIX, we only need to try once to move tmpfile to target; this will
    # work even if target is opened by others, and any failure (e.g.
    # insufficient permissions) is permanent.
    # On Windows, there is the case where the file is open by others (busy); we
    # should wait a little and retry in this case. It is not possible to do
    # this cleanly, because the error we get when the target is busy is "Access
    # is denied" (PermissionError, a subclass of OSError, with .winerror = 5),
    # which is indistinguishable from the case where target permanently has bad
    # permissions.
    # But because this implementation is only intended for small files that
    # will not be kept open for long, and because permanent bad permissions is
    # not expected in the typical use case, we can do something that almost
    # always results in the intended behavior.
    WINDOWS_ERROR_ACCESS_DENIED = 5

    target.parent.mkdir(parents=True, exist_ok=True)
    for wait_seconds in _backoff_seconds(0.001, 0.5, timeout):
        try:
            tmpfile.replace(target)
        except OSError as e:
            if (
                hasattr(e, "winerror")
                and e.winerror == WINDOWS_ERROR_ACCESS_DENIED
                and wait_seconds > 0
            ):
                time.sleep(wait_seconds)
                continue
            raise
        else:
            return


def _move_in_fetched_directory(target, tmpdir):
    target.parent.mkdir(parents=True, exist_ok=True)
    tmpdir.replace(target)


def _wait_for_dir_to_vanish(directory, timeout, progress=True):
    for wait_seconds in _backoff_seconds(
        0.001, 0.5, timeout, progress=progress
    ):
        if not directory.is_dir():
            return
        if wait_seconds < 0:
            raise Exception(
                f"Timeout while waiting for directory {directory} to disappear"
            )
        time.sleep(wait_seconds)


def _backoff_seconds(
    initial_interval, max_interval, max_total, factor=1.5, progress=True
):
    """
    Yield intervals to sleep after repeated attempts with exponential backoff.

    The last-yielded value is -1. When -1 is received, the caller should make
    the final attempt before giving up.
    """
    assert initial_interval > 0
    assert max_total >= 0
    assert factor > 1
    with tqdm(
        desc="Waiting for download elsewhere",
        # Intentionally not showing total; percentage makes no sense here
        disable=(None if progress else True),
        unit="s",
    ) as tq:
        total = 0
        next_interval = initial_interval
        while max_total > 0:
            next_total = total + next_interval
            if next_total > max_total:
                remaining = max_total - total
                if remaining > 0.01:
                    yield remaining
                    tq.update(remaining)
                break
            yield next_interval
            tq.update(next_interval)
            total = next_total
            next_interval *= factor
            if next_interval > max_interval:
                next_interval = max_interval
        yield -1
