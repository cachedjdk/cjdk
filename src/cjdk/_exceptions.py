# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

__all__ = [
    "CjdkError",
    "ConfigError",
    "DownloadError",
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


class DownloadError(CjdkError, RuntimeError):
    """Download failure, HTTP error, or hash mismatch."""

    exit_code = 4


class InstallError(CjdkError, RuntimeError):
    """Extraction failure, JDK validation error, or cache timeout."""

    exit_code = 5


class UnsupportedFormatError(Exception):
    """Unsupported URL scheme or compression format (internal use)."""

    pass
