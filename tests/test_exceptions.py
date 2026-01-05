# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

from cjdk._exceptions import (
    CjdkError,
    ConfigError,
    InstallError,
    JdkNotFoundError,
)


def test_exception_hierarchy():
    assert issubclass(CjdkError, Exception)
    assert issubclass(ConfigError, CjdkError)
    assert issubclass(ConfigError, ValueError)
    assert issubclass(JdkNotFoundError, CjdkError)
    assert issubclass(JdkNotFoundError, LookupError)
    assert issubclass(InstallError, CjdkError)
    assert issubclass(InstallError, RuntimeError)


def test_exit_codes():
    assert CjdkError.exit_code == 1
    assert ConfigError.exit_code == 2
    assert JdkNotFoundError.exit_code == 3
    assert InstallError.exit_code == 4


def test_backward_compatibility():
    try:
        raise ConfigError("test")
    except ValueError:
        pass

    try:
        raise JdkNotFoundError("test")
    except LookupError:
        pass

    try:
        raise InstallError("test")
    except RuntimeError:
        pass

    try:
        raise ConfigError("test")
    except CjdkError:
        pass
