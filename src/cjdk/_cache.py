# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import sys
import time
import urllib.parse
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from . import _progress, _utils

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
from ._exceptions import ConfigError, InstallError

__all__ = [
    "atomic_file",
    "permanent_directory",
]


def _key_for_url(url: str | urllib.parse.ParseResult) -> str:
    """
    Return a cache key suitable to cache content retrieved from the given URL.
    """
    if not isinstance(url, tuple):
        url = urllib.parse.urlparse(url, allow_fragments=False)
    if url.params or url.query or url.fragment:
        raise ConfigError(
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
    def percent_reencode(item: str) -> str:
        try:
            decoded = urllib.parse.unquote(item, errors="strict")
            return urllib.parse.quote(decoded, safe="+-._", errors="strict")
        except UnicodeDecodeError as e:
            raise ConfigError(
                f"Invalid percent encoding in URL component '{item}': {e}"
            ) from e

    normalized = "/".join(percent_reencode(i) for i in items)

    hasher = hashlib.sha1(usedforsecurity=False)
    hasher.update(normalized.encode())
    return hasher.hexdigest().lower()


def atomic_file(
    prefix: str,
    key_url: str,
    filename: str,
    fetchfunc: Callable[[Path], None],
    *,
    cache_dir: Path,
    ttl: float,
    timeout_for_fetch_elsewhere: float = 10,
    timeout_for_read_elsewhere: float = 2.5,
) -> Path:
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
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise InstallError(
            f"Failed to create cache directory {cache_dir}: {e}"
        ) from e

    keydir = _key_directory(cache_dir, key)
    target = keydir / filename
    if not _file_exists_and_is_fresh(target, ttl):
        with _create_key_tmpdir(cache_dir, key) as tmpdir:
            if tmpdir:
                filepath = tmpdir / filename
                try:
                    fetchfunc(filepath)
                    _utils.swap_in_file(
                        target,
                        filepath,
                        timeout=timeout_for_read_elsewhere,
                    )
                    _add_url_file(keydir, key_url)
                finally:
                    _utils.unlink_tempfile(filepath)
            else:  # Somebody else is currently fetching
                _wait_for_dir_to_vanish(
                    _key_tmpdir(cache_dir, key),
                    timeout=timeout_for_fetch_elsewhere,
                )
                if not _file_exists_and_is_fresh(target, ttl=2**63):
                    raise InstallError(
                        f"Another process was fetching {target} but the file is not present; "
                        f"the other process may have failed or been interrupted."
                    )
    return target


def permanent_directory(
    prefix: str,
    key_url: str,
    fetchfunc: Callable[[Path], None],
    *,
    cache_dir: Path,
    timeout_for_fetch_elsewhere: float = 60,
) -> Path:
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
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise InstallError(
            f"Failed to create cache directory {cache_dir}: {e}"
        ) from e

    keydir = _key_directory(cache_dir, key)
    if not keydir.is_dir():
        with _create_key_tmpdir(cache_dir, key) as tmpdir:
            if tmpdir:
                try:
                    fetchfunc(tmpdir)
                    _move_in_fetched_directory(keydir, tmpdir)
                    _add_url_file(keydir, key_url)
                finally:
                    _utils.rmtree_tempdir(tmpdir)
            else:  # Somebody else is currently fetching
                _wait_for_dir_to_vanish(
                    _key_tmpdir(cache_dir, key),
                    timeout=timeout_for_fetch_elsewhere,
                )
                if not keydir.is_dir():
                    raise InstallError(
                        f"Another process was fetching {keydir} but the directory is not present; "
                        f"the other process may have failed or been interrupted"
                    )
    return keydir


def _file_exists_and_is_fresh(file: Path, ttl: float) -> bool:
    if not file.is_file():
        return False
    now = time.time()
    try:
        mtime = file.stat().st_mtime
    except OSError:
        return False
    expiration = mtime + ttl
    # To avoid all possibilities of races, err on the side of considering the
    # file stale when the difference is less than 1 second.
    return now + 1.0 < expiration


@contextmanager
def _create_key_tmpdir(
    cache_dir: Path, key: tuple[str, str]
) -> Iterator[Path | None]:
    tmpdir = _key_tmpdir(cache_dir, key)
    try:
        tmpdir.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise InstallError(
            f"Failed to create cache directory {tmpdir.parent}: {e}"
        ) from e

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
            _utils.rmtree_tempdir(tmpdir)


def _key_directory(cache_dir: Path, key: tuple[str, str]) -> Path:
    return cache_dir / "v0" / Path(*key)


def _key_tmpdir(cache_dir: Path, key: tuple[str, str]) -> Path:
    return cache_dir / "v0" / Path("fetching", *key)


def _move_in_fetched_directory(target: Path, tmpdir: Path) -> None:
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise InstallError(
            f"Failed to create cache directory {target.parent}: {e}"
        ) from e
    try:
        tmpdir.replace(target)
    except OSError as e:
        raise InstallError(f"Failed to move {tmpdir} to {target}: {e}") from e


def _add_url_file(keydir: Path, key_url: str) -> None:
    url_file = keydir.parent / (keydir.name + ".url")
    try:
        with open(url_file, "w") as f:
            f.write(key_url)
    except OSError as e:
        raise InstallError(f"Failed to write URL file {url_file}: {e}") from e


def _wait_for_dir_to_vanish(
    directory: Path, timeout: float, progress: bool = True
) -> None:
    print(
        "cjdk: Another process is currently downloading the same file",
        file=sys.stderr,
    )
    print(
        f"cjdk: If you are sure this is not the case (e.g., previous download crashed), try again after deleting the directory {directory}",
        file=sys.stderr,
    )
    with _progress.indefinite(
        enabled=progress, text="Already downloading; waiting"
    ) as update_pbar:
        for wait_seconds in _utils.backoff_seconds(0.001, 0.5, timeout):
            if not directory.is_dir():
                return
            if wait_seconds < 0:
                raise InstallError(
                    f"Timeout while waiting for directory {directory} to disappear"
                )
            time.sleep(wait_seconds)
            update_pbar()
