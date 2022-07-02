# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import hashlib
import sys

__all__ = [
    "str_removeprefix",
]


if sys.version_info >= (3, 9):

    def str_removeprefix(s, prefix):
        return s.removeprefix(prefix)

else:

    def str_removeprefix(s, prefix):
        if s.startswith(prefix):
            return s[len(prefix) :]
        return s


if sys.version_info >= (3, 9):

    def sha1_not_for_security(**kwargs):
        return hashlib.sha1(usedforsecurity=False, **kwargs)

else:

    def sha1_not_for_security(**kwargs):
        return hashlib.sha1(**kwargs)
