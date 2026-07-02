# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

from cjdk import _cache


def test_remove(tmp_path):
    cache_dir = tmp_path / "cache"
    url = "tgz+https://example.com/jdk.tar.gz"
    keydir = cache_dir / "v0" / "jdks" / _cache._key_for_url(url)
    keydir.mkdir(parents=True)
    (keydir / "file.txt").touch()
    url_file = keydir.parent / (keydir.name + ".url")
    url_file.write_text(url)

    assert _cache.is_cached("jdks", url, cache_dir=cache_dir)

    removed = _cache.remove("jdks", url, cache_dir=cache_dir)

    assert removed is True
    assert not keydir.exists()
    assert not url_file.exists()
    assert not _cache.is_cached("jdks", url, cache_dir=cache_dir)


def test_remove_nonexistent(tmp_path):
    cache_dir = tmp_path / "cache"
    url = "tgz+https://example.com/jdk.tar.gz"

    removed = _cache.remove("jdks", url, cache_dir=cache_dir)

    assert removed is False  # Nothing to remove, but no error


def test_remove_without_url_file(tmp_path):
    cache_dir = tmp_path / "cache"
    url = "tgz+https://example.com/jdk.tar.gz"
    keydir = cache_dir / "v0" / "jdks" / _cache._key_for_url(url)
    keydir.mkdir(parents=True)

    removed = _cache.remove("jdks", url, cache_dir=cache_dir)

    assert removed is True
    assert not keydir.exists()
