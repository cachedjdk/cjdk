# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

__all__ = [
    "CjdkError",
    "ConfigError",
    "InstallError",
    "JdkNotFoundError",
    "UnsupportedFormatError",
]


class CjdkError(Exception):
    """Base class for all cjdk exceptions."""

    exit_code = 1


class ConfigError(CjdkError, ValueError):
    """Invalid configuration, conflicting options, or malformed input."""

    exit_code = 2


class JdkNotFoundError(CjdkError, LookupError):
    """Requested JDK not available in the index."""

    exit_code = 3


class InstallError(CjdkError, RuntimeError):
    """Download, extraction, or cache failure."""

    exit_code = 4


class UnsupportedFormatError(Exception):
    """Unsupported URL scheme or compression format (internal use)."""

    pass
