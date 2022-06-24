# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from cjdk import _cache


def test_key_for_url():
    f = _cache._key_for_url
    key = f("https://x.com/a/b.json")
    assert len(key) == 40
    assert isinstance(key, str)
    assert key == key.lower()
    assert f("https://x.com/a%2Bb/c.json") == f("http://x.com/a+b/c.json")
    assert f("https://x.com/a%2Bb/c.json") == f("https://x.com/a%2bb/c.json")


def test_file_exists_and_is_fresh(tmp_path):
    f = _cache._file_exists_and_is_fresh
    path = tmp_path / "test"
    assert not f(path, ttl=0)
    assert not f(path, ttl=2**63)
    path.touch()
    assert f(path, ttl=2)
    time.sleep(1)
    assert not f(path, ttl=0)
    assert f(path, ttl=3)


def test_key_directory():
    f = _cache._key_directory
    assert f(Path("a"), ("b",)) == Path("a/v0/b")


def test_key_tmpdir():
    f = _cache._key_tmpdir
    assert f(Path("a"), ("b",)) == Path("a/v0/fetching/b")


def test_swap_in_fetched_file(tmp_path):
    dest = tmp_path / "a" / "b" / "target"
    src = tmp_path / "tmpfile"
    src.touch()
    _cache._swap_in_fetched_file(dest, src, timeout=0)
    assert dest.is_file()
    assert not src.is_file()

    # With dest existing
    src.touch()
    _cache._swap_in_fetched_file(dest, src, timeout=0)
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
        _cache._swap_in_fetched_file(dest, src, timeout=10)
        assert dest.is_file()
        assert not src.is_file()

    exec.shutdown()

    # With dest left open
    if sys.platform == "win32":
        src.touch()
        with open(dest) as fp:
            with pytest.raises(OSError):
                _cache._swap_in_fetched_file(dest, src, timeout=0.1)


def test_move_in_fetched_directory(tmp_path):
    dest = tmp_path / "a" / "b" / "target"
    src = tmp_path / "tmpdir"
    src.mkdir()
    _cache._move_in_fetched_directory(dest, src)
    assert dest.is_dir()
    assert not src.is_dir()


def test_wait_for_dir_to_vanish(tmp_path):
    path = tmp_path / "testdir"
    path.mkdir()
    exec = ThreadPoolExecutor()

    def rmdir_after_delay(p):
        time.sleep(0.1)
        p.rmdir()

    exec.submit(rmdir_after_delay, path)
    _cache._wait_for_dir_to_vanish(path, 10)
    exec.shutdown()

    path.mkdir()
    with pytest.raises(Exception):
        _cache._wait_for_dir_to_vanish(path, 0.1)


def test_backoff_seconds():
    f = _cache._backoff_seconds
    assert list(f(1, 1, 0)) == [-1]
    assert list(f(1, 1, 1)) == [1, -1]
    assert list(f(1, 1, 0.1)) == [0.1, -1]
    assert list(f(1, 5, 10, factor=2)) == [1, 2, 4, 3, -1]
    assert list(f(1, 2, 10, factor=2)) == [1, 2, 2, 2, 2, 1, -1]
