import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_TRUE_VALUES = ("1", "true", "yes")


def env_bool(value, default=False):
    """Parse a robyn.env-style boolean string.

    bool("False") is True in Python, so ROBYN_BROWSER_OPEN=False used to enable
    the setting. Unset values keep `default`.
    """
    if value is None:
        return bool(default)
    return str(value).strip().lower() in _TRUE_VALUES


# parse the configuration file returning a list of tuples (key, value) containing the environment variables
def parser(config_path=None, project_root=""):
    """Find robyn.env file in root of the project and parse it"""
    if config_path is None:
        config_path = Path(project_root) / "robyn.env"

    if config_path.exists():
        with open(config_path, "r") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                yield line.strip().split("=")


# check for the environment variables set in cli and if not set them
def load_vars(variables=None, project_root=""):
    """Main function"""

    if variables is None:
        variables = parser(project_root=project_root)

    for var in variables:
        if var[0] in os.environ:
            logger.info(" Variable %s already set", var[0])
            continue
        else:
            os.environ[var[0]] = var[1]
            logger.info(" Variable %s set to %s", var[0], var[1])
