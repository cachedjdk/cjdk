# JDK index

<!--
This file is part of cjdk.
Copyright 2022, Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

**cjdk** currently depends on the [JDK
index](https://github.com/coursier/jvm-index) assembled (in an automated
fashion) by the [Coursier](https://get-coursier.io/) project.

The index is used to map JDK vendors and versions to download URLs.

A local copy of the index is stored in the [cache directory](./cachedir.md),
and a fresh copy is fetched if it is more than a day old.
