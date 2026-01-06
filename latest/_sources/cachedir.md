<!--
This file is part of cjdk.
Copyright 2022-25 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# Cache directory

By default, **cjdk** uses the platform-dependent user cache directory to store
downloaded JDKs and other data. The defaults are:

- On Windows, `%LOCALAPPDATA%\cjdk\cache`, which is usually
  `%USERPROFILE%\AppData\Local\cjdk\cache`,
- On macOS, `~/Library/Caches/cjdk`, and
- On other platforms, `~/.cache/cjdk` or, if defined, `$XDG_CACHE_HOME/cjdk`.

You can override the default cache directory by setting the environment
variable [`CJDK_CACHE_DIR`](environ-cjdk-cache-dir).

You can safely delete the cache directory at any time, provided that **cjdk**
and the JDKs installed by it are not in use. You can use the
[`cjdk clear-cache`](cli-clear-cache) command or the
[`cjdk.clear_cache()`](cjdk.clear_cache) function to do this.
