# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import pytest

from cjdk import _jdk


def test_find_home(tmp_path):
    f = _jdk.find_home
    p = tmp_path
    with pytest.raises(Exception):
        f(p)
    (p / "bin").mkdir()
    with pytest.raises(Exception):
        f(p)
    (p / "bin" / "java").touch()
    assert f(p) == p
    (p / "jdk").mkdir()
    (p / "bin").rename(p / "jdk" / "bin")
    assert f(p) == p / "jdk"

    p = tmp_path / "macjdk"
    (p / "Contents" / "Home").mkdir(parents=True)
    with pytest.raises(Exception):
        f(p)
    (p / "Contents" / "Home" / "bin").mkdir()
    with pytest.raises(Exception):
        f(p)
    (p / "Contents" / "Home" / "bin" / "java").touch()
    assert f(p) == p / "Contents" / "Home"


def test_looks_like_java_home(tmp_path):
    f = _jdk._looks_like_java_home
    assert not f(tmp_path)
    (tmp_path / "bin").mkdir()
    assert not f(tmp_path)
    (tmp_path / "bin" / "java").touch()
    assert f(tmp_path)
    (tmp_path / "bin" / "java").unlink()
    (tmp_path / "bin" / "java.exe").touch()
    assert f(tmp_path)


def test_contains_single_subdir(tmp_path):
    f = _jdk._contains_single_subdir
    assert not f(tmp_path)
    (tmp_path / "testfile").touch()
    assert not f(tmp_path)
    (tmp_path / "testdir").mkdir()
    assert f(tmp_path)
    (tmp_path / "testdir2").mkdir()
    assert not f(tmp_path)
