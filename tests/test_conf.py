# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import sys
from pathlib import Path

import pytest

from cjdk import _conf
from cjdk._exceptions import ConfigError


def test_configure():
    f = _conf.configure

    conf = f(vendor="temurin", version="17")
    assert conf.vendor == "temurin"
    assert conf.version == "17"
    assert conf.cache_dir == _conf._default_cachedir()

    with pytest.raises(ConfigError):
        f(vendor="temurin", jdk="temurin:17")
    with pytest.raises(ConfigError):
        f(version="17", jdk="temurin:17")

    conf = f(jdk="temurin:17")
    assert conf.vendor == "temurin"
    assert conf.version == "17"

    conf = f(jdk=":")
    assert conf.vendor == _conf._default_vendor()
    assert not conf.version

    conf = f(cache_dir="abc")
    assert conf.cache_dir == Path("abc")

    conf = f(index_ttl=0)
    assert conf.index_ttl == 0
    conf = f(index_ttl=None)
    assert conf.index_ttl == 86400


def test_read_vendor_version():
    f = _conf.parse_vendor_version
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
    f = _conf._default_cachedir
    testdir = "C:\\b\\a" if sys.platform == "win32" else "/a/b/c"
    monkeypatch.setenv("CJDK_CACHE_DIR", testdir)
    assert f() == Path(testdir)
    monkeypatch.delenv("CJDK_CACHE_DIR")
    assert Path.home() in f().parents
    assert "cache" in str(f().relative_to(Path.home())).lower()


def test_local_app_data(monkeypatch):
    f = _conf._local_app_data
    monkeypatch.setenv("LOCALAPPDATA", "/a/b/c")
    assert f(create=False) == Path("/a/b/c")
    monkeypatch.delenv("LOCALAPPDATA")
    assert f(create=False) == Path.home() / "AppData" / "Local"


def test_macos_cachedir():
    f = _conf._macos_cachedir
    assert f(create=False) == Path.home() / "Library" / "Caches" / "cjdk"


def test_xdg_cachedir(monkeypatch):
    f = _conf._xdg_cachedir
    monkeypatch.setenv("XDG_CACHE_HOME", "/a/b/c")
    assert f(create=False) == Path("/a/b/c/cjdk")
    monkeypatch.delenv("XDG_CACHE_HOME")
    assert f(create=False) == Path.home() / ".cache" / "cjdk"


def test_default_index_url(monkeypatch):
    f = _conf._default_index_url
    monkeypatch.setenv("CJDK_INDEX_URL", "https://example.com/index.json")
    assert f() == "https://example.com/index.json"
    monkeypatch.delenv("CJDK_INDEX_URL")
    assert f().startswith("https://raw.githubusercontent.com/")
    assert f().endswith(".json")


def test_default_index_ttl(monkeypatch):
    f = _conf._default_index_ttl
    monkeypatch.setenv("CJDK_INDEX_TTL", "0")
    assert f() == 0
    monkeypatch.delenv("CJDK_INDEX_TTL")
    assert f() == 24 * 3600


def test_canonicalize_os(monkeypatch):
    f = _conf._canonicalize_os
    monkeypatch.setenv("CJDK_OS", "aix10")
    assert f(None) == "aix"
    assert f("linux") == "linux"
    monkeypatch.delenv("CJDK_OS")
    f(None)  # Current OS
    assert f("Win32") == "windows"
    assert f("macOS") == "darwin"
    assert f("aix100") == "aix"
    assert f("solaris100") == "solaris"


def test_canonicalize_arch(monkeypatch):
    f = _conf._canonicalize_arch
    monkeypatch.setenv("CJDK_ARCH", "aarch64")
    assert f(None) == "arm64"
    assert f("x86_64") == "amd64"
    monkeypatch.delenv("CJDK_ARCH")
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


def test_default_vendor(monkeypatch):
    f = _conf._default_vendor
    monkeypatch.setenv("CJDK_VENDOR", "zulu")
    assert f() == "zulu"
    monkeypatch.delenv("CJDK_VENDOR")
    assert f() == "adoptium"
