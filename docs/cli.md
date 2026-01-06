<!--
This file is part of cjdk.
Copyright 2022-25 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# Command line interface

## Common options

The **cjdk** command-line interface is organized into subcommands. A list of
available subcommands and common options can be displayed using the `--help`
option.

```{command-output} cjdk --help
```

```{eval-rst}
.. versionadded:: 0.2.0
    ``--index-url``, ``--index-ttl``, ``--os``, and ``--arch``
```

More details about the choices and defaults for [`VENDOR`](./vendors.md),
[`VERSION`](./versions.md), and [`--cache_dir`](./cachedir.md) are available on
separate pages.

All subcommands return 0 on success, 1 on general/unknown errors, 2 on
configuration error (e.g., invalid arguments), 3 if a matching JDK is not
available, 4 if download or unpacking fails. However, the `exec` subcommand, if
successful, returns the exit code of the launched program.

```{eval-rst}
.. versionchanged:: 0.5.0
   Specific exit codes were added.
```

## Querying the JDK index

### `ls`

```{command-output} cjdk ls --help
```

```{eval-rst}
.. versionadded:: 0.4.0
```

### `ls-vendors`

```{command-output} cjdk ls-vendors --help
```

```{eval-rst}
.. versionadded:: 0.4.0
```

## Working with cached JDKs

### `exec`

```{command-output} cjdk exec --help
```

For example, run the `java` command from the Temurin JRE 17.0.3 with the
`-version` option, installing the JRE if necessary:

```{command-output} cjdk --jdk temurin-jre:17.0.3 exec -- java -version
```

### `java-home`

```{command-output} cjdk java-home --help
```

For example, to print the Java home directory for the Temurin JRE 17.0.3,
installing it if necessary:

```text
$ cjdk --jdk temurin-jre:17.0.3 java-home
/Users/mark/Library/Caches/cjdk/v0/jdks/0f77e52f812d326e1137d7a22b81d6c328679c68/jdk-17.0.3+7-jre/Contents/Home
```

(The output will depend on your operating system and configuration; the example
shown was on macOS.)

### `cache`

```{command-output} cjdk cache --help
```

```{eval-rst}
.. versionchanged:: 0.4.0
   Renamed from ``cache-jdk``.
```

## Caching arbitrary files and packages

### `cache-file`

```{command-output} cjdk cache-file --help
```

```{eval-rst}
.. versionadded:: 0.2.0
```

### `cache-package`

```{command-output} cjdk cache-package --help
```

```{eval-rst}
.. versionadded:: 0.2.0
```

## Managing the cache

(cli-clear-cache)=

### `clear-cache`

```{command-output} cjdk clear-cache --help
```

```{eval-rst}
.. versionadded:: 0.5.0
```
