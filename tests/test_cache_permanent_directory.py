# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import time
from concurrent.futures import ThreadPoolExecutor
from queue import SimpleQueue

import pytest

from cjdk import _cache
from cjdk._cache import permanent_directory

_TEST_URL = "http://x.com/y"


def test_permanent_directory_uncached(tmp_path):
    def fetch(path):
        (path / "testfile").touch()
        assert path.samefile(
            tmp_path / "v0" / "fetching" / "p" / _cache._key_for_url(_TEST_URL)
        )

    cached = permanent_directory("p", _TEST_URL, fetch, cache_dir=tmp_path)
    assert cached.is_dir()
    assert cached.samefile(
        tmp_path / "v0" / "p" / _cache._key_for_url(_TEST_URL)
    )
    assert (cached / "testfile").is_file()
    assert (cached.parent / (cached.name + ".url")).is_file()
    with open(cached.parent / (cached.name + ".url")) as f:
        assert f.read() == _TEST_URL


def test_permanent_directory_cached(tmp_path):
    def fetch(path):
        assert False

    target = tmp_path / "v0" / "p" / _cache._key_for_url(_TEST_URL)
    target.mkdir(parents=True)
    mtime = target.stat().st_mtime
    cached = permanent_directory("p", _TEST_URL, fetch, cache_dir=tmp_path)
    assert cached.is_dir()
    assert cached.samefile(target)
    assert target.stat().st_mtime == mtime


def test_permanent_directory_fetching_elsewhere(tmp_path):
    exec = ThreadPoolExecutor()
    q1 = SimpleQueue()
    q2 = SimpleQueue()

    def fetch(path):
        assert False

    def other_fetch():
        def fetch(path):
            q1.put("other fetch started")
            assert q2.get() == "ready to start"
            time.sleep(0.1)
            (path / "otherfile").touch()

        permanent_directory("p", _TEST_URL, fetch, cache_dir=tmp_path)

    exec.submit(other_fetch)
    assert q1.get() == "other fetch started"
    q2.put("ready to start")
    cached = permanent_directory("p", _TEST_URL, fetch, cache_dir=tmp_path)
    assert cached.is_dir()
    assert (cached / "otherfile").is_file()

    exec.shutdown()


def test_permanent_directory_fetching_elsewhere_timeout(tmp_path):
    def fetch(path):
        assert False

    (
        tmp_path / "v0" / "fetching" / "p" / _cache._key_for_url(_TEST_URL)
    ).mkdir(parents=True)

    with pytest.raises(Exception):
        permanent_directory(
            "p",
            _TEST_URL,
            fetch,
            timeout_for_fetch_elsewhere=0.1,
            cache_dir=tmp_path,
        )
