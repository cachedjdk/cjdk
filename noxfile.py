# This file is part of cjdk.
# Copyright 2022 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import nox

nox.options.sessions = ["test"]

nox.options.default_venv_backend = "uv|virtualenv"


@nox.session(python=["3.9", "3.10", "3.11", "3.12", "3.13"])
def test(session):
    session.install("-e", ".[testing]")
    session.run("pytest")


@nox.session
def docs(session):
    session.install("-e", ".")
    session.install("-e", "-r", "docs/requirements.txt")
    session.run("jb", "build", "docs/", env={"CJDK_HIDE_PROGRESS_BARS": "1"})
