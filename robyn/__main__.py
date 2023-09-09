import os
import webbrowser
from InquirerPy import prompt
from InquirerPy.base.control import Choice
from .argument_parser import Config


def create_robyn_app():
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
    project_dir = result[0]
    docker = result[1]

    print(f"Creating a new Robyn project '{project_dir}'...")

    # Create a new directory for the project
    os.makedirs(project_dir, exist_ok=True)

    # Create the main application file
    app_file_path = os.path.join(project_dir, "app.py")
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

    # Dockerfile configuration
    if docker == "Y":
        print(f"Generating docker configuration for {project_dir}")
        dockerfile_path = os.path.join(project_dir, "Dockerfile")
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
    elif docker == "N":
        print("Docker not included")
    else:
        print("Unknown Command")

    print(f"New Robyn project created in '{project_dir}' ")


def docs():
    print("Opening Robyn documentation... | Offline docs coming soon!")
    webbrowser.open("https://sparckles.github.io/robyn/#/")



if __name__ == "__main__":
    config = Config()
    if config.create:
        create_robyn_app()

    if config.docs:
        docs()
