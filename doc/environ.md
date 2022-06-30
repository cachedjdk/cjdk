# Environment variables

<!--
This file is part of cjdk.
Copyright 2022, Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

The following environment variables modify the default behavior of both the
Python API and the command-line interface.
They are intended for setting user preferences.

(environ-cjdk-cache-dir)=

## `CJDK_CACHE_DIR`

Set to an absolute path to override the default [cache
directory](./cachedir.md), used when not overridden by a keyword argument or
command-line option.

(environ-cjdk-default-vendor)=

## `CJDK_DEFAULT_VENDOR`

Set to a JDK [vendor](./vendors.md) to override the default (`adoptium`).
