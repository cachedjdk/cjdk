# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import json
import os
import zipfile
from pathlib import Path

import mock_server
import pytest

from cjdk import _api, _cache, _index


def test_java_home(tmp_path):
    originals = tmp_path / "orig"
    originals.mkdir()
    (originals / "bin").mkdir()
    (originals / "bin" / "java").touch()
    zip = tmp_path / "orig.zip"
    with zipfile.ZipFile(zip, "x") as zf:
        zf.write(originals / "bin" / "java", "bin/java")
    with open(zip, "rb") as f:
        jdk_zip_data = f.read()

    port = mock_server.port()
    with mock_server.start(
        endpoint="/index.json",
        data={
            "linux": {
                "amd64": {
                    "jdk@adoptium": {
                        "17": f"zip+http://127.0.0.1:{port}/jdk.zip"
                    }
                }
            }
        },
        file_endpoint="/jdk.zip",
        file_data=jdk_zip_data,
    ) as server:
        home = _api.java_home(
            vendor="adoptium",
            version="17",
            os="linux",
            arch="amd64",
            cache_dir=tmp_path / "cache",
            index_url=server.url("/index.json"),
            _allow_insecure_for_testing=True,
        )

    assert home.is_dir()
    assert (home / "bin").is_dir()
    assert (home / "bin" / "java").is_file()


def test_java_env(tmp_path):
    # Pretend cache (= tmp_path) is pre-populated
    port = mock_server.port()
    index_dir = (
        tmp_path
        / _index._INDEX_KEY_PREFIX
        / f"127.0.0.1%3A{port}"
        / "index.json"
    )
    index_dir.mkdir(parents=True)
    with open(index_dir / _index._INDEX_FILENAME, "w") as f:
        json.dump(
            {
                "linux": {
                    "amd64": {
                        "jdk@adoptium": {
                            "17": f"zip+http://127.0.0.1:{port}/jdk.zip"
                        }
                    }
                }
            },
            f,
        )
    jdk_dir = tmp_path / "jdks" / f"127.0.0.1%3A{port}" / "jdk.zip"
    (jdk_dir / "bin").mkdir(parents=True)
    (jdk_dir / "bin" / "java").touch()

    with mock_server.start() as server:  # No requests expected
        old_java_home = os.environ.get("JAVA_HOME", None)
        old_path = os.environ.get("PATH", None)
        with _api.java_env(
            vendor="adoptium",
            version="17",
            os="linux",
            arch="amd64",
            cache_dir=tmp_path,
            index_url=f"http://127.0.0.1:{port}/index.json",
        ):
            assert os.environ["JAVA_HOME"] == str(jdk_dir)
            assert os.environ["PATH"].startswith(
                str(jdk_dir / "bin") + os.pathsep
            )
        assert os.environ.get("JAVA_HOME", None) == old_java_home
        assert os.environ.get("PATH", None) == old_path


def test_env_var_set():
    f = _api._env_var_set

    os.environ["CJDK_TEST_ENV_VAR"] = "x"
    with f("CJDK_TEST_ENV_VAR", "testvalue"):
        assert os.environ["CJDK_TEST_ENV_VAR"] == "testvalue"
    assert os.environ["CJDK_TEST_ENV_VAR"] == "x"

    del os.environ["CJDK_TEST_ENV_VAR"]
    with f("CJDK_TEST_ENV_VAR", "testvalue"):
        assert os.environ["CJDK_TEST_ENV_VAR"] == "testvalue"
    assert "CJDK_TEST_ENV_VAR" not in os.environ


def test_check_kwargs():
    f = _api._check_kwargs

    conf = f("temurin", "17")
    assert conf.vendor == "temurin"
    assert conf.version == "17"
    assert conf.cache_dir == _cache.default_cachedir()

    with pytest.raises(ValueError):
        f(vendor="temurin", jdk="temurin:17")
    with pytest.raises(ValueError):
        f(version="17", jdk="temurin:17")

    conf = f(jdk="temurin:17")
    assert conf.vendor == "temurin"
    assert conf.version == "17"

    conf = f(jdk=":")
    assert not conf.vendor
    assert not conf.version

    conf = f(cache_dir="abc")
    assert conf.cache_dir == Path("abc")


def test_read_vendor_version():
    f = _api._parse_vendor_version
    assert f("temurin:17") == ("temurin", "17")
    assert f(":") == ("", "")
    assert f("17") == ("", "17")
    assert f(":17") == ("", "17")
    assert f("17+") == ("", "17+")
    assert f("17.0") == ("", "17.0")
    assert f("17.0+") == ("", "17.0+")
    assert f("17-0") == ("", "17-0")
    assert f("17-0+") == ("", "17-0+")
    assert f("temurin") == ("temurin", "")
    assert f("temurin:") == ("temurin", "")