import os
import click

@click.command()
def create():
    project_name = input("Enter the project name: ")
    project_dir = input("Enter the name of the project directory: ")
    # Initailize a new Robyn project

    print(f"Creating a new Robyn project '{project_name}' in '{project_dir}'...")

    # Create a new directory for the project
    project_path = os.path.join(project_dir, project_name)
    os.makedirs(project_path)

    # Create the main application file
    app_file_path = os.path.join(project_path, "app.py")
    with open(app_file_path, "w") as f:
        f.write(
            'from robyn import Robyn\n\napp = Robyn(__file__)\n\nif __name__ == "__main__":\n app.run()'
        )

    print(f"New Robyn project '{project_name}' created in '{project_dir}' ")


if __name__ == "__main__":
    create()
