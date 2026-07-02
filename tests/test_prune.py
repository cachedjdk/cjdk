# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

from cjdk._jdk import jdks_to_prune


def test_prune_keeps_newest_per_vendor_major():
    jdks = [
        ("zulu", "25.0.0"),
        ("zulu", "25.0.1"),
        ("corretto", "25.0.2"),
    ]
    # Default: per vendor, per major. Only the older Zulu 25 is obsolete.
    assert jdks_to_prune(jdks) == [("zulu", "25.0.0")]


def test_prune_keeps_each_major():
    jdks = [
        ("zulu", "21.0.8"),
        ("zulu", "21.0.9"),
        ("zulu", "26.0.0"),
        ("zulu", "26.0.1"),
    ]
    # Each major line keeps its own newest.
    assert jdks_to_prune(jdks) == [("zulu", "21.0.8"), ("zulu", "26.0.0")]


def test_prune_across_majors():
    jdks = [
        ("zulu", "21.0.8"),
        ("zulu", "21.0.9"),
        ("zulu", "26.0.0"),
        ("zulu", "26.0.1"),
    ]
    # Collapsing majors keeps only the single newest Zulu.
    assert jdks_to_prune(jdks, per_major=False) == [
        ("zulu", "21.0.8"),
        ("zulu", "21.0.9"),
        ("zulu", "26.0.0"),
    ]


def test_prune_across_vendors():
    jdks = [
        ("zulu", "25.0.0"),
        ("zulu", "25.0.1"),
        ("corretto", "25.0.2"),
    ]
    # Pooling vendors: only the newest version of major 25 survives.
    assert jdks_to_prune(jdks, per_vendor=False) == [
        ("zulu", "25.0.0"),
        ("zulu", "25.0.1"),
    ]


def test_prune_across_vendors_and_majors():
    jdks = [
        ("zulu", "21.0.9"),
        ("zulu", "26.0.0"),
        ("corretto", "26.0.1"),
    ]
    # Everything but the single newest is obsolete.
    assert jdks_to_prune(jdks, per_vendor=False, per_major=False) == [
        ("zulu", "21.0.9"),
        ("zulu", "26.0.0"),
    ]


def test_prune_nothing_when_distinct_majors():
    jdks = [
        ("zulu", "21.0.9"),
        ("adoptium", "17.0.3"),
    ]
    assert jdks_to_prune(jdks) == []


def test_prune_empty():
    assert jdks_to_prune([]) == []


def test_prune_keep_none():
    jdks = [
        ("zulu", "25.0.0"),
        ("zulu", "25.0.1"),
        ("corretto", "25.0.2"),
    ]
    # keep_none prunes everything, ignoring the grouping options.
    assert jdks_to_prune(jdks, keep_none=True) == jdks
    assert (
        jdks_to_prune(jdks, keep_none=True, per_vendor=False, per_major=False)
        == jdks
    )


def test_prune_handles_jdk_1_x_prefix():
    # JDK 1.8 normalizes to major 8; keep the newest 1.8.
    jdks = [
        ("adoptium", "1.8.0-292"),
        ("adoptium", "1.8.0-302"),
    ]
    assert jdks_to_prune(jdks) == [("adoptium", "1.8.0-292")]
