# cjdk

<!--
This file is part of cjdk.
Copyright 2022, Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

**cjdk** (for "cached JDK") is a Python package and command-line tool to
download and run JDK (Java Development Kit) or JRE (Java Runtime Environment)
distributions.

The required environment (`JAVA_HOME` and `PATH`) can be set up automatically
for the requested JDK, which is downloaded as needed and stored (by default) in
a per-user cache directory.

## What for

- Installing exact JDK versions for reproducible testing
- Working with multiple versions of JDKs
- Deploying tools that require Java

For example, you might want to set `JAVA_HOME` to a JDK 8 installation while
working on a particular project that supports that version, but you might also
want to be able to run tools written in Java, and some of those may require a
newer version of Java (say, 11). Without having to manually set `JAVA_HOME`
every time, you can invoke a tool (say, [CheckStyle](https://checkstyle.org/))
like this:

```sh
cjdk --jdk=11+ exec java -jar checkstyle-10.3-all.jar -c style.xml path/to/file.java
```

(or even leave out the `--jdk=11+` outside of automation).

**cjdk** will automatically install the latest Temurin JDK (see [how to
override](#jdk-vendors)) and invoke its `java` with `JAVA_HOME` set to the
correct directory. The download will only happen when the latest JDK has not
yet been installed by **cjdk**.

The ability to use simple commands to use a particular JDK, whether or not it
is already available on the system, makes it easy to manage and share test
environments and build tooling (such as Git hooks).

## Requirements

No pre-installed JDK or JRE is required. Python 3.9 or later is required.

## Installing

To be written once package is available on PyPI.

## Cache directory

By default, **cjdk** uses the platform-dependent user cache directory to store
downloaded JDKs and other data. The defaults are:

- On Linux, `~/.cache/cjdk`, or, if defined, `$XDG_CACHE_HOME/cjdk`,
- On macOS, `~/Library/Caches/cjdk`, and
- On Windows, `%LOCALAPPDATA%\cjdk\cache`, which is usually
  `%USERPROFILE%\AppData\Local\cjdk\cache`.

You can delete this directory at any time (provided that no program is running
using a JDK installed by cjdk).

You can override the default cache directory by setting the environment
variable `CJDK_CACHE_DIR` to the desired directory.

You can also override the cache directory by specifying the flag
`--cache-dir=DIR` on the command line or giving the `cache_dir=path` keyword
argument to most API functions. This takes precedence over `CJDK_CACHE_DIR` and
is useful for scripts that want to maintain their own set of JDK installations.

## JDK index

**cjdk** currently depends on the [JDK
index](https://github.com/coursier/jvm-index) assembled (in an automated
fashion) by the [Coursier](https://get-coursier.io/) project.

The index is used to map JDK vendors and versions to download URLs.

A local copy of the index is stored in the [cache directory](#cache-directory),
and a fresh copy is fetched if it is more than a day old.

## JDK vendors

**cjdk** allows you to choose among JDKs and JREs released from different
sources. Names such as `adoptium`, `zulu-jre`, or `graalvm-java17` are used to
select a particular series of JDKs. These names are referred to as "vendors",
even though they do not map 1:1 to companies.

If no vendor is specified, `adoptium` is used by default, unless the
environment variable `CJDK_DEFAULT_VENDOR` is defined, in which case its value
is used instead.

### About concrete vendors

The available set of vendors is determined by the [JDK index](#jdk-index), and
is not built into **cjdk** itself.

Common vendors include `adopt`, `adoptium`, `temurin`, `liberica`, `zulu`, and
their JRE counterparts `adopt-jre`, `adoptium-jre`, `temurin-jre`,
`liberica-jre`, `zulu-jre`.

AdoptOpenJDK was
[succeeded](https://blog.adoptium.net/2021/08/adoptium-celebrates-first-release/)
by Eclipse Temurin by Adoptium in 2021. To specifically get AdoptOpenJDK
releases, use `adopt`; to specifically get Temurin releases, use `temurin`;
`adoptium` will get a Temurin release if available, falling back to
AdoptOpenJDK for older versions. (Again, this behavior is defined by the index,
not **cjdk** itself.)

For GraalVM, `graalvm-java11`, `graalvm-java16`, and `graalvm-java17` are
available at the time of writing (these each have [versions](#jdk-versions)
that are numbered independently of the regular JDK version).

## JDK versions

JDK versions are selected using version expressions attached to vendor names:
for example, `temurin:17` or `graalvm-java17:22.1.0`.

Like vendors, the available versions for a given vendor are determined by the
[JDK index](#jdk-index). Different vendors use different numbering schemes.

If you want to reproducibly install an exact JDK build, you should consult the
[index](#jdk-index) and specify an exact version in full.

Otherwise, it is often sufficient to use a single number, such as `17`, to
specify the major version of the JDK. This will match to the latest version for
the given vendor that is at least 17 and less than 18.

You can also use `17+` to indicate the latest version, but no less than 17. If
no version is given, it is interpreted as `0+`, that is, the latest available
version with no minimum.

For the purpose of comparing and matching versions, any `1.` prefix is ignored,
except in the case where the vendor contains `graalvm`. So `adoptium:1.8` has
the same effect as `adoptium:8`.

Dots `.` and dashes `-` are considered the same when comparing and matching
versions.

## Development

Clone the Git repository and make sure to enable the Git hooks by running
`pre-commit install`. You can install [pre-commit](https://pre-commit.com/)
using `pip`, `brew`, and other means.

To run the tests (best done in a virtual environment),

```sh
pip install -e .[testing]
pytest
```
