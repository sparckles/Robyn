import sys

import nox


@nox.session(python=["3.10", "3.11", "3.12", "3.13", "3.14"])
def tests(session):
    session.run("pip", "install", "uv")
    session.run("pip", "install", "maturin")
    session.run(
        "uv",
        "export",
        "--frozen",
        "--group",
        "test",
        "--group",
        "dev",
        "--no-hashes",
        "--output-file",
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
        args.append("--target")
        args.append("universal2-apple-darwin")

    session.run(*args)
    session.run("pip", "install", "--no-index", "--find-links=dist/", "robyn")
    session.run("pytest")


@nox.session(python=["3.11"])
def lint(session):
    session.run("pip", "install", "ruff")
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")
