<!--
This file is part of cjdk.
Copyright 2022-25 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# Overview

**cjdk** (for "cached JDK") is a Python package and command-line tool to
download and run JDK (Java Development Kit) or JRE (Java Runtime Environment)
distributions.

Previously used JDKs are kept in the user's [cache directory](./cachedir.md),
so that future invocations do not require a download.

Possible use cases include:

- Installing exact JDK versions for reproducible testing
- Working with multiple versions of JDKs
- Deploying tools that require Java

Using the command-line interface of **cjdk**, you can run Java programs using a
one-liner, without having to worry about whether the user has installed a new
enough Java runtime and set `JAVA_HOME` and `PATH` to appropriate values.

For example, the following command will run
[Checkstyle](https://checkstyle.org/) using Temurin JRE 17 (which will be
downloaded if this is the first time it is requested):

```sh
cjdk --jdk=temurin-jre:17 exec java -jar checkstyle-10.3-all.jar -c style.xml MyApp.java
```

**cjdk** is distrubuted under the MIT license.

## Acknowledgments

**cjdk** was inspired by [Coursier](https://get-coursier.io/)'s
[`java`](https://get-coursier.io/docs/cli-java) command, and uses Coursier's
[JDK index](https://github.com/coursier/jvm-index).
