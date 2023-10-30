import os
import webbrowser
from InquirerPy import prompt
from InquirerPy.base.control import Choice
from .argument_parser import Config
from robyn.robyn import get_version
from pathlib import Path
import shutil


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
            ],
            "default": Choice("no-db", name="No DB"),
            "name": "project_type",
        },
    ]
    result = prompt(questions=questions)
    project_dir_path = Path(result["directory"]).resolve()
    docker = result["docker"]
    project_type = result["project_type"]

    final_project_dir_path = (CURRENT_WORKING_DIR / project_dir_path).resolve()

    print(f"Creating a new Robyn project '{final_project_dir_path}'...")

    # Create a new directory for the project
    os.makedirs(final_project_dir_path, exist_ok=True)

    selected_project_template = (SCAFFOLD_DIR / Path(project_type)).resolve()
    shutil.copytree(str(selected_project_template), str(final_project_dir_path), dirs_exist_ok=True)

    # If docker is not needed, delete the docker file
    if docker == "N":
        os.remove(f"{final_project_dir_path}/Dockerfile")

    print(f"New Robyn project created in '{final_project_dir_path}' ")


def docs():
    print("Opening Robyn documentation... | Offline docs coming soon!")
    webbrowser.open("https://robyn.tech")


if __name__ == "__main__":
    config = Config()
    if config.create:
        create_robyn_app()

    if config.version:
        print(get_version())

    if config.docs:
        docs()
