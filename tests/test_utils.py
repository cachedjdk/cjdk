# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import sys
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from cjdk import _utils
from cjdk._exceptions import InstallError


def test_backoff_seconds():
    f = _utils.backoff_seconds
    assert list(f(1, 1, 0)) == [-1]
    assert list(f(1, 1, 1)) == [1, -1]
    assert list(f(1, 1, 0.1)) == [0.1, -1]
    assert list(f(1, 5, 10, factor=2)) == [1, 2, 4, 3, -1]
    assert list(f(1, 2, 10, factor=2)) == [1, 2, 2, 2, 2, 1, -1]


def test_rmtree_tempdir(tmp_path):
    path = tmp_path / "testdir"
    path.mkdir()
    (path / "file").touch()
    _utils.rmtree_tempdir(path)
    assert not path.exists()

    # Non-dir is ignored
    _utils.rmtree_tempdir(tmp_path / "nonexistent")
    (tmp_path / "a_file").touch()
    _utils.rmtree_tempdir(tmp_path / "a_file")
    assert (tmp_path / "a_file").exists()

    # With file inside initially open
    exec = ThreadPoolExecutor()

    def close_after_delay(f):
        time.sleep(0.1)
        f.close()

    path.mkdir()
    file = path / "file"
    file.touch()
    with open(file) as fp:
        exec.submit(close_after_delay, fp)
        _utils.rmtree_tempdir(path, timeout=10)
        assert not path.exists()

    exec.shutdown()

    # With file inside left open
    if sys.platform == "win32":
        path.mkdir()
        file = path / "file"
        file.touch()
        with open(file) as fp, pytest.raises(InstallError):
            _utils.rmtree_tempdir(path, timeout=0.1)


def test_unlink_tempfile(tmp_path):
    file = tmp_path / "test.txt"
    file.touch()
    _utils.unlink_tempfile(file)
    assert not file.exists()

    # Non-existent file is ignored
    _utils.unlink_tempfile(tmp_path / "nonexistent")


def test_swap_in_file(tmp_path):
    dest = tmp_path / "a" / "b" / "target"
    src = tmp_path / "tmpfile"
    src.touch()
    _utils.swap_in_file(dest, src, timeout=0)
    assert dest.is_file()
    assert not src.is_file()

    # With dest existing
    src.touch()
    _utils.swap_in_file(dest, src, timeout=0)
    assert dest.is_file()
    assert not src.is_file()

    # With dest initially open
    exec = ThreadPoolExecutor()

    def close_after_delay(f):
        time.sleep(0.1)
        f.close()

    src.touch()
    with open(dest) as fp:
        exec.submit(close_after_delay, fp)
        _utils.swap_in_file(dest, src, timeout=10)
        assert dest.is_file()
        assert not src.is_file()

    exec.shutdown()

    # With dest left open
    if sys.platform == "win32":
        src.touch()
        with open(dest) as fp, pytest.raises(InstallError):
            _utils.swap_in_file(dest, src, timeout=0.1)
