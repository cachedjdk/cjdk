import nox

nox.options.sessions = ["test"]


@nox.session(python=["3.8", "3.9", "3.10"])
def test(session):
    session.install(".[testing]")
    session.run("pytest")


@nox.session
def docs(session):
    session.install(".")
    session.install("-r", "docs/requirements.txt")
    session.run("jb", "build", "docs/")
