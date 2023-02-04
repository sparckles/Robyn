import os
import pathlib

from robyn.env_populator import load_vars, parser


# this tests if a connection can be made to the server with the correct port imported from the env file
def test_env_population(test_session, env_file):
    path = pathlib.Path(__file__).parent
    env_path = path / "robyn.env"
    load_vars(variables=parser(config_path=env_path))
    PORT = os.environ["ROBYN_PORT"]
    HOST = os.environ["ROBYN_URL"]
    assert PORT == "8080"
    assert HOST == "127.0.0.1"
