import os 
from definitions import CONFIG_PATH

# parse the configuration file returning a list of tuples (key, value) containing the environment variables
def parser():
    """Parse the configuration file"""
    with open(CONFIG_PATH, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            yield line.strip().split('=')  


# check for the environment variables set in cli and if not set them

def load_vars(variables = parser()):
    """Main function"""
    for var in variables:
        if var[0] in os.environ:
            continue
    else:
        os.environ[var[0]]=var[1]   
    

    


