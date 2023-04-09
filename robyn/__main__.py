import click
import os
from robyn import Robyn


@click.command()
@click.option('--project-name', prompt='Enter project name', default='Sample-project', help='The name of your new Robyn project')
@click.option('--project-dir', prompt='Enter project directory', default=os.getcwd(), help='The directory where your new Robyn project is created')
def create(project_name, project_dir):
    # Initailize a new Robyn project

    click.echo(
        f"Creating a new Robyn project '{project_name}' in '{project_dir}'...")

    # Create a new directory for the project
    project_path = os.path.join(project_dir, project_name)
    os.makedirs(project_path)

    # Create the main application file
    app_file_path = os.path.join(project_path, 'app.py')
    with open(app_file_path, 'w') as f:
        f.write(
            'from robyn import Robyn\n\napp = Robyn()\n\nif __name__ == "__main__":\n app.run()')

    click.echo(
        f"New Robyn project '{project_name}' created in '{project_dir}' ")


if __name__ == '__main__':
    create()
