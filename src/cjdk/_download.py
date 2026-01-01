# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import contextlib
import os
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests

from . import _progress

__all__ = [
    "download_and_extract",
    "download_file",
]


def _unlink_file(path):
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


def download_and_extract(
    destdir,
    url,
    *,
    checkfunc=None,
    progress=True,
    _allow_insecure_for_testing=False,
):
    """
    Download zip or tgz archive and extract to destdir.

    checkfunc is called on the archive temporary file.
    """
    scheme = urlparse(url).scheme
    try:
        ext, http = scheme.split("+")
    except ValueError as err:
        raise NotImplementedError(f"Cannot handle {scheme} URL") from err
    if http != "https" and not _allow_insecure_for_testing:
        raise NotImplementedError(f"Cannot handle {http} (must be https)")
    try:
        extract = {"zip": _extract_zip, "tgz": _extract_tgz}[ext]
    except KeyError as err:
        raise NotImplementedError(
            f"Cannot handle compression type {ext}"
        ) from err

    url = http + url.removeprefix(scheme)
    with tempfile.TemporaryDirectory(prefix="cjdk-") as tempd:
        file = Path(tempd) / f"archive.{ext}"
        download_file(
            file,
            url,
            checkfunc=checkfunc,
            progress=progress,
            _allow_insecure_for_testing=_allow_insecure_for_testing,
        )
        extract(destdir, file, progress)


def download_file(
    dest,
    url,
    *,
    checkfunc=None,
    progress=False,
    _allow_insecure_for_testing=False,
):
    """
    Download any file at URL and place at dest.

    checkfunc is called on dest.
    """
    if not _allow_insecure_for_testing:
        scheme = urlparse(url).scheme
        if scheme != "https":
            raise NotImplementedError(
                f"Cannot handle {scheme} (must be https)"
            )

    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            total = response.headers.get("content-length", None)
            total = int(total) if total else None
            with open(dest, "wb") as outfile:
                for chunk in _progress.data_transfer(
                    total,
                    response.iter_content(chunk_size=16384),
                    enabled=progress,
                    text="Download",
                ):
                    outfile.write(chunk)

        if checkfunc:
            checkfunc(dest)
    except BaseException:
        with contextlib.suppress(OSError):
            _unlink_file(dest)
        raise


def _extract_zip(destdir, srcfile, progress=True):
    with zipfile.ZipFile(srcfile) as zf:
        infolist = zf.infolist()
        for member in _progress.iterate(
            infolist, enabled=progress, text="Extract"
        ):
            extracted = Path(zf.extract(member, destdir))

            # Recover executable bits; see https://stackoverflow.com/a/46837272
            if member.create_system == 3 and extracted.is_file():
                mode = (member.external_attr >> 16) & 0o111
                extracted.chmod(extracted.stat().st_mode | mode)


def _extract_tgz(destdir, srcfile, progress=True):
    filter_kwargs = {} if sys.version_info < (3, 12) else {"filter": "tar"}
    with tarfile.open(srcfile, "r:gz", bufsize=65536) as tf:
        for member in _progress.iterate(tf, enabled=progress, text="Extract"):
            tf.extract(member, destdir, **filter_kwargs)
