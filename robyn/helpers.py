import importlib
import pkgutil
from robyn import Robyn

import logging
logger = logging.getLogger(__name__)


def discover_routes(handler_path: str = "api.handlers") -> Robyn:
    mux: Robyn = Robyn(__file__)
    package = importlib.import_module(handler_path)
    for _, module_name, _ in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
        module = importlib.import_module(module_name)
        for name, member in vars(module).items():
            if hasattr(member, 'include_router'):
                logger.info(f"detected route: {name}")
                mux.include_router(member)
    return mux
