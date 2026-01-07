<!--
This file is part of cjdk.
Copyright 2022-25 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# Python API

## Querying the JDK index

```{eval-rst}
.. autofunction:: cjdk.list_vendors
.. versionadded:: 0.4.0
```

```{eval-rst}
.. autofunction:: cjdk.list_jdks
.. versionadded:: 0.4.0
```

## Working with cached JDKs

```{eval-rst}
.. autofunction:: cjdk.java_home
```

```{eval-rst}
.. autofunction:: cjdk.java_env
```

```{eval-rst}
.. autofunction:: cjdk.cache_jdk
.. versionadded:: 0.2.0
```

More details about the choices and defaults for [`vendor`](./vendors.md),
[`version`](./versions.md), [`cache_dir`](./cachedir.md),
[`index_url`](./jdk-index.md), and [`index_ttl`](./jdk-index.md) are available
on separate pages.

## Caching arbitrary files and packages

The following functions allow **cjdk**'s file download and extract logic to
cache arbitrary resources from the Internet. They can be used, for example, to
install an application JAR.

```{eval-rst}
.. autofunction:: cjdk.cache_file
.. versionadded:: 0.2.0
```

```{eval-rst}
.. autofunction:: cjdk.cache_package
.. versionadded:: 0.2.0
```

## Managing the cache

```{eval-rst}
.. autofunction:: cjdk.clear_cache
.. versionadded:: 0.5.0
```

## Exceptions

```{eval-rst}
.. autoexception:: cjdk.CjdkError
.. versionadded:: 0.5.0
```

```{eval-rst}
.. autoexception:: cjdk.ConfigError
.. versionadded:: 0.5.0
```

```{eval-rst}
.. autoexception:: cjdk.JdkNotFoundError
.. versionadded:: 0.5.0
```

```{eval-rst}
.. autoexception:: cjdk.InstallError
.. versionadded:: 0.5.0
```
