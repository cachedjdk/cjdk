# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

from cjdk import clear_cache


def test_clear_cache(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "v0" / "test").mkdir(parents=True)
    (cache_dir / "v0" / "test" / "file.txt").touch()

    result = clear_cache(cache_dir=cache_dir)

    assert result == cache_dir
    assert not cache_dir.exists()


def test_clear_cache_nonexistent(tmp_path):
    cache_dir = tmp_path / "nonexistent"

    result = clear_cache(cache_dir=cache_dir)

    assert result == cache_dir
    assert not cache_dir.exists()  # Still doesn't exist, no error
