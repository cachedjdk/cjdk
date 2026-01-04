# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT
from __future__ import annotations

import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import requests

if TYPE_CHECKING:
    from collections.abc import Callable

from . import _progress, _utils
from ._exceptions import InstallError, UnsupportedFormatError

__all__ = [
    "download_and_extract",
    "download_file",
]


def download_and_extract(
    destdir: Path,
    url: str,
    *,
    checkfunc: Callable[[Path], None] | None = None,
    progress: bool = True,
    _allow_insecure_for_testing: bool = False,
) -> None:
    """
    Download zip or tgz archive and extract to destdir.

    checkfunc is called on the archive temporary file.
    """
    scheme = urlparse(url).scheme
    try:
        ext, http = scheme.split("+")
    except ValueError as err:
        raise UnsupportedFormatError(f"Cannot handle {scheme} URL") from err
    if http != "https" and not _allow_insecure_for_testing:
        raise UnsupportedFormatError(f"Cannot handle {http} (must be https)")
    try:
        extract = {"zip": _extract_zip, "tgz": _extract_tgz}[ext]
    except KeyError as err:
        raise UnsupportedFormatError(
            f"Cannot handle compression type {ext}"
        ) from err

    url = http + url.removeprefix(scheme)
    with tempfile.TemporaryDirectory(prefix="cjdk-") as tempd:
        file = Path(tempd) / f"archive.{ext}"
        try:
            download_file(
                file,
                url,
                checkfunc=checkfunc,
                progress=progress,
                _allow_insecure_for_testing=_allow_insecure_for_testing,
            )
            extract(destdir, file, progress)
        finally:
            _utils.unlink_tempfile(file)


def download_file(
    dest: Path,
    url: str,
    *,
    checkfunc: Callable[[Path], None] | None = None,
    progress: bool = False,
    _allow_insecure_for_testing: bool = False,
) -> None:
    """
    Download any file at URL and place at dest.

    checkfunc is called on dest.
    """
    if not _allow_insecure_for_testing:
        scheme = urlparse(url).scheme
        if scheme != "https":
            raise UnsupportedFormatError(
                f"Cannot handle {scheme} (must be https)"
            )

    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            total = response.headers.get("content-length", None)
            try:
                total = int(total) if total else None
            except ValueError:
                total = None
            try:
                with open(dest, "wb") as outfile:
                    for chunk in _progress.data_transfer(
                        total,
                        response.iter_content(chunk_size=16384),
                        enabled=progress,
                        text="Download",
                    ):
                        outfile.write(chunk)
            except OSError as e:
                raise InstallError(
                    f"Failed to write download to {dest}: {e}"
                ) from e
    except requests.RequestException as e:
        raise InstallError(f"Download failed: {e}") from e

    if checkfunc:
        checkfunc(dest)


def _extract_zip(destdir: Path, srcfile: Path, progress: bool = True) -> None:
    try:
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
    except zipfile.BadZipFile as e:
        raise InstallError(f"Invalid or corrupted zip archive: {e}") from e
    except OSError as e:
        raise InstallError(f"Failed to extract zip archive: {e}") from e


def _extract_tgz(destdir: Path, srcfile: Path, progress: bool = True) -> None:
    filter_kwargs = {} if sys.version_info < (3, 12) else {"filter": "tar"}
    try:
        with tarfile.open(srcfile, "r:gz", bufsize=65536) as tf:
            for member in _progress.iterate(
                tf, enabled=progress, text="Extract"
            ):
                tf.extract(member, destdir, **filter_kwargs)
    except tarfile.TarError as e:
        raise InstallError(f"Invalid or corrupted tar archive: {e}") from e
    except OSError as e:
        raise InstallError(f"Failed to extract tar archive: {e}") from e
