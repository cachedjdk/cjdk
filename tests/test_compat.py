# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

from cjdk import _compat


def test_str_removeprefix():
    f = _compat.str_removeprefix
    assert f("", "") == ""
    assert f("", "x") == ""
    assert f("x", "x") == ""
    assert f("xy", "x") == "y"
    assert f("xy", "z") == "xy"


def test_sha1_not_for_security():
    # Just make sure it doesn't raise.
    _compat.sha1_not_for_security()
