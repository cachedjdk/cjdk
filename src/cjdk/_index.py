# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import json
import platform
import re
import sys
import warnings
from urllib.parse import urlparse

import requests

from . import _cache

__all__ = [
    "default_index_url",
    "jdk_index",
    "available_jdks",
    "jdk_url",
]


def default_index_url():
    # The Coursier JDK index is auto-generated, well curated, and clean.
    return "https://raw.githubusercontent.com/coursier/jvm-index/master/index.json"

    # There is also an older index from the jabba project, but it is manually
    # maintained and would benefit from some data cleaning. Noting down the URL
    # here in case we ever need an alternative. Note that it won't work without
    # some normalization of arch names.
    # "https://raw.githubusercontent.com/shyiko/jabba/master/index.json"


_INDEX_KEY_PREFIX = "jdk-index"
_INDEX_FILENAME = "jdk-index.json"


def jdk_index(
    url=None, ttl=None, cachedir=None, _allow_insecure_for_testing=False
):
    """
    Get the JDK index, from cache if possible.

    Keyword arguments:
    url -- The URL of the index (default: Coursier's JDK index on GitHub)
    ttl -- Time to live for the cached index, in seconds. If the cached index
           is older than the TTL, it will be freshly retrieved (default: one
           day).
    cachedir -- The root cache directory (default: default_cachedir()).
    """
    if not url:
        url = default_index_url()
    if ttl is None:
        ttl = 24 * 3600
    return _read_index(
        _cached_index(
            url,
            ttl,
            cachedir,
            _allow_insecure_for_testing=_allow_insecure_for_testing,
        )
    )


def available_jdks(index, os=None, arch=None):
    """
    Find in index the available JDK vendor-version combinations.

    A list of tuples (vendor, version) is returned.

    Arguments:
    index -- The JDK index (nested dict)

    Keyword arguments:
    os -- Operating system (default: from sys.platform)
    arch -- Architecture (default: from platform.machine, which should reflect
            the operating system architecture regardless of whether the Python
            interpreter is 32-bit or 64-bit)
    """
    os = _normalize_os(os)
    arch = _normalize_arch(arch)
    try:
        # jdks is dict: vendor -> (version -> url)
        jdks = index[os][arch]
    except KeyError:
        return []

    return sorted(
        (vendor.removeprefix("jdk@"), version)
        for vendor, versions in jdks.items()
        for version in versions
    )


def jdk_url(index, vendor, version, *, os=None, arch=None):
    """
    Find in index the URL for the JDK binary for the given vendor and version.

    The returned URL usually has a scheme like tgz+https or zip+https.

    Arguments:
    index -- The JDK index (nested dict)
    vendor -- E.g., "adoptium", "adoptium-jre", "liberica", "liberica-jre",
              "zulu", "zulu-jre", "graalvm-java11", "graalvm-java17" (available
              options depend on index)
    version -- E.g., "8", "11", "17", or vendor-specific, e.g., "1.11.0.15";
               for GraalVM, e.g.,"22.1.0"

    Keyword arguments:
    os -- Operating system (default: from sys.platform)
    arch -- Architecture (default: from platform.machine, which should reflect
            the operating system architecture regardless of whether the Python
            interpreter is 32-bit or 64-bit)
    """
    os = _normalize_os(os)
    arch = _normalize_arch(arch)
    jdks = available_jdks(index, os=os, arch=arch)
    versions = [i[1] for i in jdks if i[0] == vendor]
    if not versions:
        raise KeyError(f"No {vendor} JDK is available for {os}-{arch}")
    matched = _match_version(vendor, versions, version)
    if not matched:
        raise KeyError(
            f"No JDK matching version {version} for {os}-{arch}-{vendor}"
        )
    return index[os][arch][f"jdk@{vendor}"][matched]


def _cached_index(url, ttl, cachedir, _allow_insecure_for_testing=False):
    cache_key = (_INDEX_KEY_PREFIX,) + _cache.url_to_key(url)

    def fetch(dest, **kwargs):
        _fetch_index(
            url, dest, _allow_insecure_for_testing=_allow_insecure_for_testing
        )

    return _cache.atomic_file(
        cache_key, _INDEX_FILENAME, fetch, ttl=ttl, cachedir=cachedir
    )


def _fetch_index(url, dest, _allow_insecure_for_testing=False):
    if not _allow_insecure_for_testing:
        scheme = urlparse(url).scheme
        if scheme != "https":
            raise ValueError("Index URL must be an HTTPS URL")

    response = requests.get(url)
    response.raise_for_status()
    # Something is probably wrong if the index is not 7-bit clean. Also by
    # making this assumption there is less to worry about when interpreting
    # the index (and the URLs in it).
    if not response.text.isascii():
        raise ValueError(
            "Index unexpectedly contains non-ASCII characters ({url})"
        )
    index = response.json()
    with open(dest, "w", encoding="ascii", newline="\n") as outfile:
        json.dump(index, outfile, indent=2, sort_keys=True)


def _read_index(path):
    with open(path, encoding="ascii", newline="\n") as infile:
        return json.load(infile)


def _normalize_os(os):
    if not os:
        os = sys.platform
    os = os.lower()

    if os == "win32":
        os = "windows"
    elif os == "macos":
        os = "darwin"
    elif os.startswith("aix"):
        os = "aix"
    elif os.startswith("solaris"):
        os = "solaris"

    return os


def _normalize_arch(arch):
    if not arch:
        arch = platform.machine()
    arch = arch.lower()

    if arch in ("x86_64", "x86-64", "x64"):
        arch = "amd64"
    elif arch == "aarch64":
        arch = "arm64"
    elif re.fullmatch(r"i?[356]86", arch):
        arch = "x86"

    return arch


def _match_version(vendor, candidates, requested):
    is_graal = "graalvm" in vendor.lower()
    normreq = _normalize_version(requested, remove_prefix_1=not is_graal)
    normcands = {}
    for candidate in candidates:
        try:
            normcand = _normalize_version(
                candidate, remove_prefix_1=not is_graal
            )
        except ValueError:
            warnings.warn(f"Invalid version '{candidate}' in index; skipped")
            continue  # Skip any non-numeric versions (not expected)
        normcands[normcand] = candidate

    # Find the newest candidate compatible with the request
    match_elems = None
    for normcand in sorted(normcands.keys(), reverse=True):
        if _is_version_compatible_with_spec(normcand, normreq):
            return normcands[normcand]
        if normcand > normreq:
            continue
        break
    raise LookupError(f"No matching version for '{vendor}:{requested}'")


_VER_SEPS = re.compile(r"[.-]")


def _normalize_version(ver, *, remove_prefix_1=False):
    # Normalize requested version and candidates:
    # - Split at dots and dashes (so we don't distinguish between '.' and '-')
    # - Convert elements to integers (so that we require numeric elements and
    #   compare them numerically)
    # - If remove_prefix_1 and first element is 1, remove it (so JDK 1.8 == 8)
    # - Return as tuple of ints (so that we compare lexicographically)
    # - Trailing zero elements are NOT removed, so, e.g., 11 < 11.0 (for the
    #   most part, the index uses versions with the same number of elements
    #   within a given vendor; versions like "11" are outliers)
    # - If suffixed with "+", append "+" to the returned tuple
    is_plus = ver.endswith("+")
    if is_plus:
        ver = ver[:-1]
    if ver:
        norm = re.split(_VER_SEPS, ver)
        try:
            norm = tuple(int(e) for e in norm)
        except ValueError:
            raise ValueError(f"Invalid version string: {ver}")
    else:
        norm = ()
    plus = ("+",) if is_plus else ()
    if remove_prefix_1 and len(norm) and norm[0] == 1:
        return norm[1:] + plus
    return norm + plus


def _is_version_compatible_with_spec(version, spec):
    assert "+" not in version
    is_plus = spec and spec[-1] == "+"
    if is_plus:
        spec = spec[:-1]
        if not len(spec):  # spec was just ("+",)
            return True
        return (
            len(version) >= len(spec)
            and version[: len(spec) - 1] == spec[:-1]
            and version[len(spec) - 1] >= spec[-1]
        )
    return len(version) >= len(spec) and version[: len(spec)] == spec
