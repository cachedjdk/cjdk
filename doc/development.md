# Development

<!--
This file is part of cjdk.
Copyright 2022, Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

Clone the Git repository and make sure to enable the Git hooks by running
`pre-commit install`. You can install [pre-commit](https://pre-commit.com/)
using `pip`, `brew`, and other means (I recommend the `pip` of a virtual
environment, especially on Windows).

To run the tests using an editable install:

```sh
pip install -e .[testing]
pytest
```

To run the tests as they are run by CI, use Nox:

```sh
pip install nox
nox
```

To build the documentation, use

```sh
nox -s docs
```

## Versioning

**cjdk** uses [SemVer](https://semver.org/), with the API for versioning
purposes comprising the [Python API](./api.md), [command-line
interface](./cli.md), and [environment variables](./environ.md) for
configuration.

As specified by SemVer, anything can change during the 0.x series, although the
plan is to keep disruptive changes to a minimum.
