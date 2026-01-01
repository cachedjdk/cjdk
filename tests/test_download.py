# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import stat
import sys
import tarfile
import zipfile

import mock_server
import pytest

from cjdk import _download


def test_download_and_extract(tmp_path):
    (tmp_path / "origfile").touch()
    zip = tmp_path / "orig.zip"
    with zipfile.ZipFile(zip, "x") as zf:
        zf.write(tmp_path / "origfile", "testfile")
    with open(zip, "rb") as f:
        zipdata = f.read()

    def check(filepath):
        assert filepath.name.endswith(".zip")

    destdir = tmp_path / "destdir"
    destdir.mkdir()
    with mock_server.start(
        file_endpoint="/test.zip", file_data=zipdata
    ) as server:
        _download.download_and_extract(
            destdir,
            "zip+" + server.url("/test.zip"),
            checkfunc=check,
            _allow_insecure_for_testing=True,
        )

    assert (destdir / "testfile").is_file()


def test_download_file(tmp_path):
    size = 100 * 1024 * 1024
    destfile = tmp_path / "testfile"

    def check(filepath):
        assert filepath.stat().st_size == size
        with open(filepath, "rb") as f:
            assert f.read(10) == b"*" * 10

    with mock_server.start(
        download_endpoint="/test.bin", download_size=size
    ) as server:
        _download.download_file(
            destfile,
            server.url("/test.bin"),
            checkfunc=check,
            _allow_insecure_for_testing=True,
        )

    assert destfile.is_file()
    assert destfile.stat().st_size == size
    with open(destfile, "rb") as f:
        assert f.read(10) == b"*" * 10

    def check_not_called(filepath):
        assert False

    with mock_server.start() as server, pytest.raises(Exception):
        _download.download_file(
            destfile,
            server.url("/error"),
            checkfunc=check_not_called,
            _allow_insecure_for_testing=True,
        )


def test_extract_zip(tmp_path):
    originals = tmp_path / "original"
    originals.mkdir()
    (originals / "a").touch()
    (originals / "b").touch()
    (originals / "b").chmod(0o755)
    (originals / "c").mkdir()
    (originals / "c" / "d").touch()

    zip = tmp_path / "test.zip"
    with zipfile.ZipFile(zip, "x") as zf:
        zf.write(originals / "a", "a")
        zf.write(originals / "b", "b")
        zf.write(originals / "c" / "d", "c/d")

    extracted = tmp_path / "extracted"
    extracted.mkdir()
    _download._extract_zip(extracted, zip)
    assert (extracted / "a").is_file()
    assert (extracted / "b").is_file()
    assert (extracted / "c").is_dir()
    assert (extracted / "c" / "d").is_file()
    if sys.platform != "win32":
        assert not (extracted / "a").stat().st_mode & stat.S_IEXEC
        assert (extracted / "b").stat().st_mode & stat.S_IXUSR


def test_extract_tar(tmp_path):
    originals = tmp_path / "original"
    originals.mkdir()
    (originals / "a").touch()
    (originals / "b").touch()
    (originals / "b").chmod(0o755)
    (originals / "c").mkdir()
    (originals / "c" / "d").touch()

    tgz = tmp_path / "test.tar.gz"
    with tarfile.open(tgz, "x:gz") as tf:
        tf.add(originals / "a", "a")
        tf.add(originals / "b", "b")
        tf.add(originals / "c" / "d", "c/d")

    extracted = tmp_path / "extracted"
    extracted.mkdir()
    _download._extract_tgz(extracted, tgz)
    assert (extracted / "a").is_file()
    assert (extracted / "b").is_file()
    assert (extracted / "c").is_dir()
    assert (extracted / "c" / "d").is_file()
    if sys.platform != "win32":
        assert not (extracted / "a").stat().st_mode & stat.S_IEXEC
        assert (extracted / "b").stat().st_mode & stat.S_IXUSR
