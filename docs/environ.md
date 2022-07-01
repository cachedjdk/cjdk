# Environment variables

<!--
This file is part of cjdk.
Copyright 2022, Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

The following environment variables modify the default behavior of both the
Python API and the command-line interface.
They are intended for setting user preferences.

## `CJDK_ARCH`

Set to the name of a CPU architecture to override the default (which is the
current CPU architecture as reported by Python's `platform.machine()`).

(environ-cjdk-cache-dir)=

## `CJDK_CACHE_DIR`

Set to an absolute path to override the default [cache
directory](./cachedir.md), used when not overridden by a keyword argument or
command-line option.

(environ-cjdk-index-ttl)=

## `CJDK_INDEX_TTL`

Set to an integer number of seconds to override the default time-to-live for
the cached [JDK index](./jdk-index.md).

(environ-cjdk-index-url)=

## `CJDK_INDEX_URL`

Set to a URL to override the default [JDK index](./jdk-index.md).

## `CJDK_OS`

Set to the name of an operating system to override the default (which is the
current operating system as reported by Python's `sys.platform`).

(environ-cjdk-vendor)=

## `CJDK_VENDOR`

Set to a JDK [vendor](./vendors.md) to override the default (`adoptium`).
