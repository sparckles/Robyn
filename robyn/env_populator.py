import os 
import logging
from pathlib import Path



# Path to the root of the project
ROOT_DIR = Path(__file__).parent.parent

# Path to the environment variables
CONFIG_PATH = ROOT_DIR / 'robyn.env'

#set the logger that will log the environment variables imported from robyn.env and the ones already set
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# parse the configuration file returning a list of tuples (key, value) containing the environment variables
def parser(config_path=CONFIG_PATH):
    """Parse the configuration file"""
    with open(config_path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            yield line.strip().split('=')  


# check for the environment variables set in cli and if not set them
def load_vars(variables = None):
    """Main function"""
    
    variables = parser() 

    if variables is None:
        return

    for var in variables:
        if var[0] in os.environ:
            logger.info(f" Variable {var[0]} already set")
            continue
        else:
            os.environ[var[0]]=var[1]   
            logger.info(f" Variable {var[0]} set to {var[1]}")
            

    


