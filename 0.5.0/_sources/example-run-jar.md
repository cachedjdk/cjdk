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

# Running an application distributed as an all-in-one Jar

This example shows how to use the `cjdk.cache_file()` function to download an
application Jar and run it with the desired JDK.

We will use the [Checkstyle](https://checkstyle.org/) program (a Java linter)
as an example.

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
checkstyle_url = "https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.3.1/checkstyle-10.3.1-all.jar"
```

The following will download the Jar the first time it is run, and place it in
the **cjdk** cache directory.

```{code-cell} ipython3
checkstyle_path = cjdk.cache_file(
    "Checkstyle", checkstyle_url, "checkstyle-all.jar"
)
```

Now we will run Checkstyle, with a JDK that is downloaded if needed.

```{code-cell} ipython3
with cjdk.java_env(vendor="temurin-jre", version="17.0.3"):
    subprocess.run(
        [
            "java",
            "-jar", str(checkstyle_path),
            "-c", "/google_checks.xml",
            "Hello.java",
        ]
    )
```

Checkstyle has pointed out that our example code is missing documentation
comments and does not conform to the indentation rules defined in
`google_checks.xml` (which is included in the Checkstyle Jar).
