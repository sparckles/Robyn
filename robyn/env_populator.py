import os 
import logging
from pathlib import Path


#set the logger that will log the environment variables imported from robyn.env and the ones already set
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# detect the robyn.env file in the project
def find(name, path):
    for root, dirs, files in os.walk(path, topdown=False):
        if name in files:            
            return Path(os.path.join(root, name))

# parse the configuration file returning a list of tuples (key, value) containing the environment variables
def parser(entry_point=None):
    """Parse the configuration file"""
    if entry_point is not None:
        config_path = find('robyn.env', entry_point)

        if config_path.exists():
            with open(config_path, 'r') as f:
                for line in f:
                    if line.startswith('#'):
                        continue
                    yield line.strip().split('=')  


# check for the environment variables set in cli and if not set them
def load_vars(variables = None, search_from=None):
    """Main function"""
    
    if variables is None:
        variables = parser(entry_point=search_from)

    for var in variables:
        if var[0] in os.environ:
            logger.info(f" Variable {var[0]} already set")
            continue
        else:
            os.environ[var[0]]=var[1]   
            logger.info(f" Variable {var[0]} set to {var[1]}")
            




