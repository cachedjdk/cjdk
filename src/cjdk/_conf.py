# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import re
from dataclasses import dataclass
from pathlib import Path

from . import _cache, _index

__all__ = [
    "Configuration",
    "configure",
]


@dataclass
class Configuration:
    vendor: str
    version: str
    cache_dir: Path = _cache.default_cachedir()
    index_url: str = _index.default_index_url()
    os: str = None
    arch: str = None
    progress: bool = True
    _allow_insecure_for_testing = False


def configure(vendor=None, version=None, **kwargs):
    # kwargs must have API-specific items removed before passing here.

    if "jdk" in kwargs:
        if vendor is not None or version is not None:
            raise ValueError(
                "Cannot specify jdk= together with vendor= or version="
            )
        vendor, version = _parse_vendor_version(kwargs.pop("jdk"))

    conf = Configuration(vendor=vendor, version=version)

    cache_dir = kwargs.pop("cache_dir", None)
    if cache_dir:
        conf.cache_dir = Path(cache_dir)

    index_url = kwargs.pop("index_url", None)
    if index_url:
        conf.index_url = index_url

    conf.os = kwargs.pop("os", None)
    conf.arch = kwargs.pop("arch", None)
    conf.progress = kwargs.pop("progress", True)

    conf._allow_insecure_for_testing = kwargs.pop(
        "_allow_insecure_for_testing", False
    )

    if kwargs:
        raise ValueError(f"Unrecognized kwargs: {tuple(kwargs.keys())}")
    return conf


def _parse_vendor_version(spec):
    # Actually we don't fully parse here; we only disambiguate between vendor
    # and version when only one is given.
    if ":" in spec:
        parts = spec.split(":")
        if len(parts) != 2:
            raise ValueError(f"Cannot parse JDK spec '{spec}'")
        return tuple(parts)
    if len(spec) == 0:
        return "", ""
    if re.fullmatch(r"[a-z][a-z0-9-]*", spec):
        return spec, ""
    if re.fullmatch(r"[0-9+.-]*", spec):
        return "", spec
    raise ValueError(f"Cannot parse JDK spec '{spec}'")
