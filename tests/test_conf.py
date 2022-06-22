# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest

from cjdk import _cache, _conf


def test_check_kwargs():
    f = _conf.check_kwargs

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
