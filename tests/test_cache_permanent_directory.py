# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from cjdk._cache import permanent_directory


def test_permanent_directory_uncached(tmp_path):
    def fetch(path, **kwargs):
        (path / "testfile").touch()
        assert path.samefile(tmp_path / "fetching" / "abc")

    cached = permanent_directory(("abc",), fetch, cache_dir=tmp_path)
    assert cached.is_dir()
    assert cached.samefile(tmp_path / "abc")
    assert (cached / "testfile").is_file()


def test_permanent_directory_cached(tmp_path):
    def fetch(path, **kwargs):
        assert False

    (tmp_path / "abc").mkdir()
    mtime = (tmp_path / "abc").stat().st_mtime
    cached = permanent_directory(("abc",), fetch, cache_dir=tmp_path)
    assert cached.is_dir()
    assert cached.samefile(tmp_path / "abc")
    assert (tmp_path / "abc").stat().st_mtime == mtime


def test_permanent_directory_fetching_elsewhere(tmp_path):
    exec = ThreadPoolExecutor()

    def fetch(path, **kwargs):
        assert False

    def other_fetch():
        def fetch(path, **kwargs):
            time.sleep(0.1)
            (path / "otherfile").touch()

        permanent_directory(("abc",), fetch, cache_dir=tmp_path)

    exec.submit(other_fetch)
    time.sleep(0.05)
    cached = permanent_directory(("abc",), fetch, cache_dir=tmp_path)
    assert cached.is_dir()
    assert (cached / "otherfile").is_file()

    exec.shutdown()


def test_permament_directory_fetching_elsewhere_timeout(tmp_path):
    def fetch(path, **kwargs):
        assert False

    (tmp_path / "fetching" / "abc").mkdir(parents=True)

    with pytest.raises(Exception):
        permanent_directory(
            ("abc",),
            fetch,
            timeout_for_fetch_elsewhere=0.1,
            cache_dir=tmp_path,
        )
