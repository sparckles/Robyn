import os
import webbrowser

from .argument_parser import Config


def check(value, input_name):
    while value not in ["Y", "N"]:
        print("Invalid input. Please enter Y or N")
        value = input(f"Need {input_name}? (Y/N) ")
    return value


def create_robyn_app():
    project_dir = input("Enter the name of the project directory: ")
    docker = input("Need Docker? (Y/N) ")

    # Initailize a new Robyn project
    docker = check(docker, "Docker")

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
    app.run()

            """
        )

    # DockerFile configuration
    if docker == "Y":
        print(f"Generating docker configuration for {project_dir}")
        dockerfile_path = os.path.join(project_dir, "DockerFile")
        with open(dockerfile_path, "w") as f:
            f.write(
                """
FROM ubuntu:22.04

WORKDIR /workspace

RUN apt-get update -y && \
    apt-get install -y python 3.10
python3-pip

RUN pip install --no-cache-dir
--upgrade robyn

COPY ./src/workspace/

EXPOSE 8080

CMD ["python3.10", "/workspace/foo/
app.py", "--log-level=DEBUG"]

                """
            )
    elif docker == "N":
        print("Docker not included")
    else:
        print("Unknown Command")

    print(f"New Robyn project created in '{project_dir}' ")


def docs():
    print("Opening Robyn documentation... | Offline docs coming soon!")
    webbrowser.open("https://sansyrox.github.io/robyn/#/")


if __name__ == "__main__":
    config = Config()
    if config.create:
        create_robyn_app()

    if config.docs:
        docs()
