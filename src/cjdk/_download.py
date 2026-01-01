# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import contextlib
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests

from . import _progress, _utils

__all__ = [
    "download_and_extract",
    "download_file",
]


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
        _utils.unlink_file(file)


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
            _utils.unlink_file(dest)
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
