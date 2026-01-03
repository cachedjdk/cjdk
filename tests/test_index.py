# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import json

import mock_server
import pytest

from cjdk import _cache, _index
from cjdk._conf import configure
from cjdk._exceptions import JdkNotFoundError


def test_jdk_index(tmp_path):
    data = {
        "linux": {
            "amd64": {
                "jdk@adoptium": {"17.0.1": "tgz+https://example.com/a/b/c.tgz"}
            }
        }
    }
    with mock_server.start(endpoint="/jdk-index.json", data=data) as server:
        index = _index.jdk_index(
            configure(
                index_url=server.url("/jdk-index.json"),
                cache_dir=tmp_path,
                _allow_insecure_for_testing=True,
            )
        )
        assert index == data
        assert server.request_count() == 1
        index = _index.jdk_index(
            configure(
                index_url=server.url("/jdk-index.json"),
                cache_dir=tmp_path,
            )
        )
        assert index == data
        assert server.request_count() == 1  # No new request


def test_available_jdks(tmp_path):
    index = {
        "linux": {
            "amd64": {
                "jdk@adoptium": {"17.0.1": "tgz+https://example.com/a/b/c.tgz"}
            }
        }
    }
    jdks = _index.available_jdks(index, configure(os="linux", arch="amd64"))
    assert len(jdks) == 1
    assert jdks[0] == ("adoptium", "17.0.1")


def test_resolve_jdk_version():
    index = {
        "linux": {
            "amd64": {
                "jdk@adoptium": {"17.0.1": "tgz+https://example.com/a/b/c.tgz"}
            }
        }
    }
    assert (
        _index.resolve_jdk_version(
            index,
            configure(
                os="linux", arch="amd64", vendor="adoptium", version="17+"
            ),
        )
        == "17.0.1"
    )


def test_jdk_url():
    index = {
        "linux": {
            "amd64": {
                "jdk@adoptium": {"17.0.1": "tgz+https://example.com/a/b/c.tgz"}
            }
        }
    }
    assert (
        _index.jdk_url(
            index,
            configure(
                os="linux", arch="amd64", vendor="adoptium", version="17.0.1"
            ),
        )
        == "tgz+https://example.com/a/b/c.tgz"
    )
    assert (
        _index.jdk_url(
            index,
            configure(
                os="linux", arch="amd64", vendor="adoptium", version="17"
            ),
        )
        == "tgz+https://example.com/a/b/c.tgz"
    )
    assert (
        _index.jdk_url(
            index,
            configure(
                os="linux", arch="amd64", vendor="adoptium", version="11"
            ),
            exact_version="17.0.1",
        )
        == "tgz+https://example.com/a/b/c.tgz"
    )


def test_cached_index_path(tmp_path):
    with mock_server.start(
        endpoint="/index.json", data={"hello": "world"}
    ) as server:
        url = server.url("/index.json")
        expected_path = (
            tmp_path
            / "v0"
            / _index._INDEX_KEY_PREFIX
            / _cache._key_for_url(url)
            / _index._INDEX_FILENAME
        )
        path = _index._cached_index_path(
            configure(
                index_url=url,
                cache_dir=tmp_path,
                _allow_insecure_for_testing=True,
            )
        )
        assert path.is_file()
        assert path.samefile(expected_path)
        data = _index._read_index(path)
        assert data == {"hello": "world"}
        mtime = path.stat().st_mtime

        # Second time should return same data without fetching.
        assert server.request_count() == 1
        path2 = _index._cached_index_path(
            configure(
                index_url=url,
                cache_dir=tmp_path,
            )
        )
        assert server.request_count() == 1  # No new request
        assert path2.is_file()
        assert path2.samefile(path)
        assert path2.stat().st_mtime == mtime
        data = _index._read_index(path2)
        assert data == {"hello": "world"}


def test_read_index(tmp_path):
    data = {
        "a": ["b", "c"],
    }
    path = tmp_path / "test.json"
    with open(path, "w") as outfile:
        json.dump(data, outfile)
    assert _index._read_index(path) == data


def test_postprocess_index():
    index = {
        "linux": {
            "amd64": {
                "jdk@ibm-semeru-openj9-java11": {
                    "11.0.21+9_openj9-0.41.0": "a",
                    "11.0.22+7_openj9-0.43.0": "b",
                    "11.0.23+9_openj9-0.44.0": "c",
                },
                "jdk@ibm-semeru-openj9-java17": {
                    "17.0.1+12_openj9-0.29.1": "d",
                    "17.0.2+8_openj9-0.30.0": "e",
                    "17.0.3+7_openj9-0.32.0": "f",
                },
                "jdk@ibm-semeru-openj9-java21": {
                    "21.0.1+12_openj9-0.42.0": "g",
                    "21.0.2+13_openj9-0.43.0": "h",
                },
                "jdk@not-semeru": {"8.0.252": "i"},
            }
        }
    }
    pp_index = _index._postprocess_index(index)
    assert pp_index is index
    assert "jdk@ibm-semeru-openj9" in index["linux"]["amd64"]
    assert len(index["linux"]["amd64"]["jdk@ibm-semeru-openj9"]) == 8


def test_match_versions():
    f = _index._match_versions
    assert f("adoptium", ["10", "11.0", "11.1", "1.12.0"], "11") == {
        (11, 0): "11.0",
        (11, 1): "11.1",
    }
    assert f("adoptium", ["10", "11.0", "11.1", "1.12.0"], "12") == {
        (12, 0): "1.12.0"
    }
    assert f("graalvm", ["10", "11.0", "11.1", "1.12.0"], "11") == {
        (11, 0): "11.0",
        (11, 1): "11.1",
    }
    assert f("graalvm", ["10", "11.0", "11.1", "1.12.0"], "1") == {
        (1, 12, 0): "1.12.0"
    }
    assert f("temurin", ["11.0", "17.0", "18.0"], "") == {
        (11, 0): "11.0",
        (17, 0): "17.0",
        (18, 0): "18.0",
    }
    assert f("temurin", ["11.0", "17.0", "18.0"], "17+") == {
        (17, 0): "17.0",
        (18, 0): "18.0",
    }
    assert f("temurin", ["11.0", "17.0", "18.0"], "19+") == {}


def test_match_version():
    f = _index._match_version
    assert f("adoptium", ["10", "11.0", "11.1", "1.12.0"], "11") == "11.1"
    assert f("adoptium", ["10", "11.0", "11.1", "1.12.0"], "12") == "1.12.0"
    assert f("graalvm", ["10", "11.0", "11.1", "1.12.0"], "11") == "11.1"
    assert f("graalvm", ["10", "11.0", "11.1", "1.12.0"], "1") == "1.12.0"
    assert f("temurin", ["11.0", "17.0", "18.0"], "") == "18.0"
    assert f("temurin", ["11.0", "17.0", "18.0"], "17+") == "18.0"
    with pytest.raises(JdkNotFoundError):
        f("temurin", ["11.0", "17.0", "18.0"], "19+")


def test_normalize_version():
    f = _index._normalize_version
    assert f("1") == (1,)
    assert f("1.0") == (1, 0)
    assert f("1-0") == (1, 0)
    assert f("1", remove_prefix_1=True) == ()
    assert f("1.8", remove_prefix_1=True) == (8,)
    assert f("1.8.0", remove_prefix_1=True) == (8, 0)
    assert f("1.8u300", remove_prefix_1=True) == ("8u300",)
    assert f("21.0.1+12_openj9-0.42.0") == (21, 0, 1, 12, "openj9", 0, 42, 0)


def test_is_version_compatible_with_spec():
    def f(x, y):
        nx = _index._normalize_version(x)
        ny = _index._normalize_version(y)
        return _index._is_version_compatible_with_spec(nx, ny)

    assert f("1", "1")
    assert not f("1", "0")
    assert not f("1", "2")
    assert f("1.0", "1")
    assert not f("1", "1.0")
    assert not f("1.0", "1.1")
    assert not f("1.1", "1.0")
    assert f("11.1.2.3", "11")
    assert f("11.1.2.3", "11.1")
    assert not f("11.1.2.3", "11.1.2.3.0")

    assert f("1", "")
    assert f("1", "+")
    assert f("1", "0+")
    assert f("1.0", "1+")
    assert f("1.0", "1.0+")
    assert f("1.0.5", "1.0+")
    assert not f("1", "1.0+")
    assert f("1.1", "1.0+")
    assert not f("1.0", "1.1+")
    assert f("11.1.2.3", "11+")
    assert f("11.1.2.3", "10+")
    assert f("11.1.2.3", "11.1+")
    assert not f("11.1.2.3", "11.2+")
    assert not f("11.1.2.3", "12+")
