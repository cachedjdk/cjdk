# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import re

import cjdk


def test_version():
    # cchedjdk uses SemVer major.minor.patch[-dev]; the possible '-dev' suffix
    # is translated to '.dev0' for PEP 440 format.

    parts = cjdk.__version__.split(".")
    assert len(parts) >= 3
    if len(parts) > 3:
        assert parts[3].startswith("dev")

    n = r"(([1-9][0-9]*)|0)"
    assert re.fullmatch(n, "0")
    assert re.fullmatch(n, "1")
    assert re.fullmatch(n, "123")
    assert not re.fullmatch(n, "00")
    assert not re.fullmatch(n, "01")

    assert re.fullmatch(n, parts[0])
    assert re.fullmatch(n, parts[1])
    assert re.fullmatch(n, parts[2])
