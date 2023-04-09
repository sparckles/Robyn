import os
from .argument_parser import Config


def create():
    project_dir = input("Enter the name of the project directory: ")
    # Initailize a new Robyn project

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

    print(f"New Robyn project created in '{project_dir}' ")


if __name__ == "__main__":
    config = Config()
    if config.create:
        create()
