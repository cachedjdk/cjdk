# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT
from __future__ import annotations

import copy
import json
import re
import warnings
from typing import TYPE_CHECKING, TypeAlias

from . import _install
from ._exceptions import InstallError, JdkNotFoundError

if TYPE_CHECKING:
    from pathlib import Path

    from ._conf import Configuration

__all__ = [
    "jdk_index",
    "available_jdks",
    "resolve_jdk_version",
    "jdk_url",
]


_INDEX_KEY_PREFIX = "index"
_INDEX_FILENAME = "jdk-index.json"


# Type alias declarations.
Versions: TypeAlias = dict[str, str]  # key = version, value = archive URL
Vendors: TypeAlias = dict[str, Versions]  # key = vendor name
Arches: TypeAlias = dict[str, Vendors]  # key = arch name
Index: TypeAlias = dict[str, Arches]  # key = os name


def jdk_index(conf: Configuration) -> Index:
    """
    Get the JDK index, from cache if possible.
    """
    return _read_index(_cached_index_path(conf))


def available_jdks(index: Index, conf: Configuration) -> list[tuple[str, str]]:
    """
    Find in index the available JDK vendor-version combinations.

    A list of tuples (vendor, version) is returned.

    Arguments:
    index -- The JDK index (nested dict)
    """
    try:
        jdks: Vendors = index[conf.os][conf.arch]
    except KeyError:
        return []

    return sorted(
        (vendor.removeprefix("jdk@"), version)
        for vendor, versions in jdks.items()
        for version in versions
    )


def resolve_jdk_version(index: Index, conf: Configuration) -> str:
    """
    Find in index the exact JDK version for the given configuration.

    Arguments:
    index -- The JDK index (nested dict)
    """
    jdks = available_jdks(index, conf)
    versions = _get_versions(jdks, conf)
    if not versions:
        raise JdkNotFoundError(
            f"No {conf.vendor} JDK is available for {conf.os}-{conf.arch}"
        )
    return _match_version(conf.vendor, versions, conf.version)


def jdk_url(
    index: Index, conf: Configuration, exact_version: str | None = None
) -> str:
    """
    Find in index the URL for the JDK binary for the given vendor and version.

    The returned URL usually has a scheme like tgz+https or zip+https.

    Arguments:
    index -- The JDK index (nested dict)
    exact_version (optional) -- The JDK version, or None to resolve it from the configuration
    """
    if exact_version is None:
        exact_version = resolve_jdk_version(index, conf)
    try:
        return index[conf.os][conf.arch][f"jdk@{conf.vendor}"][exact_version]
    except KeyError as e:
        raise JdkNotFoundError(
            f"No URL found for {conf.vendor}:{exact_version} on {conf.os}-{conf.arch}"
        ) from e


def _cached_index_path(conf: Configuration) -> Path:
    def check_index(path: Path) -> None:
        _read_index(path)

    conf_no_progress = copy.deepcopy(conf)
    conf_no_progress.progress = False

    return _install.install_file(
        _INDEX_KEY_PREFIX,
        "index",
        conf.index_url,
        _INDEX_FILENAME,
        conf_no_progress,
        ttl=conf.index_ttl,
        checkfunc=check_index,
    )


def _read_index(path: Path) -> Index:
    try:
        with open(path, encoding="ascii") as infile:
            index = json.load(infile)
    except OSError as e:
        raise InstallError(f"Failed to read index file {path}: {e}") from e
    except json.JSONDecodeError as e:
        raise InstallError(f"Invalid JSON in index file {path}: {e}") from e

    return _postprocess_index(index)


def _postprocess_index(index: Index) -> Index:
    """
    Post-process the index to normalize the data.

    Some "vendors" include the major Java version,
    so let's merge such entries. In particular:

    * ibm-semuru-openj9-java<##>
    * graalvm-java<##>

    However: while the graalvm vendors follow this pattern, the version
    numbers for graalvm are *not* JDK versions, but rather GraalVM versions,
    which merely strongly resemble JDK version strings. For example,
    graalvm-java17 version 22.3.3 bundles OpenJDK 17.0.8, but
    unfortunately there is no way to know this from the index alone.
    """

    pattern = re.compile("^(jdk@ibm-semeru.*)-java\\d+$")
    if not hasattr(index, "items"):
        return index
    for os, arches in index.items():
        if not hasattr(arches, "items"):
            continue
        for arch, vendors in arches.items():
            if not hasattr(vendors, "items"):
                continue
            for vendor, versions in vendors.copy().items():
                if not vendor.startswith("jdk@graalvm") and (
                    m := pattern.match(vendor)
                ):
                    true_vendor = m.group(1)
                    if true_vendor not in index[os][arch]:
                        index[os][arch][true_vendor] = {}
                    index[os][arch][true_vendor].update(versions)

    return index


def _get_versions(
    jdks: list[tuple[str, str]], conf: Configuration
) -> list[str]:
    return [i[1] for i in jdks if i[0] == conf.vendor]


def _match_versions(
    vendor: str, candidates: list[str], requested: str
) -> dict[tuple[int | str, ...], str]:
    # Find all candidates compatible with the request
    is_graal = "graalvm" in vendor.lower()
    normreq = _normalize_version(requested, remove_prefix_1=not is_graal)
    normcands = {}
    for candidate in candidates:
        try:
            normcand = _normalize_version(
                candidate, remove_prefix_1=not is_graal
            )
        except ValueError:
            warnings.warn(
                f"Invalid version '{candidate}' in index; skipped",
                stacklevel=2,
            )
            continue  # Skip any non-numeric versions (not expected)
        normcands[normcand] = candidate

    return {
        k: v
        for k, v in normcands.items()
        if _is_version_compatible_with_spec(k, normreq)
    }


def _match_version(vendor: str, candidates: list[str], requested: str) -> str:
    matched = _match_versions(vendor, candidates, requested)

    if len(matched) == 0:
        raise JdkNotFoundError(
            f"No matching version for '{vendor}:{requested}'"
        )

    return matched[max(matched)]


_VER_SEPS = re.compile(r"[.+_-]")


def _normalize_version(
    ver: str, *, remove_prefix_1: bool = False
) -> tuple[int | str, ...]:
    # Normalize requested version and candidates:
    # - Split at dots and dashes (so we don't distinguish between '.' and '-')
    # - Try to convert elements to integers (so that we can compare elements
    #   numerically where feasible)
    # - If remove_prefix_1 and first element is 1, remove it (so JDK 1.8 == 8)
    # - Return as a tuple (so that we compare element by element)
    # - Trailing zero elements are NOT removed, so, e.g., 11 < 11.0 (for the
    #   most part, the index uses versions with the same number of elements
    #   within a given vendor; versions like "11" are outliers)
    # - If suffixed with "+", append "+" to the returned tuple
    is_plus = ver.endswith("+")
    if is_plus:
        ver = ver[:-1]
    if ver:
        norm = tuple(re.split(_VER_SEPS, ver))
        norm = tuple(_intify(e) for e in norm)
    else:
        norm = ()
    plus = ("+",) if is_plus else ()
    if remove_prefix_1 and len(norm) and norm[0] == 1:
        return norm[1:] + plus
    return norm + plus


def _intify(s: str) -> int | str:
    try:
        return int(s)
    except ValueError:
        return s


def _is_version_compatible_with_spec(
    version: tuple[int | str, ...], spec: tuple[int | str, ...]
) -> bool:
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
