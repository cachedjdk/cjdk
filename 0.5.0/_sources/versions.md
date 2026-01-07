<!--
This file is part of cjdk.
Copyright 2022-25 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# JDK versions

JDK versions are selected using version expressions attached to
[vendor](./vendors.md) names: for example, `temurin:17` or
`graalvm-java17:22.1.0`.

The available versions for a given vendor (and OS, architecture) are defined by
the [JDK index](./jdk-index.md). Different vendors use different numbering
schemes.

If you want to reproducibly install an exact JDK build, you should consult the
index and specify an exact version in full.

Otherwise, it is often sufficient to use a single number, such as `17`, to
specify the major version of the JDK. This will match the latest version for
the given vendor that is at least 17 and less than 18. Similarly, `17.0` will
match `17.0.1` but not `17.1.0` or later.

You can also use `17+` to indicate the latest version, but no less than 17. If
no version is given, it is interpreted as `0+`, that is, the latest available
version with no minimum.

For the purpose of comparing and matching versions, any `1.` prefix is ignored,
except in the case where the vendor contains `graalvm`. So `adoptium:1.8` has
the same effect as `adoptium:8`.

Dots (`.`) and dashes (`-`) are considered the same when comparing and matching
versions.
