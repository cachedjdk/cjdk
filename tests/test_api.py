# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import json
import os
import zipfile

import mock_server
import pytest

from cjdk import _api, _cache, _index, _jdk


def test_cache_jdk():
    # The code path is a subset of java_home(), so no need for separate test.
    pass


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
    index_url = f"http://127.0.0.1:{port}/index.json"
    index_dir = (
        tmp_path
        / "v0"
        / _index._INDEX_KEY_PREFIX
        / _cache._key_for_url(index_url)
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
    jdk_dir = (
        tmp_path
        / "v0"
        / _jdk._JDK_KEY_PREFIX
        / _cache._key_for_url(f"http://127.0.0.1:{port}/jdk.zip")
    )
    (jdk_dir / "bin").mkdir(parents=True)
    (jdk_dir / "bin" / "java").touch()

    with mock_server.start():  # No requests expected
        old_java_home = os.environ.get("JAVA_HOME", None)
        old_path = os.environ.get("PATH", None)
        with _api.java_env(
            vendor="adoptium",
            version="17",
            os="linux",
            arch="amd64",
            cache_dir=tmp_path,
            index_url=index_url,
        ):
            assert os.environ["JAVA_HOME"] == str(jdk_dir)
            assert os.environ["PATH"].startswith(
                str(jdk_dir / "bin") + os.pathsep
            )
        assert os.environ.get("JAVA_HOME", None) == old_java_home
        assert os.environ.get("PATH", None) == old_path


def test_make_hash_checker(tmp_path):
    sha1_empty_string = "da39a3ee5e6b4b0d3255bfef95601890afd80709"
    sha256_empty_string = (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    sha512_empty_string = "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"

    empty_file = tmp_path / "empty"
    empty_file.touch()

    check = _api._make_hash_checker({})
    check(empty_file)

    check = _api._make_hash_checker(
        dict(
            sha1=sha1_empty_string,
            sha256=sha256_empty_string,
            sha512=sha512_empty_string,
        )
    )
    check(empty_file)

    check = _api._make_hash_checker(dict(sha1=sha1_empty_string))

    not_empty_file = tmp_path / "not_empty"
    with open(not_empty_file, "w") as fp:
        fp.write("hello")
    with pytest.raises(ValueError):
        check(not_empty_file)


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
