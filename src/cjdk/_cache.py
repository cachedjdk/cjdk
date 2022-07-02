# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import shutil
import time
import urllib
from contextlib import contextmanager
from pathlib import Path

from tqdm.auto import tqdm

from . import _compat

__all__ = [
    "atomic_file",
    "permanent_directory",
]


def _key_for_url(url):
    """
    Return a cache key suitable to cache content retrieved from the given URL.
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

    normalized = "/".join(percent_reencode(i) for i in items)

    hasher = _compat.sha1_not_for_security()
    hasher.update(normalized.encode())
    return hasher.hexdigest().lower()


def atomic_file(
    prefix,
    key_url,
    filename,
    fetchfunc,
    *,
    cache_dir,
    ttl,
    timeout_for_fetch_elsewhere=10,
    timeout_for_read_elsewhere=2.5,
):
    """
    Retrieve cached file for key, fetching with fetchfunc if necessary.

    Arguments:
    prefix -- Cache directory prefix (string)
    key_url -- The URL used as cache key. The netloc and path parts are
               normalized and hashed to generate a key.
    fetchfunc -- A function taking a single positional argument (the
                 destination file path). The function must populate the given
                 path with the desired file content.
    cache_dir -- The root cache directory.
    ttl -- Time to live for the cached file, in seconds. If the cached file
           exists but is older than the TTL, it will be re-fetched and
           replaced (default: for ever).
    """
    if not isinstance(cache_dir, Path):
        cache_dir = Path(cache_dir)

    key = (prefix, _key_for_url(key_url))
    cache_dir.mkdir(parents=True, exist_ok=True)

    keydir = _key_directory(cache_dir, key)
    target = keydir / filename
    if not _file_exists_and_is_fresh(target, ttl):
        with _create_key_tmpdir(cache_dir, key) as tmpdir:
            if tmpdir:
                fetchfunc(tmpdir / filename)
                _swap_in_fetched_file(
                    target,
                    tmpdir / filename,
                    timeout=timeout_for_read_elsewhere,
                )
                _add_url_file(keydir, key_url)
            else:  # Somebody else is currently fetching
                _wait_for_dir_to_vanish(
                    _key_tmpdir(cache_dir, key),
                    timeout=timeout_for_fetch_elsewhere,
                )
                if not _file_exists_and_is_fresh(target, ttl=2**63):
                    raise Exception(
                        f"Fetching of file {target} appears to have been completed elsewhere, but file does not exist"
                    )
    return target


def permanent_directory(
    prefix,
    key_url,
    fetchfunc,
    *,
    cache_dir,
    timeout_for_fetch_elsewhere=60,
):
    """
    Retrieve cached directory for key, fetching with fetchfunc if necessary.

    Arguments:
    prefix -- Cache directory prefix (string)
    key_url -- The URL used as cache key. The netloc and path parts are
               normalized and hashed to generate a key.
    fetchfunc -- A function taking a single positional argument (the
                 destination directory as a pathlib.Path). The function must
                 populate the given directory with the desired cached content.
    cache_dir -- The root cache directory.
    """
    if not isinstance(cache_dir, Path):
        cache_dir = Path(cache_dir)

    key = (prefix, _key_for_url(key_url))
    cache_dir.mkdir(parents=True, exist_ok=True)

    keydir = _key_directory(cache_dir, key)
    if not keydir.is_dir():
        with _create_key_tmpdir(cache_dir, key) as tmpdir:
            if tmpdir:
                fetchfunc(tmpdir)
                _move_in_fetched_directory(keydir, tmpdir)
                _add_url_file(keydir, key_url)
            else:  # Somebody else is currently fetching
                _wait_for_dir_to_vanish(
                    _key_tmpdir(cache_dir, key),
                    timeout=timeout_for_fetch_elsewhere,
                )
                if not keydir.is_dir():
                    raise Exception(
                        f"Fetching of directory {keydir} appears to have been completed elsewhere, but directory does not exist"
                    )
    return keydir


def _file_exists_and_is_fresh(file, ttl):
    if not file.is_file():
        return False
    now = time.time()
    mtime = file.stat().st_mtime
    expiration = mtime + ttl
    # To avoid all possibilities of races, err on the side of considering the
    # file stale when the difference is less than 1 second.
    return now + 1.0 < expiration


@contextmanager
def _create_key_tmpdir(cache_dir, key):
    tmpdir = _key_tmpdir(cache_dir, key)
    tmpdir.parent.mkdir(parents=True, exist_ok=True)

    already_exists = False
    try:
        tmpdir.mkdir()
    except FileExistsError:
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


def _key_directory(cache_dir, key):
    return cache_dir / "v0" / Path(*key)


def _key_tmpdir(cache_dir, key):
    return cache_dir / "v0" / Path("fetching", *key)


def _swap_in_fetched_file(target, tmpfile, timeout, progress=False):
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
    with tqdm(
        desc="Waiting for another process",
        # Intentionally not showing total; percentage makes no sense here
        disable=(None if progress else True),
        unit="s",
        delay=0.5,
    ) as tq:
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
                    tq.update(wait_seconds)
                    continue
                raise
            else:
                return


def _move_in_fetched_directory(target, tmpdir):
    target.parent.mkdir(parents=True, exist_ok=True)
    tmpdir.replace(target)


def _add_url_file(keydir, key_url):
    with open(keydir.parent / (keydir.name + ".url"), "w") as f:
        f.write(key_url)


def _wait_for_dir_to_vanish(directory, timeout, progress=True):
    with tqdm(
        desc="Waiting for another download",
        # Intentionally not showing total; percentage makes no sense here
        disable=(None if progress else True),
        unit="s",
    ) as tq:
        for wait_seconds in _backoff_seconds(0.001, 0.5, timeout):
            if not directory.is_dir():
                return
            if wait_seconds < 0:
                raise Exception(
                    f"Timeout while waiting for directory {directory} to disappear"
                )
            time.sleep(wait_seconds)
            tq.update(wait_seconds)


def _backoff_seconds(initial_interval, max_interval, max_total, factor=1.5):
    """
    Yield intervals to sleep after repeated attempts with exponential backoff.

    The last-yielded value is -1. When -1 is received, the caller should make
    the final attempt before giving up.
    """
    assert initial_interval > 0
    assert max_total >= 0
    assert factor > 1
    total = 0
    next_interval = initial_interval
    while max_total > 0:
        next_total = total + next_interval
        if next_total > max_total:
            remaining = max_total - total
            if remaining > 0.01:
                yield remaining
            break
        yield next_interval
        total = next_total
        next_interval *= factor
        if next_interval > max_interval:
            next_interval = max_interval
    yield -1
