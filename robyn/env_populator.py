import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


# parse the configuration file returning a list of tuples (key, value) containing the environment variables
def parser(config_path=None, project_root=""):
    """Find robyn.env file in root of the project and parse it"""
    if config_path is None:
        config_path = Path(project_root) / "robyn.env"

    if config_path.exists():
        with open(config_path, "r") as f:
            for line in f:
                line = line.strip()
                # Skip blank lines and comments so they do not yield a
                # malformed (key-only) pair that crashes load_vars().
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    logger.warning(" Ignoring malformed robyn.env line: %r", line)
                    continue
                # maxsplit=1 so values containing '=' (e.g. base64 secrets)
                # are preserved instead of being truncated at the first '='.
                yield line.split("=", 1)


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
