# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import os
import shutil
import sys
import time

from . import _progress

__all__ = [
    "backoff_seconds",
    "rmtree",
    "swap_in_file",
    "unlink_file",
]

# ERROR_ACCESS_DENIED (5) and ERROR_SHARING_VIOLATION (32)
_WIN_OPEN_FILE_ERRS = (5, 32)


def backoff_seconds(initial_interval, max_interval, max_total, factor=1.5):
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


def rmtree(path, timeout=2.5):
    # Try extra hard to clean up a temporary directory.

    if sys.version_info >= (3, 12):

        def retry_unlink(func, path, exc):
            if func is os.unlink:
                unlink_file(path, timeout=0)
            else:
                raise exc

        rmtree_kwargs = {"onexc": retry_unlink}
    else:

        def retry_unlink(func, path, exc_info):
            if func is os.unlink:
                unlink_file(path, timeout=0)
            else:
                raise exc_info[1].with_traceback(exc_info[2])

        rmtree_kwargs = {"onerror": retry_unlink}

    for wait_seconds in backoff_seconds(0.001, 0.5, timeout):
        try:
            shutil.rmtree(path, **rmtree_kwargs)
        except OSError as e:
            if (
                hasattr(e, "winerror")
                and e.winerror in _WIN_OPEN_FILE_ERRS
                and wait_seconds > 0
            ):
                time.sleep(wait_seconds)
                continue
            raise
        else:
            return


def unlink_file(path, timeout=2.5):
    if sys.platform != "win32":
        return os.unlink(path)

    # On Windows, we sometimes encounter errors when trying to delete a file
    # that we just closed after writing. This is due to Antivirus opening the
    # file to scan it. Microsoft Defender Antivirus is said to use
    # FILE_SHARE_DELETE, but os.unlink() calls DeleteFileW(), which does not
    # use FILE_SHARE_DELETE; since the check is bidirectional, it fails.
    # So use Win32 API calls that will not have this problem.

    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32
    kernel32.CreateFileW.restype = wintypes.HANDLE

    DELETE = 0x00010000
    FILE_SHARE_READ = 0x01
    FILE_SHARE_WRITE = 0x02
    FILE_SHARE_DELETE = 0x04
    OPEN_EXISTING = 3
    FILE_FLAG_DELETE_ON_CLOSE = 0x04000000
    INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

    def do_unlink(path):
        handle = INVALID_HANDLE_VALUE
        try:
            handle = kernel32.CreateFileW(
                str(path),
                DELETE,
                FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                None,
                OPEN_EXISTING,
                FILE_FLAG_DELETE_ON_CLOSE,
                None,
            )
            if handle == INVALID_HANDLE_VALUE:
                os.unlink(path)  # Let it raise an appropriate error.
        finally:
            if handle != INVALID_HANDLE_VALUE:
                kernel32.CloseHandle(handle)

    for wait_seconds in backoff_seconds(0.001, 0.5, timeout):
        try:
            do_unlink(path)
        except OSError as e:
            if (
                hasattr(e, "winerror")
                and e.winerror in _WIN_OPEN_FILE_ERRS
                and wait_seconds > 0
            ):
                time.sleep(wait_seconds)
                continue
            raise
        else:
            return


def swap_in_file(target, tmpfile, timeout, progress=False):
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
    target.parent.mkdir(parents=True, exist_ok=True)
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
                raise
            else:
                return
