# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT
from __future__ import annotations

import os
import shutil
import time
from typing import TYPE_CHECKING

from . import _progress
from ._exceptions import InstallError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

__all__ = [
    "backoff_seconds",
    "rmtree_tempdir",
    "swap_in_file",
    "unlink_tempfile",
]

# ERROR_ACCESS_DENIED (5) and ERROR_SHARING_VIOLATION (32)
_WIN_OPEN_FILE_ERRS = (5, 32)


def backoff_seconds(
    initial_interval: float,
    max_interval: float,
    max_total: float,
    factor: float = 1.5,
) -> Iterator[float]:
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


def rmtree_tempdir(path: Path, timeout: float = 2.5) -> None:
    # Try extra hard to clean up a temporary directory. See comment in
    # unlink_tempfile() for why.

    for wait_seconds in backoff_seconds(0.001, 0.5, timeout):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
        except OSError as e:
            if (
                hasattr(e, "winerror")
                and e.winerror in _WIN_OPEN_FILE_ERRS
                and wait_seconds > 0
            ):
                time.sleep(wait_seconds)
                continue
            raise InstallError(
                f"Failed to remove directory {path}: {e}"
            ) from e
        else:
            return


def unlink_tempfile(path: Path, timeout: float = 2.5) -> None:
    # On Windows, we may encounter errors when trying to delete a file that we
    # just closed after writing, due to Antivirus opening the file to scan it.
    # Microsoft Defender Antivirus is said to use FILE_SHARE_DELETE, but
    # os.unlink() calls DeleteFileW(), which does not use FILE_SHARE_DELETE;
    # since the check is bidirectional, it fails.
    #
    # (To be clear, this is probably rare and the exact conditions are unknown;
    # Also I have not actually observed it happening.)
    #
    # So we could use different Win32 API calls, namely CreateFile(path,
    # DELETE, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL,
    # OPEN_EXISTING, FILE_FLAG_DELETE_ON_CLOSE, NULL) and then CloseHandle().
    # This should succeed on files being scanned.
    #
    # However, that method only marks the file for deleteion; actual deletion
    # happens once all processes close the file. This is a problem, because we
    # need to do the next thing, which is often to delete the parent directory
    # of the file. So we need to wait for the file to go away.
    #
    # And as long as we're waiting anyway, we can wait for regular deletion to
    # succeed, so we don't need to use Win32 API calls directly.

    for wait_seconds in backoff_seconds(0.001, 0.5, timeout):
        try:
            if os.path.exists(path):
                os.unlink(path)
        except OSError as e:
            if (
                hasattr(e, "winerror")
                and e.winerror in _WIN_OPEN_FILE_ERRS
                and wait_seconds > 0
            ):
                time.sleep(wait_seconds)
                continue
            raise InstallError(f"Failed to delete file {path}: {e}") from e
        else:
            return


def swap_in_file(
    target: Path, tmpfile: Path, timeout: float, progress: bool = False
) -> None:
    # On POSIX, we only need to try once to move tmpfile to target; this will
    # work even if target is opened by others, and any failure (e.g.
    # insufficient permissions) is permanent.
    # On Windows, there is the case where the file is open by others (busy); we
    # should wait a little and retry in this case. It is not possible to do
    # this cleanly, because the error we get when the target is busy is often
    # "Access is denied" (PermissionError, a subclass of OSError, with
    # .winerror = 5), which is indistinguishable from the case where target
    # permanently has bad permissions.
    # But because this implementation is only intended for small files that
    # will not be kept open for long, and because permanent bad permissions is
    # not expected in the typical use case, we can do something that almost
    # always results in the intended behavior.
    # Note that this is in a different category from rmtree() and unlink_file()
    # in that it is adding robustness to the case of cached files being
    # accessed by other programs, as opposed to cleaning up internal cjdk
    # files.
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise InstallError(
            f"Failed to create directory {target.parent}: {e}"
        ) from e
    with _progress.indefinite(
        enabled=progress, text="File busy; waiting"
    ) as update_pbar:
        for wait_seconds in backoff_seconds(0.001, 0.5, timeout):
            try:
                tmpfile.replace(target)
            except OSError as e:
                if (
                    hasattr(e, "winerror")
                    and e.winerror in _WIN_OPEN_FILE_ERRS
                    and wait_seconds > 0
                ):
                    time.sleep(wait_seconds)
                    update_pbar()
                    continue
                raise InstallError(
                    f"Failed to move {tmpfile} to {target}: {e}"
                ) from e
            else:
                return
