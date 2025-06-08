import sys

import nox


@nox.session(python=["3.9", "3.10", "3.11", "3.12", "3.13"])
def tests(session):
    session.run("pip", "install", "poetry==1.3.0")
    session.run("pip", "install", "maturin")
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

    args = [
        "maturin",
        "build",
        "-i",
        "python",
        "--out",
        "dist",
    ]

    if sys.platform == "darwin":
        session.run("rustup", "target", "add", "x86_64-apple-darwin")
        session.run("rustup", "target", "add", "aarch64-apple-darwin")
        # args.append("--universal2")

    session.run(*args)
    session.run("pip", "install", "--no-index", "--find-links=dist/", "robyn")
    session.run("pytest")


@nox.session(python=["3.11"])
def lint(session):
    session.run("pip", "install", "black", "ruff")
    session.run("black", "robyn/", "integration_tests/")
