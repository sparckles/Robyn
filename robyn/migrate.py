import os
import sys
import logging
from functools import wraps
import argparse
import re
from pathlib import Path
from typing import Optional, Dict, Any, Callable, TypeVar, cast

# Ensure alembic is installed
import importlib.util

spec = importlib.util.find_spec("alembic")
if spec is None or spec.loader is None:
    print("Alembic has not been installed. Please run 'pip install alembic' to install it.")
    exit(1)

import alembic
from alembic import command
from alembic.config import Config as AlembicConfig


class Config(AlembicConfig):
    """Configuration for Robyn migrations."""

    def __init__(self, directory: str = "migrations", **kwargs):
        config_path = os.path.join(directory, "alembic.ini") if directory else None
        super().__init__(config_path)
        self.set_main_option("script_location", directory)
        self.directory = directory
        self.kwargs = kwargs

    def _get_template_path(self, template=None):
        """Get the path to the template directory.

        Args:
            template: Template name or path, defaults to None

        Returns:
            str: Path to the template directory
        """
        if template is None:
            return Path(__file__).parent / "templates" / "robyn"
        return Path(template)


# Define specific exception types for migration operations
class MigrationError(Exception):
    """Base exception for migration errors."""

    pass


class ConfigurationError(MigrationError):
    """Exception raised for configuration errors."""

    pass


class DatabaseConnectionError(MigrationError):
    """Exception raised for database connection errors."""

    pass


class RevisionError(MigrationError):
    """Exception raised for revision-related errors."""

    pass


class TemplateError(MigrationError):
    """Exception raised for template-related errors."""

    pass


# Type variable for function return type
T = TypeVar("T")


def handle_migration_errors(f: Callable[..., T]) -> Callable[..., T]:
    """Decorator to catch and handle specific migration errors."""

    @wraps(f)
    def wrapped(*args: Any, **kwargs: Any) -> T:
        try:
            return f(*args, **kwargs)
        except MigrationError as e:
            # Handle our specific migration errors
            print(f"Migration Error: {str(e)}")
            sys.exit(1)
        except ImportError as e:
            # Handle import errors separately
            print(f"Import Error: {str(e)}")
            print("Please ensure all required packages are installed.")
            sys.exit(1)
        except alembic.util.exc.CommandError as e:
            # Handle Alembic command errors
            print(f"Alembic Command Error: {str(e)}")
            sys.exit(1)
        except Exception as e:
            # Fallback for unexpected errors
            print(f"Unexpected Error: {str(e)}")
            print("Please report this issue with the full traceback.")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    return cast(Callable[..., T], wrapped)


def _get_config(directory: str, x_arg: Optional[str] = None, opts: Optional[Dict[str, Any]] = None) -> Config:
    """Get the Alembic configuration.

    Args:
        directory: Directory where migration files are stored
        x_arg: Extra arguments to pass to Alembic
        opts: Additional options to pass to Alembic

    Returns:
        Config: Robyn migration configuration

    Raises:
        ConfigurationError: If the configuration directory doesn't exist or is invalid
    """
    if not os.path.exists(directory):
        raise ConfigurationError(f"Migration directory '{directory}' does not exist. Run 'init' command first.")

    try:
        config = Config(directory)
        if x_arg is not None:
            config.cmd_opts = argparse.Namespace(x=x_arg)
        return config
    except Exception as e:
        raise ConfigurationError(f"Failed to create Alembic configuration: {str(e)}")


@handle_migration_errors
def list_templates() -> None:
    """List available migration templates."""
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    templates = os.listdir(templates_dir)
    for template in templates:
        print(template)


def _auto_configure_migrations(directory: str, db_url: Optional[str] = None, model_path: Optional[str] = None) -> None:
    """Automatically configure alembic.ini and env.py

    Args:
        directory: Directory where migration files are stored
        db_url: Database URL
        model_path: Path to the model file

    Raises:
        ConfigurationError: If configuration files cannot be found or modified
        DatabaseConnectionError: If database URL is invalid
    """
    # Configure alembic.ini
    if db_url:
        alembic_ini_path = os.path.join(directory, "alembic.ini")
        if not os.path.exists(alembic_ini_path):
            raise ConfigurationError(f"alembic.ini not found at {alembic_ini_path}. Initialization may have failed.")

        try:
            with open(alembic_ini_path, "r") as f:
                content = f.read()

            # Replace the database URL using regex pattern for more flexibility
            pattern = r"sqlalchemy\.url\s*=\s*[^\n]+"
            replacement = f"sqlalchemy.url = {db_url}"
            new_content = re.sub(pattern, replacement, content)

            if new_content != content:
                with open(alembic_ini_path, "w") as f:
                    f.write(new_content)
                print(f"Successfully configured the database URL: {db_url}")
            else:
                logging.warning("Could not find database URL configuration in alembic.ini")
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to configure database URL: {str(e)}")

    # Configure env.py
    if model_path:
        env_py_path = os.path.join(directory, "env.py")
        if not os.path.exists(env_py_path):
            raise ConfigurationError(f"env.py not found at {env_py_path}. Initialization may have failed.")

        try:
            with open(env_py_path, "r") as f:
                content = f.read()

            try:
                module_path, class_name = model_path.rsplit(".", 1)
                # Allow importing from the parent directory
                import_statement = f"sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))\nfrom {module_path} import {class_name}\ntarget_metadata = {class_name}.metadata"

                # Replace the import statement using regex for more robustness
                import_pattern = r"# add your model's MetaData object here\s*\n# for 'autogenerate' support\s*\n# from myapp import mymodel\s*\n# target_metadata = mymodel\.Base\.metadata"
                import_replacement = f"# add your model's MetaData object here\n# for 'autogenerate' support\n{import_statement}"

                new_content = re.sub(import_pattern, import_replacement, content)

                # Replace the target_metadata setting
                metadata_pattern = r"target_metadata = config\.attributes\.get\('sqlalchemy\.metadata', None\)"
                metadata_replacement = "# target_metadata = config.attributes.get('sqlalchemy.metadata', None)\n# Already set by the import above"

                new_content = re.sub(metadata_pattern, metadata_replacement, new_content)

                if new_content != content:
                    with open(env_py_path, "w") as f:
                        f.write(new_content)
                    print(f"Successfully configured the model path: {model_path}")
                else:
                    logging.warning("Could not find expected patterns in env.py, please manually configure it")
            except ValueError:
                raise ConfigurationError(f"Could not parse the model path {model_path}. Format should be 'module.Class'")
        except Exception as e:
            if not isinstance(e, MigrationError):
                raise ConfigurationError(f"Failed to configure model path: {str(e)}")
            raise


def _special_configure_for_sqlite(directory: str, model_path: Optional[str] = None) -> None:
    """Configure SQLite-specific settings in env.py.

    Args:
        directory: Directory where migration files are stored
        model_path: Path to the model file

    Raises:
        ConfigurationError: If configuration files cannot be found or modified
    """
    # If the database is SQLite, must add render_as_batch=True in run_migrations_online() to avoid migration errors caused by SQLite's limited support for ALTER TABLE.
    if model_path:
        env_py_path = os.path.join(directory, "env.py")
        if not os.path.exists(env_py_path):
            raise ConfigurationError(f"env.py not found at {env_py_path}. Initialization may have failed.")

        try:
            with open(env_py_path, "r") as f:
                content = f.read()

            # Use regex pattern to match the context.configure block more flexibly
            pattern = r"\s+context\.configure\(\s*\n\s+connection=connection,\s*\n\s+target_metadata=target_metadata,\s*\n\s+process_revision_directives=process_revision_directives,\s*\n\s+\)"
            replacement = '\n        from sqlalchemy.engine import Connection\n        def is_sqlite(conn: Connection) -> bool:\n            return conn.dialect.name == "sqlite"\n        context.configure(\n            connection=connection,\n            target_metadata=target_metadata,\n            process_revision_directives=process_revision_directives,\n            render_as_batch=is_sqlite(connection),\n        )'

            new_content = re.sub(pattern, replacement, content)

            if new_content != content:
                with open(env_py_path, "w") as f:
                    f.write(new_content)
                print("Successfully configured SQLite support with render_as_batch=True")
            else:
                logging.warning("Could not find context.configure block in env.py, please manually add render_as_batch=True for SQLite support")
        except Exception as e:
            logging.warning(
                f"Could not configure SQLite support: {str(e)}. If your database is SQLite, you need to manually add `render_as_batch=True` in run_migrations_online() to avoid migration errors caused by SQLite's limited support for ALTER TABLE."
            )
    else:
        logging.warning(
            "If your database is SQLite, you need to manually add `render_as_batch=True` in run_migrations_online() to avoid migration errors caused by SQLite's limited support for ALTER TABLE."
        )


@handle_migration_errors
def init(
    directory: str = "migrations",
    multidb: bool = False,
    template: Optional[str] = None,
    package: bool = False,
    db_url: Optional[str] = None,
    model_path: Optional[str] = None,
) -> None:
    """Initialize a new migration repository.

    Args:
        directory: Directory where migration files will be stored
        multidb: Whether to use multiple databases
        template: Template to use for migration files
        package: Whether to create a package
        db_url: Database URL to use for migrations
        model_path: Path to the model file containing the Base class

    Raises:
        DatabaseConnectionError: If database URL cannot be determined
        ConfigurationError: If model path cannot be determined or configuration fails
        TemplateError: If the specified template cannot be found
    """
    if not db_url:
        try:
            # Try to import models from current working directory
            sys.path.insert(0, os.getcwd())
            try:
                from models import engine

                db_url = str(engine.url)
            except ImportError:
                # Try to import models module dynamically
                spec = importlib.util.find_spec("models")
                if spec is not None:
                    models_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(models_module)
                    if hasattr(models_module, "engine"):
                        db_url = str(models_module.engine.url)
                    else:
                        raise DatabaseConnectionError("Models module does not have 'engine' attribute.")
                else:
                    raise DatabaseConnectionError('Cannot find models module. Please provide your database URL with "--db-url=<YOUR_DB_URL>".')
        except ImportError as e:
            raise DatabaseConnectionError(f"Import error: {e}. Please fix before proceeding.")

    if not model_path:
        try:
            # Try to import models dynamically from current working directory
            spec = importlib.util.find_spec("models")
            if spec is not None:
                models_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(models_module)
                if hasattr(models_module, "Base"):
                    model_path = "models.Base"
                else:
                    raise ConfigurationError(
                        'Models module does not have Base attribute. Please provide your model path with "--model-path=<YOUR_MODEL_PATH>".'
                    )
            else:
                raise ConfigurationError('Cannot find models module. Please provide your model path with "--model-path=<YOUR_MODEL_PATH>".')
        except ImportError as e:
            raise ConfigurationError(f'Import error: {e}. Cannot find models module. Please provide your model path with "--model-path=<YOUR_MODEL_PATH>".')

    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)

    try:
        config = Config(directory)
        if template is not None:
            template_path = config._get_template_path(template)
            if not os.path.exists(template_path):
                raise TemplateError(f"Template '{template}' not found at path: {template_path}")
        else:
            template_path = config._get_template_path()
            if not os.path.exists(template_path):
                raise TemplateError(f"Default template not found at path: {template_path}")

        print(f"Using template: {template_path}")
        command.init(config, directory, template=template_path, package=package)

        _auto_configure_migrations(directory, db_url, model_path)
        _special_configure_for_sqlite(directory, model_path)
    except Exception as e:
        if not isinstance(e, MigrationError):
            raise ConfigurationError(f"Failed to initialize migration repository: {str(e)}")
        raise


@handle_migration_errors
def revision(
    directory: str = "migrations",
    message: Optional[str] = None,
    autogenerate: bool = False,
    sql: bool = False,
    head: str = "head",
    splice: bool = False,
    branch_label: Optional[str] = None,
    version_path: Optional[str] = None,
    rev_id: Optional[str] = None,
) -> None:
    """Create a new revision file.

    Args:
        directory: Directory where migration files are stored
        message: Message to use for the revision
        autogenerate: Whether to autogenerate the revision
        sql: Whether to generate SQL
        head: Head revision to use
        splice: Whether to splice the revision
        branch_label: Label to apply to the branch
        version_path: Path to the version directory
        rev_id: Revision ID to use

    Raises:
        ConfigurationError: If the migration directory is not properly configured
        RevisionError: If there's an error creating the revision
    """
    if not message and not rev_id:
        raise RevisionError("A revision message (-m) or revision id (--rev-id) is required")

    try:
        config = _get_config(directory)
        command.revision(
            config, message, autogenerate=autogenerate, sql=sql, head=head, splice=splice, branch_label=branch_label, version_path=version_path, rev_id=rev_id
        )
    except alembic.util.exc.CommandError as e:
        raise RevisionError(f"Failed to create revision: {str(e)}")
    except Exception as e:
        if not isinstance(e, MigrationError):
            raise RevisionError(f"Unexpected error creating revision: {str(e)}")
        raise


@handle_migration_errors
def migrate(
    directory: str = "migrations",
    message: Optional[str] = None,
    sql: bool = False,
    head: str = "head",
    splice: bool = False,
    branch_label: Optional[str] = None,
    version_path: Optional[str] = None,
    rev_id: Optional[str] = None,
    x_arg: Optional[str] = None,
) -> None:
    """Alias for 'revision --autogenerate'.

    Args:
        directory: Directory where migration files are stored
        message: Message to use for the revision
        sql: Whether to generate SQL
        head: Head revision to use
        splice: Whether to splice the revision
        branch_label: Label to apply to the branch
        version_path: Path to the version directory
        rev_id: Revision ID to use
        x_arg: Extra arguments to pass to Alembic

    Raises:
        ConfigurationError: If the migration directory is not properly configured
        RevisionError: If there's an error creating the revision
        DatabaseConnectionError: If there's an error connecting to the database
    """
    if not message and not rev_id:
        raise RevisionError("A revision message (-m) or revision id (--rev-id) is required")

    try:
        config = _get_config(directory, x_arg)
        command.revision(
            config, message, autogenerate=True, sql=sql, head=head, splice=splice, branch_label=branch_label, version_path=version_path, rev_id=rev_id
        )
    except alembic.util.exc.CommandError as e:
        if "No connection could be established" in str(e):
            raise DatabaseConnectionError(f"Database connection error: {str(e)}")
        raise RevisionError(f"Failed to create migration: {str(e)}")
    except Exception as e:
        if not isinstance(e, MigrationError):
            raise RevisionError(f"Unexpected error creating migration: {str(e)}")
        raise


@handle_migration_errors
def edit(directory: str = "migrations", revision: str = "current") -> None:
    """Edit the revision file.

    Args:
        directory: Directory where migration files are stored
        revision: Revision to edit
    """
    command.edit(_get_config(directory), revision)


@handle_migration_errors
def merge(
    directory: str = "migrations", revisions: str = "", message: Optional[str] = None, branch_label: Optional[str] = None, rev_id: Optional[str] = None
) -> None:
    """Merge two revisions.

    Args:
        directory: Directory where migration files are stored
        revisions: Revisions to merge
        message: Message to use for the merge
        branch_label: Label to apply to the branch
        rev_id: Revision ID to use
    """
    command.merge(_get_config(directory), revisions.split(","), message=message, branch_label=branch_label, rev_id=rev_id)


@handle_migration_errors
def upgrade(directory: str = "migrations", revision: str = "head", sql: bool = False, tag: Optional[str] = None, x_arg: Optional[str] = None) -> None:
    """Upgrade to a later revision.

    Args:
        directory: Directory where migration files are stored
        revision: Revision to upgrade to
        sql: Whether to generate SQL
        tag: Tag to apply to the revision
        x_arg: Extra arguments to pass to Alembic

    Raises:
        ConfigurationError: If the migration directory is not properly configured
        RevisionError: If there's an error with the revision
        DatabaseConnectionError: If there's an error connecting to the database
    """
    try:
        config = _get_config(directory, x_arg)
        command.upgrade(config, revision, sql=sql, tag=tag)
    except alembic.util.exc.CommandError as e:
        if "No connection could be established" in str(e):
            raise DatabaseConnectionError(f"Database connection error: {str(e)}")
        elif "Can't locate revision" in str(e):
            raise RevisionError(f"Revision error: {str(e)}")
        else:
            raise RevisionError(f"Failed to upgrade: {str(e)}")
    except Exception as e:
        if not isinstance(e, MigrationError):
            raise RevisionError(f"Unexpected error during upgrade: {str(e)}")
        raise


@handle_migration_errors
def downgrade(directory: str = "migrations", revision: str = "-1", sql: bool = False, tag: Optional[str] = None, x_arg: Optional[str] = None) -> None:
    """Revert to a previous revision.

    Args:
        directory: Directory where migration files are stored
        revision: Revision to downgrade to
        sql: Whether to generate SQL
        tag: Tag to apply to the revision
        x_arg: Extra arguments to pass to Alembic

    Raises:
        ConfigurationError: If the migration directory is not properly configured
        RevisionError: If there's an error with the revision
        DatabaseConnectionError: If there's an error connecting to the database
    """
    try:
        config = _get_config(directory, x_arg)
        command.downgrade(config, revision, sql=sql, tag=tag)
    except alembic.util.exc.CommandError as e:
        if "No connection could be established" in str(e):
            raise DatabaseConnectionError(f"Database connection error: {str(e)}")
        elif "Can't locate revision" in str(e):
            raise RevisionError(f"Revision error: {str(e)}")
        else:
            raise RevisionError(f"Failed to downgrade: {str(e)}")
    except Exception as e:
        if not isinstance(e, MigrationError):
            raise RevisionError(f"Unexpected error during downgrade: {str(e)}")
        raise


@handle_migration_errors
def show(directory: str = "migrations", revision: str = "head") -> None:
    """Show the revision(s).

    Args:
        directory: Directory where migration files are stored
        revision: Revision to show
    """
    command.show(_get_config(directory), revision)


@handle_migration_errors
def history(directory: str = "migrations", rev_range: Optional[str] = None, verbose: bool = False, indicate_current: bool = False) -> None:
    """List revision history.

    Args:
        directory: Directory where migration files are stored
        rev_range: Revision range to show
        verbose: Whether to show verbose output
        indicate_current: Whether to indicate the current revision
    """
    command.history(_get_config(directory), rev_range, verbose=verbose, indicate_current=indicate_current)


@handle_migration_errors
def heads(directory: str = "migrations", verbose: bool = False, resolve_dependencies: bool = False) -> None:
    """Show current available heads.

    Args:
        directory: Directory where migration files are stored
        verbose: Whether to show verbose output
        resolve_dependencies: Whether to resolve dependencies
    """
    command.heads(_get_config(directory), verbose=verbose, resolve_dependencies=resolve_dependencies)


@handle_migration_errors
def branches(directory: str = "migrations", verbose: bool = False) -> None:
    """Show current branch points.

    Args:
        directory: Directory where migration files are stored
        verbose: Whether to show verbose output
    """
    command.branches(_get_config(directory), verbose=verbose)


@handle_migration_errors
def current(directory: str = "migrations", verbose: bool = False) -> None:
    """Display the current revision.

    Args:
        directory: Directory where migration files are stored
        verbose: Whether to show verbose output
    """
    command.current(_get_config(directory), verbose=verbose)


@handle_migration_errors
def stamp(directory: str = "migrations", revision: str = "head", sql: bool = False, tag: Optional[str] = None, purge: bool = False) -> None:
    """'stamp' the revision table.

    Args:
        directory: Directory where migration files are stored
        revision: Revision to stamp
        sql: Whether to generate SQL
        tag: Tag to apply to the revision
        purge: Whether to purge the revision
    """
    command.stamp(_get_config(directory), revision, sql=sql, tag=tag, purge=purge)


@handle_migration_errors
def check(directory: str = "migrations") -> None:
    """Check if database is up to date.

    Args:
        directory: Directory where migration files are stored
    """
    command.check(_get_config(directory))


def configure_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Configure the argument parser for the migration commands.

    Args:
        parser: Argument parser to configure

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    subparsers = parser.add_subparsers(dest="command")

    # list_templates command
    subparsers.add_parser("list_templates", help="List available migration templates")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize a new migration repository")
    init_parser.add_argument("--directory", default="migrations", help="Migration script directory")
    init_parser.add_argument("--multidb", action="store_true", help="Multiple databases")
    init_parser.add_argument("--template", default=None, help="Migration template to use")
    init_parser.add_argument("--package", action="store_true", help="Create a package")
    init_parser.add_argument("--db-url", help="Database URL to use for migrations")
    init_parser.add_argument("--model-path", help="Path to the model file containing the Base class (e.g. myapp.models.Base)")

    # revision command
    revision_parser = subparsers.add_parser("revision", help="Create a new revision file")
    revision_parser.add_argument("--directory", default="migrations", help="Migration script directory")
    revision_parser.add_argument("--message", "-m", help="Revision message")
    revision_parser.add_argument("--autogenerate", action="store_true", help="Autogenerate migration")
    revision_parser.add_argument("--sql", action="store_true", help="Generate SQL")
    revision_parser.add_argument("--head", default="head", help="Head revision")
    revision_parser.add_argument("--splice", action="store_true", help="Splice revision")
    revision_parser.add_argument("--branch-label", help="Branch label")
    revision_parser.add_argument("--version-path", help="Version path")
    revision_parser.add_argument("--rev-id", help="Revision ID")

    # migrate command (alias for 'revision --autogenerate')
    migrate_parser = subparsers.add_parser("migrate", help='Alias for "revision --autogenerate"')
    migrate_parser.add_argument("--directory", default="migrations", help="Migration script directory")
    migrate_parser.add_argument("--message", "-m", help="Revision message")
    migrate_parser.add_argument("--sql", action="store_true", help="Generate SQL")
    migrate_parser.add_argument("--head", default="head", help="Head revision")
    migrate_parser.add_argument("--splice", action="store_true", help="Splice revision")
    migrate_parser.add_argument("--branch-label", help="Branch label")
    migrate_parser.add_argument("--version-path", help="Version path")
    migrate_parser.add_argument("--rev-id", help="Revision ID")
    migrate_parser.add_argument("-x", dest="x_arg", help="Additional arguments")

    # edit command
    edit_parser = subparsers.add_parser("edit", help="Edit the revision file")
    edit_parser.add_argument("--directory", default="migrations", help="Migration script directory")
    edit_parser.add_argument("revision", nargs="?", default="current", help="Revision to edit")

    # merge command
    merge_parser = subparsers.add_parser("merge", help="Merge two revisions")
    merge_parser.add_argument("--directory", default="migrations", help="Migration script directory")
    merge_parser.add_argument("revisions", help="Revisions to merge (comma-separated)")
    merge_parser.add_argument("--message", "-m", help="Merge message")
    merge_parser.add_argument("--branch-label", help="Branch label")
    merge_parser.add_argument("--rev-id", help="Revision ID")

    # upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade to a later revision")
    upgrade_parser.add_argument("--directory", default="migrations", help="Migration script directory")
    upgrade_parser.add_argument("revision", nargs="?", default="head", help="Revision to upgrade to")
    upgrade_parser.add_argument("--sql", action="store_true", help="Generate SQL")
    upgrade_parser.add_argument("--tag", help="Tag to apply to the revision")
    upgrade_parser.add_argument("-x", dest="x_arg", help="Additional arguments")

    # downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Revert to a previous revision")
    downgrade_parser.add_argument("--directory", default="migrations", help="Migration script directory")
    downgrade_parser.add_argument("revision", nargs="?", default="-1", help="Revision to downgrade to")
    downgrade_parser.add_argument("--sql", action="store_true", help="Generate SQL")
    downgrade_parser.add_argument("--tag", help="Tag to apply to the revision")
    downgrade_parser.add_argument("-x", dest="x_arg", help="Additional arguments")

    # show command
    show_parser = subparsers.add_parser("show", help="Show the revision(s)")
    show_parser.add_argument("--directory", default="migrations", help="Migration script directory")
    show_parser.add_argument("revision", nargs="?", default="head", help="Revision to show")

    # history command
    history_parser = subparsers.add_parser("history", help="List revision history")
    history_parser.add_argument("--directory", default="migrations", help="Migration script directory")
    history_parser.add_argument("--rev-range", help="Revision range")
    history_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    history_parser.add_argument("--indicate-current", action="store_true", help="Indicate current revision")

    # heads command
    heads_parser = subparsers.add_parser("heads", help="Show current available heads")
    heads_parser.add_argument("--directory", default="migrations", help="Migration script directory")
    heads_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    heads_parser.add_argument("--resolve-dependencies", action="store_true", help="Resolve dependencies")

    # branches command
    branches_parser = subparsers.add_parser("branches", help="Show current branch points")
    branches_parser.add_argument("--directory", default="migrations", help="Migration script directory")
    branches_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # current command
    current_parser = subparsers.add_parser("current", help="Display the current revision")
    current_parser.add_argument("--directory", default="migrations", help="Migration script directory")
    current_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # stamp command
    stamp_parser = subparsers.add_parser("stamp", help='"stamp" the revision table')
    stamp_parser.add_argument("--directory", default="migrations", help="Migration script directory")
    stamp_parser.add_argument("revision", nargs="?", default="head", help="Revision to stamp")
    stamp_parser.add_argument("--sql", action="store_true", help="Generate SQL")
    stamp_parser.add_argument("--tag", help="Tag to apply to the revision")
    stamp_parser.add_argument("--purge", action="store_true", help="Purge the revision")

    # check command
    check_parser = subparsers.add_parser("check", help="Check if database is up to date")
    check_parser.add_argument("--directory", default="migrations", help="Migration script directory")

    return parser


def execute_command(args: argparse.Namespace) -> None:
    """Execute the migration command.

    Args:
        args: Command arguments
    """
    if args.command == "list_templates":
        list_templates()
    elif args.command == "init":
        init(directory=args.directory, multidb=args.multidb, template=args.template, package=args.package, db_url=args.db_url, model_path=args.model_path)
    elif args.command == "revision":
        revision(
            directory=args.directory,
            message=args.message,
            autogenerate=args.autogenerate,
            sql=args.sql,
            head=args.head,
            splice=args.splice,
            branch_label=args.branch_label,
            version_path=args.version_path,
            rev_id=args.rev_id,
        )
    elif args.command == "migrate":
        migrate(
            directory=args.directory,
            message=args.message,
            sql=args.sql,
            head=args.head,
            splice=args.splice,
            branch_label=args.branch_label,
            version_path=args.version_path,
            rev_id=args.rev_id,
            x_arg=getattr(args, "x_arg", None),
        )
    elif args.command == "edit":
        edit(directory=args.directory, revision=args.revision)
    elif args.command == "merge":
        merge(directory=args.directory, revisions=args.revisions, message=args.message, branch_label=args.branch_label, rev_id=args.rev_id)
    elif args.command == "upgrade":
        upgrade(directory=args.directory, revision=args.revision, sql=args.sql, tag=args.tag, x_arg=getattr(args, "x_arg", None))
    elif args.command == "downgrade":
        downgrade(directory=args.directory, revision=args.revision, sql=args.sql, tag=args.tag, x_arg=getattr(args, "x_arg", None))
    elif args.command == "show":
        show(directory=args.directory, revision=args.revision)
    elif args.command == "history":
        history(directory=args.directory, rev_range=args.rev_range, verbose=args.verbose, indicate_current=args.indicate_current)
    elif args.command == "heads":
        heads(directory=args.directory, verbose=args.verbose, resolve_dependencies=args.resolve_dependencies)
    elif args.command == "branches":
        branches(directory=args.directory, verbose=args.verbose)
    elif args.command == "current":
        current(directory=args.directory, verbose=args.verbose)
    elif args.command == "stamp":
        stamp(directory=args.directory, revision=args.revision, sql=args.sql, tag=args.tag, purge=args.purge)
    elif args.command == "check":
        check(directory=args.directory)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)
