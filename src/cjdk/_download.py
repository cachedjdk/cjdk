# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import tarfile
import tempfile
import zipfile
from pathlib import Path

import requests
from tqdm.auto import tqdm

__all__ = [
    "download_jdk",
]


def download_jdk(
    destdir, url, *, progress=True, _allow_insecure_for_testing=False
):
    """
    Download the JDK at url and extract to destdir.

    Arguments:
    destdir -- a pathlib.Path
    url -- a zip+https or tgz+https URL
    progress -- bool
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


def _download_large_file(destfile, srcurl, progress=True):
    response = requests.get(srcurl, stream=True)
    size = int(response.headers.get("content-length", None))
    with tqdm(
        desc="Downloading",
        total=size,
        disable=(None if progress else True),
        unit="B",
        unit_scale=True,
    ) as tq:
        with open(destfile, "wb") as outfile:
            for chunk in response.iter_content(chunk_size=16384):
                outfile.write(chunk)
                tq.update(len(chunk))


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
