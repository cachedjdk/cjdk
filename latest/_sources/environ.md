<!--
This file is part of cjdk.
Copyright 2022-25 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# Environment variables

The following environment variables modify the default behavior of both the
Python API and the command-line interface. Since they affect any program that
uses **cjdk** as a library, they are intended for setting user preferences or
for testing applications.

Empty environment variables are treated as unset (since version 0.5.0).

## `CJDK_ARCH`

Set to the name of a CPU architecture to override the default (which is the
current CPU architecture as reported by Python's `platform.machine()`).

```{eval-rst}
.. versionadded:: 0.2.0
```

(environ-cjdk-cache-dir)=

## `CJDK_CACHE_DIR`

Set to an absolute path to override the default
[cache directory](./cachedir.md), used when not overridden by a keyword
argument or command-line option.

## `CJDK_HIDE_PROGRESS_BARS`

Set to `1`, `YES`, or `TRUE` (case insensitive) to disable all progress bars.
Note that this only hides progress bars, unlike `--no-progress` or
`progress=False` which hide all progress messages.

This can be used when the output is being captured by tools that do not
correctly emulate a terminal (such as Jupyter Book at the time of writing). You
probably don't need it in Jupyter Lab or regular terminals.

```{eval-rst}
.. versionadded:: 0.3.0
```

(environ-cjdk-index-ttl)=

## `CJDK_INDEX_TTL`

Set to an integer number of seconds to override the default time-to-live for
the cached [JDK index](./jdk-index.md).

```{eval-rst}
.. versionadded:: 0.2.0
```

(environ-cjdk-index-url)=

## `CJDK_INDEX_URL`

Set to a URL to override the default [JDK index](./jdk-index.md).

```{eval-rst}
.. versionadded:: 0.2.0
```

## `CJDK_OS`

Set to the name of an operating system to override the default (which is the
current operating system as reported by Python's `sys.platform`).

```{eval-rst}
.. versionadded:: 0.2.0
```

(environ-cjdk-vendor)=

## `CJDK_VENDOR`

Set to a JDK [vendor](./vendors.md) to override the default (`adoptium`).
