<!--
This file is part of cjdk.
Copyright 2022 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# Environment variables

The following environment variables modify the default behavior of both the
Python API and the command-line interface. Since they affect any program that
uses **cjdk** as a library, they are intended for setting user preferences or
for testing applications.

## `CJDK_ARCH`

Set to the name of a CPU architecture to override the default (which is the
current CPU architecture as reported by Python's `platform.machine()`).

(environ-cjdk-cache-dir)=

## `CJDK_CACHE_DIR`

Set to an absolute path to override the default
[cache directory](./cachedir.md), used when not overridden by a keyword
argument or command-line option.

## `CJDK_OVERRIDE_PROGRESS_BARS`

Set to `hide` to never display progress bars. Set to `fake` to only update
progress bars a few times. Note that setting this environment variable to
`hide` only hides progress bars whereas `--no-progress` or `progress=False`
hide all progress messages.

This can be used when the output is being captured by tools that do not
correctly emulate a terminal (such as Jupyter Book at the time of writing). You
probably don't need it in Jupyter Lab or regular terminals.

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
