<!--
This file is part of cjdk.
Copyright 2022-25 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# JDK index

**cjdk** currently depends on the
[JDK index](https://github.com/coursier/jvm-index) assembled (in an automated
fashion) by the [Coursier](https://get-coursier.io/) project.

The index is used to map JDK vendors and versions to download URLs.

You can tell **cjdk** to use an alternative index (which must have the same
JSON format) by setting the environment variable
[`CJDK_INDEX_URL`](environ-cjdk-index-url) or by specifying the API keyword
argument `index_url=` or the command line option `--index-url`.

A local copy of the index is stored in the [cache directory](./cachedir.md),
and a fresh copy is fetched if it is more than a day old. In other words, the
time-to-live of the cached index is 1 day (86400 seconds). The TTL can be
overridden by setting the environment varialbe
[`CJDK_INDEX_TTL`](environ-cjdk-index-ttl) or by specifying the API keyword
argument `index_ttl=` or the command line option `--index-ttl`.

`index_ttl=0` or `--index-ttl=0` will cause the index to be freshly downloaded
unconditionally.
