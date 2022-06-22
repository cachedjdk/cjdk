# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import os
from pathlib import Path

import pytest

from cjdk import _conf


def test_configure():
    f = _conf.configure

    conf = f(vendor="temurin", version="17")
    assert conf.vendor == "temurin"
    assert conf.version == "17"
    assert conf.cache_dir == _conf.default_cachedir()

    with pytest.raises(ValueError):
        f(vendor="temurin", jdk="temurin:17")
    with pytest.raises(ValueError):
        f(version="17", jdk="temurin:17")

    conf = f(jdk="temurin:17")
    assert conf.vendor == "temurin"
    assert conf.version == "17"

    conf = f(jdk=":")
    assert conf.vendor == _conf.default_vendor()
    assert not conf.version

    conf = f(cache_dir="abc")
    assert conf.cache_dir == Path("abc")


def test_read_vendor_version():
    f = _conf._parse_vendor_version
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


def test_default_cachedir(monkeypatch):
    f = _conf.default_cachedir
    monkeypatch.setenv("CJDK_CACHE_DIR", "/a/b/c")
    assert f() == Path("/a/b/c")
    monkeypatch.delenv("CJDK_CACHE_DIR")
    assert Path.home() in f().parents
    assert "cache" in str(f().relative_to(Path.home())).lower()


def test__default_cachedir():
    f = _conf._default_cachedir
    assert Path.home() in f().parents
    assert "cache" in str(f().relative_to(Path.home())).lower()


def test_local_app_data(monkeypatch):
    f = _conf._local_app_data
    monkeypatch.setenv("LOCALAPPDATA", "/a/b/c")
    assert f() == Path("/a/b/c")
    monkeypatch.delenv("LOCALAPPDATA")
    assert f() == Path.home() / "AppData" / "Local"


def test_macos_cachedir():
    assert (
        _conf._macos_cachedir() == Path.home() / "Library" / "Caches" / "cjdk"
    )


def test_xdg_cachedir(monkeypatch):
    f = _conf._xdg_cachedir
    monkeypatch.setenv("XDG_CACHE_HOME", "/a/b/c")
    assert f() == Path("/a/b/c/cjdk")
    monkeypatch.delenv("XDG_CACHE_HOME")
    assert f() == Path.home() / ".cache" / "cjdk"


def test_canonicalize_os():
    f = _conf.canonicalize_os
    f(None)  # Current OS
    assert f("Win32") == "windows"
    assert f("macOS") == "darwin"
    assert f("aix100") == "aix"
    assert f("solaris100") == "solaris"


def test_canonicalize_arch():
    f = _conf.canonicalize_arch
    f(None)  # Current architecture
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


def test_default_vendor():
    f = _conf.default_vendor
    os.environ["CJDK_DEFAULT_VENDOR"] = "zulu"
    assert f() == "zulu"
    del os.environ["CJDK_DEFAULT_VENDOR"]
    assert f() == "adoptium"
