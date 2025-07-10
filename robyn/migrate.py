import os
import sys
from functools import wraps
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure alembic is installed
try:
    import alembic
    from alembic import command
    from alembic.config import Config as AlembicConfig
except ImportError:
    raise ImportError("Alembic has not been installed. Please run 'pip install alembic' to install it.")


class _RobynMigrateConfig:
    """Robyn migration configuration."""

    def __init__(self, directory: str = "migrations", **kwargs):
        self.directory = directory
        self.kwargs = kwargs


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


class Migrate:
    """Robyn extension for database migrations using Alembic."""

    def __init__(self, app=None, db=None, directory="migrations", **kwargs):
        """Initialize the extension.

        Args:
            app: The Robyn application instance
            db: The SQLAlchemy database instance
            directory: Directory where migration files will be stored
            **kwargs: Additional arguments to pass to Alembic
        """
        self.app = app
        self.db = db
        self.directory = directory
        self.kwargs = kwargs

        if app is not None and db is not None:
            self.init_app(app, db, directory, **kwargs)

    def init_app(self, app, db=None, directory=None, **kwargs):
        """Initialize the application with this extension.

        Args:
            app: The Robyn application instance
            db: The SQLAlchemy database instance
            directory: Directory where migration files will be stored
            **kwargs: Additional arguments to pass to Alembic
        """
        self.app = app
        self.db = db
        self.directory = directory or self.directory
        self.kwargs = kwargs or self.kwargs

        # Register before_request handler to ensure database connection
        @app.before_request()
        async def ensure_db_connection(request):
            # This could be used to ensure database connection is established
            # or perform any pre-request database setup
            pass

        # Register after_request handler to clean up database resources
        @app.after_request()
        async def cleanup_db_resources(response):
            # This could be used to clean up database resources after request
            return response


def catch_errors(f):
    """Decorator to catch and handle errors."""

    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(f"ERROR: {str(e)}")
            sys.exit(1)

    return wrapped


def _get_config(directory: str, x_arg: Optional[str] = None, opts: Optional[Dict[str, Any]] = None) -> Config:
    """Get the Alembic configuration.

    Args:
        directory: Directory where migration files are stored
        x_arg: Extra arguments to pass to Alembic
        opts: Additional options to pass to Alembic

    Returns:
        Config: Robyn migration configuration
    """
    config = Config(directory)
    if x_arg is not None:
        config.cmd_opts = argparse.Namespace(x=x_arg)
    return config


@catch_errors
def list_templates() -> None:
    """List available migration templates."""
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    templates = os.listdir(templates_dir)
    for template in templates:
        print(template)


def _auto_configure_migrations(directory: str, db_url: Optional[str] = None, model_path: Optional[str] = None) -> None:
    """自动配置 alembic.ini 和 env.py 文件

    Args:
        directory: 迁移文件目录
        db_url: 数据库 URL
        model_path: 模型文件路径
    """
    # Configure alembic.ini
    if db_url:
        alembic_ini_path = os.path.join(directory, "alembic.ini")
        if os.path.exists(alembic_ini_path):
            with open(alembic_ini_path, "r") as f:
                content = f.read()

            # Replace the database URL
            content = content.replace("sqlalchemy.url = driver://user:pass@localhost/dbname", f"sqlalchemy.url = {db_url}")

            with open(alembic_ini_path, "w") as f:
                f.write(content)
            print(f"Successfully configured the database URL: {db_url}")

    # 配置 env.py
    if model_path:
        env_py_path = os.path.join(directory, "env.py")
        if os.path.exists(env_py_path):
            with open(env_py_path, "r") as f:
                content = f.read()

            try:
                module_path, class_name = model_path.rsplit(".", 1)

                # Replace the import statement and target_metadata setting
                # Allow importing from the parent directory
                import_statement = f"sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))\nfrom {module_path} import {class_name}\ntarget_metadata = {class_name}.metadata"

                # Replace the import statement
                content = content.replace(
                    "# add your model's MetaData object here\n# for 'autogenerate' support\n# from myapp import mymodel\n# target_metadata = mymodel.Base.metadata",
                    f"# add your model's MetaData object here\n# for 'autogenerate' support\n{import_statement}",
                )

                # Replace the target_metadata setting
                content = content.replace(
                    "target_metadata = config.attributes.get('sqlalchemy.metadata', None)",
                    "# target_metadata = config.attributes.get('sqlalchemy.metadata', None)\n# Already set by the import above",
                )

                with open(env_py_path, "w") as f:
                    f.write(content)
                print(f"Successfully configured the model path: {model_path}")
            except ValueError:
                print(f"Warning: Could not parse the model path {model_path}, please manually configure env.py")


@catch_errors
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
                import importlib.util

                spec = importlib.util.find_spec("models")
                if spec is not None:
                    models_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(models_module)
                    db_url = str(models_module.engine.url)
                else:
                    raise ImportError("Cannot find models module")
        except Exception:
            print('Please provide your database URL with "--db-url=<YOUR_DB_URL>".')
            return
    if not model_path:
        try:
            # Try to import models from current working directory
            try:
                from models import Base

                model_path = "models.Base"
            except ImportError:
                # Try to import models module dynamically
                import importlib.util

                spec = importlib.util.find_spec("models")
                if spec is not None:
                    models_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(models_module)
                    if hasattr(models_module, "Base"):
                        model_path = "models.Base"
                    else:
                        raise AttributeError("models module does not have Base attribute")
                else:
                    raise ImportError("Cannot find models module")
        except Exception:
            print('Please provide your model path with "--model-path=<YOUR_MODEL_PATH>".')
            return

    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)

    config = Config(directory)
    template_path = config._get_template_path(template) if template is not None else config._get_template_path()
    command.init(config, directory, template=template_path, package=package)

    _auto_configure_migrations(directory, db_url, model_path)


@catch_errors
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
    """
    command.revision(
        _get_config(directory),
        message,
        autogenerate=autogenerate,
        sql=sql,
        head=head,
        splice=splice,
        branch_label=branch_label,
        version_path=version_path,
        rev_id=rev_id,
    )


@catch_errors
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
    """
    command.revision(
        _get_config(directory, x_arg),
        message,
        autogenerate=True,
        sql=sql,
        head=head,
        splice=splice,
        branch_label=branch_label,
        version_path=version_path,
        rev_id=rev_id,
    )


@catch_errors
def edit(directory: str = "migrations", revision: str = "current") -> None:
    """Edit the revision file.

    Args:
        directory: Directory where migration files are stored
        revision: Revision to edit
    """
    command.edit(_get_config(directory), revision)


@catch_errors
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


@catch_errors
def upgrade(directory: str = "migrations", revision: str = "head", sql: bool = False, tag: Optional[str] = None, x_arg: Optional[str] = None) -> None:
    """Upgrade to a later revision.

    Args:
        directory: Directory where migration files are stored
        revision: Revision to upgrade to
        sql: Whether to generate SQL
        tag: Tag to apply to the revision
        x_arg: Extra arguments to pass to Alembic
    """
    command.upgrade(_get_config(directory, x_arg), revision, sql=sql, tag=tag)


@catch_errors
def downgrade(directory: str = "migrations", revision: str = "-1", sql: bool = False, tag: Optional[str] = None, x_arg: Optional[str] = None) -> None:
    """Revert to a previous revision.

    Args:
        directory: Directory where migration files are stored
        revision: Revision to downgrade to
        sql: Whether to generate SQL
        tag: Tag to apply to the revision
        x_arg: Extra arguments to pass to Alembic
    """
    command.downgrade(_get_config(directory, x_arg), revision, sql=sql, tag=tag)


@catch_errors
def show(directory: str = "migrations", revision: str = "head") -> None:
    """Show the revision(s).

    Args:
        directory: Directory where migration files are stored
        revision: Revision to show
    """
    command.show(_get_config(directory), revision)


@catch_errors
def history(directory: str = "migrations", rev_range: Optional[str] = None, verbose: bool = False, indicate_current: bool = False) -> None:
    """List revision history.

    Args:
        directory: Directory where migration files are stored
        rev_range: Revision range to show
        verbose: Whether to show verbose output
        indicate_current: Whether to indicate the current revision
    """
    command.history(_get_config(directory), rev_range, verbose=verbose, indicate_current=indicate_current)


@catch_errors
def heads(directory: str = "migrations", verbose: bool = False, resolve_dependencies: bool = False) -> None:
    """Show current available heads.

    Args:
        directory: Directory where migration files are stored
        verbose: Whether to show verbose output
        resolve_dependencies: Whether to resolve dependencies
    """
    command.heads(_get_config(directory), verbose=verbose, resolve_dependencies=resolve_dependencies)


@catch_errors
def branches(directory: str = "migrations", verbose: bool = False) -> None:
    """Show current branch points.

    Args:
        directory: Directory where migration files are stored
        verbose: Whether to show verbose output
    """
    command.branches(_get_config(directory), verbose=verbose)


@catch_errors
def current(directory: str = "migrations", verbose: bool = False) -> None:
    """Display the current revision.

    Args:
        directory: Directory where migration files are stored
        verbose: Whether to show verbose output
    """
    command.current(_get_config(directory), verbose=verbose)


@catch_errors
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


@catch_errors
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
