---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.13.8
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

<!--
This file is part of cjdk.
Copyright 2022 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# Running Java applications with jgo

This example shows how to run an arbitrary package available from a Maven
repository using [**jgo**](https://github.com/scijava/jgo).

```{code-cell} ipython3
import cjdk
import jgo
import os
from contextlib import contextmanager
```

**jgo** requires Apache Maven, so we'll install that first:

```{code-cell} ipython3
# From https://maven.apache.org/download.html
maven_url = "tgz+https://dlcdn.apache.org/maven/maven-3/3.8.6/binaries/apache-maven-3.8.6-bin.tar.gz"
maven_sha512 = "f790857f3b1f90ae8d16281f902c689e4f136ebe584aba45e4b1fa66c80cba826d3e0e52fdd04ed44b4c66f6d3fe3584a057c26dfcac544a60b301e6d0f91c26"
```

```{code-cell} ipython3
maven_dir = cjdk.cache_package("Maven", maven_url, sha512=maven_sha512)
```

The Maven `.tar.gz` file has been extracted into `maven_dir`; find the `bin`
directory within it:

```{code-cell} ipython3
maven_bin = list(maven_dir.glob("apache-maven-*"))[0] / "bin"
assert (maven_bin / "mvn").is_file()
```

Let's write a context manager that we can use to temporarily put the Maven
`bin` directory on `PATH`.

```{code-cell} ipython3
@contextmanager
def path_prepended(path):
    """
    Context manager to temporarily prepend the given path to PATH.
    """
    save_path = os.environ.get("PATH", "")
    new_path = str(path) + os.pathsep + save_path
    os.environ["PATH"] = new_path
    try:
        yield
    finally:
        os.environ["PATH"] = save_path
```

Now for the magic: run a program by specifying its Maven coordinates.

The JRE and all required Jars are downloaded (and cached) automatically.

```{code-cell} ipython3
with cjdk.java_env(vendor="zulu-jre", version="8"):
    with path_prepended(maven_bin):
        jgo.main_from_endpoint(
            "com.puppycrawl.tools:checkstyle:9.3",
            primary_endpoint_main_class="com.puppycrawl.tools.checkstyle.Main",
            argv=["--version"],
        )
```
