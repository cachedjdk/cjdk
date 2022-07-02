# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import tarfile
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from tqdm.auto import tqdm

from . import _compat

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
    except ValueError:
        raise NotImplementedError(f"Cannot handle {scheme} URL")
    if http != "https" and not _allow_insecure_for_testing:
        raise NotImplementedError(f"Cannot handle {http} (must be https)")
    try:
        extract = {"zip": _extract_zip, "tgz": _extract_tgz}[ext]
    except KeyError:
        raise NotImplementedError(f"Cannot handle compression type {ext}")

    url = http + _compat.str_removeprefix(url, scheme)
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

    response = requests.get(url, stream=True)
    response.raise_for_status()
    size = int(response.headers.get("content-length", None))
    with tqdm(
        desc="Downloading",
        total=size,
        disable=(None if progress else True),
        unit="B",
        unit_scale=True,
    ) as tq:
        with open(dest, "wb") as outfile:
            for chunk in response.iter_content(chunk_size=16384):
                outfile.write(chunk)
                tq.update(len(chunk))

    if checkfunc:
        checkfunc(dest)


def _extract_zip(destdir, srcfile, progress=True):
    with zipfile.ZipFile(srcfile) as zf:
        infolist = zf.infolist()
        for member in tqdm(
            infolist,
            desc="Extracting",
            total=len(infolist),
            disable=(None if progress else True),
            unit="files",
        ):
            extracted = Path(zf.extract(member, destdir))

            # Recover executable bits; see https://stackoverflow.com/a/46837272
            if member.create_system == 3 and extracted.is_file():
                mode = (member.external_attr >> 16) & 0o111
                extracted.chmod(extracted.stat().st_mode | mode)


def _extract_tgz(destdir, srcfile, progress=True):
    with tarfile.open(srcfile, "r:gz", bufsize=65536) as tf:
        for member in tqdm(
            tf,
            desc="Extracting",
            disable=(None if progress else True),
            unit="files",
        ):
            tf.extract(member, destdir)
