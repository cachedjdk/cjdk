# Command line interface

<!--
This file is part of cjdk.
Copyright 2022, Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

## Common options

The **cjdk** command-line interface is organized into subcommands. A list of
available subcommands and common options can be displayed using the `--help`
option.

```{command-output} cjdk --help
```

More details about the choices and defaults for [`VENDOR`](./vendors.md),
[`VERSION`](./versions.md), and [`--cache_dir`](./cachedir.md) are available on
separate pages.

## `exec`

```{command-output} cjdk exec --help
```

For example, run the `java` command from the Temurin JRE 17.0.3 with the
`-version` option, installing the JRE if necessary:

```{command-output} cjdk --jdk temurin-jre:17.0.3 exec java -version
```

## `java-home`

```{command-output} cjdk java-home --help
```

For example, to print the Java home directory for the Temurin JRE 17.0.3,
installing it if necessary:

```text
cjdk --jdk temurin-jre:17.0.3 java-home
```

(Output will depend on your operating system and configuration.)
