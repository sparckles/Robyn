import os
import shutil
import subprocess
import sys
import webbrowser
import argparse
from pathlib import Path
from typing import Optional

from InquirerPy.base.control import Choice
from InquirerPy.resolver import prompt

from robyn.env_populator import load_vars
from robyn.robyn import get_version

from .argument_parser import Config
from .reloader import create_rust_file, setup_reloader

SCAFFOLD_DIR = Path(__file__).parent / "scaffold"
CURRENT_WORKING_DIR = Path.cwd()


def create_robyn_app():
    questions = [
        {
            "type": "input",
            "message": "Directory Path:",
            "name": "directory",
        },
        {
            "type": "list",
            "message": "Need Docker? (Y/N)",
            "choices": [
                Choice("Y", name="Y"),
                Choice("N", name="N"),
            ],
            "default": Choice("N", name="N"),
            "name": "docker",
        },
        {
            "type": "list",
            "message": "Please select project type (Mongo/Postgres/Sqlalchemy/Prisma): ",
            "choices": [
                Choice("no-db", name="No DB"),
                Choice("sqlite", name="Sqlite"),
                Choice("postgres", name="Postgres"),
                Choice("mongo", name="MongoDB"),
                Choice("sqlalchemy", name="SqlAlchemy"),
                Choice("prisma", name="Prisma"),
                Choice("sqlmodel", name="SQLModel"),
            ],
            "default": Choice("no-db", name="No DB"),
            "name": "project_type",
        },
        {
            "type": "list",
            "message": "Need Database Migration? (Y/N)",
            "choices": [
                Choice("Y", name="Y"),
                Choice("N", name="N"),
            ],
            "default": Choice("N", name="N"),
            "name": "db_migration",
        },
    ]
    result = prompt(questions=questions)
    project_dir_path = Path(str(result["directory"])).resolve()
    docker = result["docker"]
    db_migration = result["db_migration"]
    project_type = str(result["project_type"])

    final_project_dir_path = (CURRENT_WORKING_DIR / project_dir_path).resolve()

    print(f"Creating a new Robyn project '{final_project_dir_path}'...")

    # Create a new directory for the project
    os.makedirs(final_project_dir_path, exist_ok=True)

    selected_project_template = (SCAFFOLD_DIR / Path(project_type)).resolve()
    shutil.copytree(str(selected_project_template), str(final_project_dir_path), dirs_exist_ok=True)

    # If docker is not needed, delete the docker file
    if docker == "N":
        os.remove(f"{final_project_dir_path}/Dockerfile")

    # If database migration is needed, install the latest version of alembic
    if db_migration == "Y":
        print("Installing the latest version of alembic...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "alembic", "-q"], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            print("Failed to install alembic. Please install it manually using 'pip install alembic'.")

    print(f"New Robyn project created in '{final_project_dir_path}' ")


def docs():
    print("Opening Robyn documentation... | Offline docs coming soon!")
    webbrowser.open("https://robyn.tech")


def start_dev_server(config: Config, file_path: Optional[str] = None):
    if file_path is None:
        return

    absolute_file_path = (Path.cwd() / file_path).resolve()
    directory_path = absolute_file_path.parent

    if config.dev and not os.environ.get("IS_RELOADER_RUNNING", False):
        setup_reloader(str(directory_path), str(absolute_file_path))
        return


def start_app_normally(config: Config):
    command = [sys.executable]

    for arg in sys.argv[1:]:
        command.append(arg)

    # Run the subprocess
    subprocess.run(command, start_new_session=False)


def handle_db_command():
    """Handle database migration commands."""
    try:
        from robyn.migrate import configure_parser, execute_command
    except ImportError:
        try:
            import importlib.util
            if importlib.util.find_spec("alembic") is None:
                print("ERROR: Alembic has not been installed. Please run 'pip install alembic' to install it.")
                sys.exit(1)
            else:
                print("ERROR: Failed to import migrate module.")
                sys.exit(1)
        except ImportError:
            print("ERROR: Fail to import migrate module.")
            sys.exit(1)
    parser = argparse.ArgumentParser(
        usage=argparse.SUPPRESS,  # omit usage hint
        description='Robyn database migration commands.'
    )
    parser = configure_parser(parser)

    if len(sys.argv) == 2 and sys.argv[1] == 'db':
        parser.print_help()
        sys.exit(1)
    # Remove the first two arguments (robyn and db)
    if len(sys.argv) > 2 and sys.argv[1] == 'db':
        if sys.argv[2] == '--help' or sys.argv[2] == '-h' or sys.argv[2] == '-H':
            parser.print_help()
            sys.exit(1)
        db_args = parser.parse_args(sys.argv[2:])
        execute_command(db_args)
    else:
        print("ERROR: Invalid command. Please run 'robyn db' to see more information.")
        sys.exit(1)


def run():
    config = Config()

    if not config.file_path:
        config.file_path = f"{os.getcwd()}/{__name__}"

    load_vars(project_root=os.path.dirname(os.path.abspath(config.file_path)))
    os.environ["ROBYN_CLI"] = "True"

    if config.dev is None:
        config.dev = os.getenv("ROBYN_DEV_MODE", False) == "True"

    # Handle db command
    if config.db == 'db' and len(sys.argv) > 1 and sys.argv[1] == 'db':
        handle_db_command()
        return

    if config.create:
        create_robyn_app()

    elif file_name := config.create_rust_file:
        create_rust_file(file_name)

    elif config.version:
        print(get_version())

    elif config.docs:
        docs()

    elif config.dev:
        print("Starting dev server...")
        start_dev_server(config, config.file_path)
    else:
        try:
            start_app_normally(config)
        except KeyboardInterrupt:
            # for the crash happening upon pressing Ctrl + C
            pass
