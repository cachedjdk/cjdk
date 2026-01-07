<!--
This file is part of cjdk.
Copyright 2022-25 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# JDK vendors

**cjdk** allows you to choose among JDKs and JREs released from different
sources. Names such as `adoptium`, `zulu-jre`, or `graalvm-java17` are used to
select a particular series of JDKs. These names are referred to as "vendors",
even though they do not map 1:1 to companies.

If no vendor is specified, `adoptium` is used unless the environment variable
[`CJDK_VENDOR`](environ-cjdk-vendor) is set to an alternative default.

## About available vendors

The available set of vendors is determined by the [JDK index](./jdk-index.md)
and is not built into **cjdk** itself.

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
available at the time of writing (these each have [versions](./versions.md)
that are numbered independently of the regular JDK version).
