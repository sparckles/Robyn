import os
import webbrowser
from InquirerPy import prompt
from InquirerPy.base.control import Choice
from .argument_parser import Config
from robyn.robyn import get_version
from distutils.dir_util import copy_tree
from pathlib import Path


SCAFFOLD_DIR = Path(__file__).parent / "scaffold"

def create_robyn_app():
    questions = [
        {
            "type": "input",
            "message": "Enter the name of the project directory:",
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
    project_dir = result["directory"]
    docker = result["docker"]
    project_type = result["project_type"]

    print(f"Creating a new Robyn project '{project_dir}'...")

    # Create a new directory for the project
    os.makedirs(project_dir, exist_ok=True)

    selected_project_template = SCAFFOLD_DIR / Path(project_type)
    copy_tree(selected_project_template, project_dir)

    # If docker is not needed, delete the docker file
    if docker == "N":
        os.remove(f"{project_dir}/Dockerfile")

    print(f"New Robyn project created in '{project_dir}' ")


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
