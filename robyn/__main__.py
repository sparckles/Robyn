import os
import webbrowser
from InquirerPy import prompt
from InquirerPy.base.control import Choice
from .argument_parser import Config
from robyn.robyn import get_version


def create_robyn_app(project_dir_name: str, is_docker_needed: str) -> None:
    print(f"Creating a new Robyn project '{project_dir_name}'...")
    os.makedirs(project_dir_name, exist_ok=True)
    app_file_path = os.path.join(project_dir_name, "app.py")
    with open(app_file_path, "w") as f:
        f.write(
            """
from robyn import Robyn

app = Robyn(__file__)

@app.get("/")
def index():
    return "Hello World!"


if __name__ == "__main__":
    app.start()

            """
        )
    if is_docker_needed == "Y":
        print(f"Generating docker configuration for {project_dir_name}")
        dockerfile_path = os.path.join(project_dir_name, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write(
                """
FROM ubuntu:22.04

WORKDIR /workspace

RUN apt-get update -y && apt-get install -y python 3.10 python3-pip
RUN pip install --no-cache-dir --upgrade robyn

COPY ./src/workspace/

EXPOSE 8080

CMD ["python3.10", "/workspace/foo/app.py", "--log-level=DEBUG"]
                """
            )
    elif is_docker_needed == "N":
        print("Docker not included")
    else:
        print("Unknown Command")

    print(f"New Robyn project created in '{project_dir_name}' ")


def prompt_create_robyn_app():
    questions = [
        {"type": "input", "message": "Enter the name of the project directory:"},
        {
            "type": "list",
            "message": "Need Docker? (Y/N)",
            "choices": [
                Choice("Y", name="Y"),
                Choice("N", name="N"),
            ],
            "default": None,
        },
    ]
    result = prompt(questions=questions)
    project_dir_name = result[0]
    is_docker_needed = result[1]

    create_robyn_app(project_dir_name=project_dir_name, is_docker_needed=is_docker_needed)


def docs():
    print("Opening Robyn documentation... | Offline docs coming soon!")
    webbrowser.open("https://sparckles.github.io/Robyn/#/")


if __name__ == "__main__":
    config = Config()
    if config.create:
        prompt_create_robyn_app()

    if config.version:
        print(get_version())

    if config.docs:
        docs()
