# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import tarfile
import tempfile
import zipfile
from pathlib import Path

import requests

__all__ = [
    "download_jdk",
]


def download_jdk(
    destdir, url, *, progress=None, _allow_insecure_for_testing=False
):
    """
    Download the JDK at url and extract to destdir.

    Arguments:
    destdir -- a pathlib.Path
    url -- a zip+https or tgz+https URL
    progress -- tqdm or None
    """
    scheme, rest = url.split(":", 1)
    try:
        ext, http = scheme.split("+")
    except ValueError:
        raise NotImplementedError(f"Cannot handle {scheme}")
    if http != "https" and not _allow_insecure_for_testing:
        raise NotImplementedError(f"Cannot handle {scheme} (must be HTTPS)")
    if ext not in ("zip", "tgz"):
        raise NotImplementedError(f"Cannot handle {scheme}")
    url = f"{http}:{rest}"
    with tempfile.TemporaryDirectory(prefix="cjdk-") as tempd:
        file = Path(tempd) / f"archive.{ext}"
        _download_large_file(file, url, progress)
        extract = {"zip": _extract_zip, "tgz": _extract_tgz}[ext]
        extract(destdir, file, progress)


def _download_large_file(destfile, srcurl, progress=None):
    response = requests.get(srcurl, stream=True)
    size = int(response.headers.get("content-length", None))
    if size and progress is not None:
        progress.reset(total=size)
        progress.set_description("Downloading")
    with open(destfile, "wb") as outfile:
        total = 0
        for chunk in response.iter_content(chunk_size=None):
            outfile.write(chunk)
            total += len(chunk)
            if progress is not None:
                progress.update(total)


def _extract_zip(destdir, srcfile, progress=None):
    with zipfile.ZipFile(srcfile) as zf:
        infolist = zf.infolist()
        if progress is not None:
            progress.reset(len(infolist))
            progress.set_description("Extracting")
        for i, member in enumerate(infolist):
            extracted = Path(zf.extract(member, destdir))

            # Recover executable bits; see https://stackoverflow.com/a/46837272
            if member.create_system == 3 and extracted.is_file():
                mode = (member.external_attr >> 16) & 0o111
                extracted.chmod(extracted.stat().st_mode | mode)

            if progress is not None:
                progress.update(i)


def _extract_tgz(destdir, srcfile, progress=None):
    with tarfile.open(srcfile, "r:gz", bufsize=65536) as tf:
        if progress is not None:
            progress.reset()
            progress.set_description("Extracting")
        for i, member in enumerate(tf):
            tf.extract(member, destdir)
            if progress is not None:
                progress.update(i)
