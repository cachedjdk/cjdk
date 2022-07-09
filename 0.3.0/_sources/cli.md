<!--
This file is part of cjdk.
Copyright 2022 Board of Regents of the University of Wisconsin System
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

### `cache-jdk`

```{command-output} cjdk cache-jdk --help
```

```{eval-rst}
.. versionadded:: 0.2.0
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
