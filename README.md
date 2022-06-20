# cachedjdk

<!--
This file is part of cachedjdk.
Copyright 2022, Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

Cachedjdk is a Python package and command-line tool to download JDK (Java
Development Kit) or JRE (Java Runtime Environment) distributions on the fly.

The required environment (`JAVA_HOME` and `PATH`) can be set up automatically
for the requested JDK, which is downloaded if necessary and stored (by default)
in the user's cache directory.
