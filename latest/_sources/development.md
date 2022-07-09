<!--
This file is part of cjdk.
Copyright 2022 Board of Regents of the University of Wisconsin System
SPDX-License-Identifier: MIT
--->

# Development

Clone the Git repository:

```sh
git clone https://github.com/cachedjdk/cjdk.git
cd cjdk
```

As usual, it is best to do all development in a virtual environment:

```sh
python -m venv venv
echo '*' >venv/.gitignore  # Make Git ignore your venv directory
source venv/bin/activate   # Use venv/Scripts/activate on Windows
python -m pip install --upgrade pip setuptools
```

Make sure to enable the [pre-commit](https://pre-commit.com/) Git hooks:

```sh
pip install pre-commit
pre-commit install
```

To run the tests using an editable install:

```sh
pip install -e .[testing]
pytest
```

To run the tests as they are run by CI, use [Nox](https://nox.thea.codes/):

```sh
pip install nox
nox
```

To build the documentation with [Jupyter Book](https://jupyterbook.org/):

```sh
pip install -r docs/requirements.txt
CJDK_HIDE_PROGRESS_BARS=1 jb build docs
# Now view docs/_build/html/index.html
```

Some of the documentation pages are Jupyter notebooks
[stored](https://jupyterbook.org/en/stable/file-types/myst-notebooks.html) in
MyST Markdown format using [Jupytext](https://jupytext.readthedocs.io/). To
edit these in Jupyter Lab, right-click the file and select "Open With >
Notebook" (if it asks you to select a kernel, you probably tried to open a
Markdown file that is not a notebook).

New notebook pages can be added by first creating the notebook (`.ipynb`) in
Jupyter Lab, then running `jupytext mypage.ipynb --to myst`. Delete the
`.ipynb` file so that the MyST (`.md`) file is the single source of truth.

To build the documentation as done by CI:

```sh
rm -rf docs/_build
nox -s docs
```

(versioning-scheme)=

## Versioning

**cjdk** uses [SemVer 2](https://semver.org/#semantic-versioning-200), with the
scope of API for versioning purposes comprising the [Python API](./api.md),
[command-line interface](./cli.md), and [environment variables](./environ.md)
for configuration.

As specified by SemVer, anything can change during the 0.x series, although the
plan is to keep disruptive changes to a minimum.

## Making API changes

1. Document in docstring. For Python API, follow our flavor of NumPy style.
1. List in the "unreleased" section of `docs/changelog.md`. Change the planned
   next release version if necessary.
1. Document in Jupyter Book (`docs/`). Add `versionadded`, `versionchanged`, or
   `deprecated` directive.

If changing the next release version, ensure that any existing `versionadded`,
`versionchanged`, or `deprecated` directives are updated.

## Release procedure

1. Ensure `docs/changelog.md` lists all changes since the last release, and
   convert the "unreleased" section to the new version.
1. Also ensure that there are no `versionadded`, `versionchanged`, or
   `deprecated` directives with a patch or minor version that is being skipped
   without releasing.
1. Tag the commit to release.

The rest is taken care of automatically.
