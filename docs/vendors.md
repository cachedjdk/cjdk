<!--
This file is part of cjdk.
Copyright 2022-25 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# JDK vendors

**cjdk** allows you to choose among JDKs and JREs released from different
sources. Names such as `adoptium`, `zulu-jre`, or `graalvm-community` are used
to select a particular series of JDKs. These names are referred to as
"vendors", even though they do not map 1:1 to companies.

If no vendor is specified, `adoptium` is used unless the environment variable
[`CJDK_VENDOR`](environ-cjdk-vendor) is set to an alternative default.

## About available vendors

The available set of vendors is determined by the [JDK index](./jdk-index.md)
and is not built into **cjdk** itself.

Common vendor names for full JDKs include `temurin`, `zulu`, `liberica`,
`corretto`, `ibm-semeru`, and `graalvm-community`. Common vendor names for JREs
include `temurin-jre`, `zulu-jre`, and `liberica-jre`.

```{note}
**Eclipse Temurin** was
[previously known](https://blog.adoptium.net/2021/08/adoptium-celebrates-first-release/)
as **AdoptOpenJDK**. To specifically get AdoptOpenJDK releases, use `adopt`; to
specifically get Temurin releases, use `temurin`; `adoptium` will get a Temurin
release if available, falling back to AdoptOpenJDK for older versions. (This
behavior is defined by the index, not **cjdk** itself.)
```

```{note}
For **GraalVM**, the recommended vendor name is `graalvm-community`, which uses
Java-version-aligned numbering (e.g., version `21.0.2` is for Java 21). Legacy
vendors `graalvm` (Java 8), `graalvm-java11`, `graalvm-java17`, etc., are also
available; these use GraalVM release version numbers (e.g., `22.3.3`) which are
independent of the Java version. The `-javaN` suffix indicates the Java
version.
```

```{note}
For **IBM Semeru**, use `ibm-semeru`. The upstream index also has separate
entries for each Java major version (`ibm-semeru-openj9-java11`,
`ibm-semeru-openj9-java17`, etc.), which, as a special case, **cjdk** merges
into a single vendor `ibm-semeru-openj9`; these have more complex version
numbers that include a suffix denoting the OpenJ9 VM version.
```
