import os 
from definitions import CONFIG_PATH

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
            print("Variable {} already set".format(var[0]))
            continue
        else:
            os.environ[var[0]]=var[1]   
            print(var[0], var[1])

    


