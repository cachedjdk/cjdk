# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import mock_server

from cjdk import _api, _cache, _jdk

_INDEX_DATA = {
    "linux": {
        "amd64": {
            "jdk@zulu": {
                "25.0.0": "tgz+http://example.com/zulu-25.0.0.tar.gz",
                "25.0.1": "tgz+http://example.com/zulu-25.0.1.tar.gz",
                "21.0.9": "tgz+http://example.com/zulu-21.0.9.tar.gz",
            },
            "jdk@adoptium": {
                "17.0.3": "tgz+http://example.com/adoptium-17.0.3.tar.gz",
            },
        },
    },
}


def _populate(cache_dir, url):
    keydir = cache_dir / "v0" / _jdk._JDK_KEY_PREFIX / _cache._key_for_url(url)
    keydir.mkdir(parents=True)
    (keydir / "marker").touch()
    (keydir.parent / (keydir.name + ".url")).write_text(url)


def _populate_all(cache_dir):
    for versions in _INDEX_DATA["linux"]["amd64"].values():
        for url in versions.values():
            _populate(cache_dir, url)


def _common(server, cache_dir):
    return dict(
        os="linux",
        arch="amd64",
        cache_dir=cache_dir,
        index_url=server.url("/index.json"),
        _allow_insecure_for_testing=True,
    )


def test_remove_jdks_exact(tmp_path):
    cache_dir = tmp_path / "cache"
    _populate_all(cache_dir)
    with mock_server.start(endpoint="/index.json", data=_INDEX_DATA) as server:
        common = _common(server, cache_dir)

        # Dry run reports but does not remove.
        dry = _api.remove_jdks(jdk="zulu:25.0.0", dry_run=True, **common)
        assert dry == ["zulu:25.0.0"]
        assert _api.list_jdks(jdk="zulu", **common) == [
            "zulu:21.0.9",
            "zulu:25.0.0",
            "zulu:25.0.1",
        ]

        removed = _api.remove_jdks(jdk="zulu:25.0.0", **common)
        assert removed == ["zulu:25.0.0"]
        assert _api.list_jdks(jdk="zulu", **common) == [
            "zulu:21.0.9",
            "zulu:25.0.1",
        ]
        # Untouched vendor still present.
        assert _api.list_jdks(jdk="adoptium", **common) == ["adoptium:17.0.3"]


def test_remove_jdks_by_vendor(tmp_path):
    cache_dir = tmp_path / "cache"
    _populate_all(cache_dir)
    with mock_server.start(endpoint="/index.json", data=_INDEX_DATA) as server:
        common = _common(server, cache_dir)

        removed = _api.remove_jdks(jdk="zulu", **common)
        assert removed == ["zulu:21.0.9", "zulu:25.0.0", "zulu:25.0.1"]
        assert _api.list_jdks(jdk="zulu", **common) == []
        assert _api.list_jdks(jdk="adoptium", **common) == ["adoptium:17.0.3"]


def test_prune_jdks_default(tmp_path):
    cache_dir = tmp_path / "cache"
    _populate_all(cache_dir)
    with mock_server.start(endpoint="/index.json", data=_INDEX_DATA) as server:
        common = _common(server, cache_dir)

        dry = _api.prune_jdks(dry_run=True, **common)
        assert dry == ["zulu:25.0.0"]

        removed = _api.prune_jdks(**common)
        assert removed == ["zulu:25.0.0"]
        # 21.0.9 (different major) and 25.0.1 (newest) survive.
        assert _api.list_jdks(jdk="zulu", **common) == [
            "zulu:21.0.9",
            "zulu:25.0.1",
        ]


def test_prune_jdks_across_majors(tmp_path):
    cache_dir = tmp_path / "cache"
    _populate_all(cache_dir)
    with mock_server.start(endpoint="/index.json", data=_INDEX_DATA) as server:
        common = _common(server, cache_dir)

        removed = _api.prune_jdks(per_major=False, **common)
        assert sorted(removed) == ["zulu:21.0.9", "zulu:25.0.0"]
        assert _api.list_jdks(jdk="zulu", **common) == ["zulu:25.0.1"]
