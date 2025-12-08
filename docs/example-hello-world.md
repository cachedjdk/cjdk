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

# Running Java "Hello, World" from Python

This example shows how to compile and run Java code.

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

```{code-cell} ipython3
with cjdk.java_env(vendor="temurin-jre", version="17.0.3"):
    subprocess.run(["javac", "Hello.java"], check=True)
    subprocess.run(["java", "Hello"], check=True)
```
