import sys
import nox


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12"])
def tests(session):
    session.run("pip", "install", "poetry==1.3.0")
    session.run(
        "poetry",
        "export",
        "--with",
        "test",
        "--with",
        "dev",
        "--without-hashes",
        "--output",
        "requirements.txt",
    )
    session.run("pip", "install", "-r", "requirements.txt")
    session.run("pip", "install", "-e", ".")
    if sys.platform == "darwin":
        session.run("rustup", "target", "add", "x86_64-apple-darwin")
        session.run("rustup", "target", "add", "aarch64-apple-darwin")
    session.run(
        "maturin",
        "build",
        "-i",
        "python",
        "--universal2",
        "--out",
        "dist",
    )
    session.run("pip", "install", "--no-index", "--find-links=dist/", "robyn")
    session.run("pytest")


@nox.session(python=["3.11"])
def lint(session):
    session.run("pip", "install", "black", "ruff")
    session.run("black", "robyn/", "integration_tests/")
