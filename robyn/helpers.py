import importlib
import pkgutil
from robyn import Robyn


def discover_routes() -> Robyn:
    mux: Robyn = Robyn(__file__)

    # Specify the package where your routers are located
    package_name = 'api.handlers'

    # Dynamically import routers
    package = importlib.import_module(package_name)

    # Iterate through the members of the package
    for _, module_name, _ in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
        module = importlib.import_module(module_name)

        # Get all members of the module and filter for routers
        for name, member in vars(module).items():
            if hasattr(member, 'include_router'):
                mux.include_router(member)

    return mux
