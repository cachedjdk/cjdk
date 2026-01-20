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
Copyright 2022-25 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# Building and running a GraalVM native image

This example shows how to compile Java source code into a native image
(executable that does not require the JVM) using GraalVM.

Note that some platform-specific prerequisites must be installed for this to
work; see the GraalVM
[documentation](https://www.graalvm.org/22.1/reference-manual/native-image/#prerequisites)
for details.

```{code-cell} ipython3
import cjdk
import subprocess
```

```{code-cell} ipython3
java_source = """
public class Hello {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
"""
```

```{code-cell} ipython3
with open("Hello.java", "w") as fp:
    fp.write(java_source)
```

Now let's compile the source, first with `javac` to byte code, then to a native
image.

```{code-cell} ipython3
with cjdk.java_env(vendor="graalvm-community", version="25.0.1"):
    subprocess.run(["javac", "Hello.java"], check=True)
    subprocess.run(["native-image", "Hello"], check=True)
```

Finally, let's run the native image. Being a native image, it does not need
`java_env()` to run:

```{code-cell} ipython3
r = subprocess.run(["./hello"], check=True)
```

```{code-cell} ipython3
r.returncode
```
