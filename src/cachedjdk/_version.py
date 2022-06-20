# This file is part of cachedjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import importlib.metadata

package_name = "cachedjdk"

try:
    __version__ = importlib.metadata.version(package_name)
except importlib.metadata.PackageNotFoundError:
    __version__ = None
