# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import os
import shutil
import sys
import time

__all__ = [
    "backoff_seconds",
    "rmtree",
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

    def retry_unlink(func, path, excinfo):
        if func is os.unlink:
            unlink_file(path, timeout=0)  # Try again with our special version

    for wait_seconds in backoff_seconds(0.001, 0.5, timeout):
        try:
            shutil.rmtree(path, onexc=retry_unlink)
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
