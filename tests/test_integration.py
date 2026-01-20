# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

from cjdk import _api


def test_list_vendors():
    vendors = _api.list_vendors(os="linux", arch="amd64")
    assert vendors is not None
    assert "adoptium" in vendors
    assert "corretto" in vendors
    assert "graalvm" in vendors
    assert "ibm-semeru-openj9" in vendors
    assert "java-oracle" in vendors
    assert "liberica" in vendors
    assert "temurin" in vendors
    assert "zulu" in vendors


def test_list_jdks():
    jdks = _api.list_jdks(cached_only=False)
    assert jdks is not None
    assert "adoptium:1.21.0.4" in jdks
    assert "corretto:21.0.4.7.1" in jdks
    assert "graalvm-community:21.0.2" in jdks
    assert "graalvm-java21:21.0.2" in jdks
    assert "liberica:22.0.2" in jdks
    assert "temurin:1.21.0.4" in jdks
    assert "zulu:8.0.362" in jdks

    cached_jdks = _api.list_jdks()
    assert cached_jdks is not None
    assert len(cached_jdks) < len(jdks)

    zulu_jdks = _api.list_jdks(vendor="zulu", cached_only=False)
    assert zulu_jdks is not None
    assert len(set(zulu_jdks))
    assert all(jdk.startswith("zulu:") for jdk in zulu_jdks)
