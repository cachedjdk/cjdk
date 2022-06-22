# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import sys
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from cjdk._cache import atomic_file


def test_atomic_file_uncached(tmp_path):
    def fetch(path, **kwargs):
        path.touch()
        assert path.samefile(tmp_path / "fetching" / "abc" / "testfile")

    cached = atomic_file(("abc",), "testfile", fetch, cache_dir=tmp_path)
    assert cached.is_file()
    assert cached.samefile(tmp_path / "abc" / "testfile")


def test_atomic_file_cached(tmp_path):
    def fetch(path, **kwargs):
        assert False

    (tmp_path / "abc").mkdir()
    (tmp_path / "abc" / "testfile").touch()
    mtime = (tmp_path / "abc" / "testfile").stat().st_mtime
    cached = atomic_file(("abc",), "testfile", fetch, cache_dir=tmp_path)
    assert cached.is_file()
    assert cached.samefile(tmp_path / "abc" / "testfile")
    assert (tmp_path / "abc" / "testfile").stat().st_mtime == mtime


def test_atomic_file_expired(tmp_path):
    new_mtime = 0

    def fetch(path, **kwargs):
        path.touch()
        assert path.samefile(tmp_path / "fetching" / "abc" / "testfile")
        nonlocal new_mtime
        new_mtime = path.stat().st_mtime

    (tmp_path / "abc").mkdir()
    (tmp_path / "abc" / "testfile").touch()
    old_mtime = (tmp_path / "abc" / "testfile").stat().st_mtime
    time.sleep(0.1)
    cached = atomic_file(
        ("abc",), "testfile", fetch, ttl=0.05, cache_dir=tmp_path
    )
    assert new_mtime > old_mtime
    assert cached.is_file()
    assert cached.samefile(tmp_path / "abc" / "testfile")
    assert (tmp_path / "abc" / "testfile").stat().st_mtime == new_mtime


def test_atomic_file_fetching_elsewhere(tmp_path):
    exec = ThreadPoolExecutor()

    def fetch(path, **kwargs):
        assert False

    (tmp_path / "abc").mkdir()
    (tmp_path / "abc" / "testfile").touch()

    def other_fetch():
        def fetch(path, **kwargs):
            time.sleep(0.1)
            with open(path, "w") as f:
                f.write("other")

        atomic_file(("abc",), "testfile", fetch, ttl=0, cache_dir=tmp_path)

    exec.submit(other_fetch)
    time.sleep(0.05)
    cached = atomic_file(
        ("abc",), "testfile", fetch, ttl=0, cache_dir=tmp_path
    )
    assert cached.is_file()
    with open(cached) as f:
        assert f.read() == "other"

    exec.shutdown()


def test_atomic_file_fetching_elsewhere_timeout(tmp_path):
    def fetch(path, **kwargs):
        assert False

    (tmp_path / "fetching" / "abc").mkdir(parents=True)

    with pytest.raises(Exception):
        atomic_file(
            ("abc",),
            "testfile",
            fetch,
            timeout_for_fetch_elsewhere=0.1,
            cache_dir=tmp_path,
        )


def test_atomic_file_open_elsewhere(tmp_path):
    exec = ThreadPoolExecutor()

    def fetch(path, **kwargs):
        with open(path, "w") as f:
            f.write("new")

    (tmp_path / "abc").mkdir()
    (tmp_path / "abc" / "testfile").touch()

    def close_after_delay(f):
        time.sleep(0.1)
        f.close()

    with open(tmp_path / "abc" / "testfile") as fp:
        exec.submit(close_after_delay, fp)
        cached = atomic_file(
            ("abc",), "testfile", fetch, ttl=0, cache_dir=tmp_path
        )
        assert cached.is_file()
        with open(tmp_path / "abc" / "testfile") as fp2:
            assert fp2.read() == "new"

    exec.shutdown()


@pytest.mark.skipif(
    sys.platform != "win32", reason="applicable only to Windows"
)
def test_atomic_file_open_elsewhere_timeout(tmp_path):
    wrote_new = False

    def fetch(path, **kwargs):
        with open(path, "w") as f:
            f.write("new")
            nonlocal wrote_new
            wrote_new = True

    (tmp_path / "abc").mkdir()
    (tmp_path / "abc" / "testfile").touch()

    with open(tmp_path / "abc" / "testfile") as fp:
        with pytest.raises(Exception):
            atomic_file(
                ("abc",),
                "testfile",
                fetch,
                ttl=0,
                timeout_for_read_elsewhere=0.1,
                cache_dir=tmp_path,
            )

        assert wrote_new
