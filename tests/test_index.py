# This file is part of cachedjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

from cachedjdk import _index, _cache
from pathlib import Path
import json
import mock_server
import pytest
import urllib


def test_index(tmp_path):
    data = {
        "linux": {
            "amd64": {
                "jdk@adoptium": {"17.0.1": "tgz+https://example.com/a/b/c.tgz"}
            }
        }
    }
    with mock_server.start("/jdk-index.json", data) as server:
        index = _index.index(url=server.endpoint_url(), cachedir=tmp_path)
        assert index == data
        assert server.request_count() == 1
        index = _index.index(url=server.endpoint_url(), cachedir=tmp_path)
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
    jdks = _index.available_jdks(index, os="linux", arch="x86_64")
    assert len(jdks) == 1
    assert jdks[0] == ("adoptium", "17.0.1")


def test_jdk_url(tmp_path):
    index = {
        "linux": {
            "amd64": {
                "jdk@adoptium": {"17.0.1": "tgz+https://example.com/a/b/c.tgz"}
            }
        }
    }
    assert _index.jdk_url(
        index, "adoptium", "17.0.1", os="linux", arch="amd64"
    ) == urllib.parse.urlparse("tgz+https://example.com/a/b/c.tgz")


def test_cached_index(tmp_path):
    with mock_server.start("/index.json", {"hello": "world"}) as server:
        url = server.endpoint_url()
        expected_path = (
            tmp_path
            / _index._INDEX_KEY_PREFIX
            / Path(*_cache.url_to_key(url))
            / _index._INDEX_FILENAME
        )
        path = _index._cached_index(url, 86400, tmp_path)
        assert path.is_file()
        assert path.samefile(expected_path)
        data = _index._read_index(path)
        assert data == {"hello": "world"}
        mtime = path.stat().st_mtime

        # Second time should return same data without fetching.
        assert server.request_count() == 1
        path2 = _index._cached_index(url, 86400, tmp_path)
        assert server.request_count() == 1  # No new request
        assert path2.is_file()
        assert path2.samefile(path)
        data = _index._read_index(path2)
        assert data == {"hello": "world"}
        assert path2.stat().st_mtime == mtime


def test_fetch_index(tmp_path):
    with mock_server.start("/index.json", {"hello": "world"}) as server:
        url = server.endpoint_url()
        path = tmp_path / "test.json"
        _index._fetch_index(url, path, progress=None)
        assert path.is_file()
        data = _index._read_index(path)
        assert "hello" in data
        assert data["hello"] == "world"


def test_read_index(tmp_path):
    data = {
        "a": ["b", "c"],
    }
    path = tmp_path / "test.json"
    with open(path, "w") as outfile:
        json.dump(data, outfile)
    assert _index._read_index(path) == data


def test_normalize_os():
    f = _index._normalize_os
    assert f("Win32") == "windows"
    assert f("macOS") == "darwin"
    assert f("aix100") == "aix"
    assert f("solaris100") == "solaris"


def test_normalize_arch():
    f = _index._normalize_arch
    aliases = {
        "x86": ["386", "i386", "586", "i586", "686", "i686", "X86"],
        "amd64": ["x64", "x86_64", "x86-64", "AMD64"],
        "arm64": ["aarch64", "ARM64"],
    }
    for k, v in aliases.items():
        for a in v:
            assert f(a) == k

    assert f("ia64") == "ia64"  # Not amd64
    assert f("ppc64le") != f("ppc64")
    assert f("ppcle") != f("ppc")
    assert f("s390x") != f("s390")


def test_match_version():
    f = _index._match_version
    assert f("adoptium", ["10", "11.0", "11.1", "1.12.0"], "11") == "11.1"
    assert f("adoptium", ["10", "11.0", "11.1", "1.12.0"], "12") == "1.12.0"
    assert f("graalvm", ["10", "11.0", "11.1", "1.12.0"], "11") == "11.1"
    assert f("graalvm", ["10", "11.0", "11.1", "1.12.0"], "1") == "1.12.0"


def test_normalize_version():
    f = _index._normalize_version
    assert f("1") == (1,)
    assert f("1.0") == (1, 0)
    assert f("1-0") == (1, 0)
    assert f("1", remove_prefix_1=True) == ()
    assert f("1.8", remove_prefix_1=True) == (8,)
    assert f("1.8.0", remove_prefix_1=True) == (8, 0)
    with pytest.raises(ValueError):
        f("1.8u300", remove_prefix_1=True)


def test_is_version_compatible_with_spec():
    f = _index._is_version_compatible_with_spec
    assert f("1", "1")
    assert not f("1", "2")
    assert f("1.0", "1")
    assert not f("1", "1.0")
    assert not f("1.0", "1.1")
    assert not f("1.1", "1.0")
    assert f("11.1.2.3", "11")
    assert f("11.1.2.3", "11.1")
    assert not f("11.1.2.3", "11.1.2.3.0")
