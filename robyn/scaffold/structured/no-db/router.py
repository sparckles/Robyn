from robyn import Robyn
from api.handlers.probes import router as probes
from api.handlers.sample import router as sample


def build_routes() -> Robyn:
    mux: Robyn = Robyn(__file__)
    mux.include_router(probes)
    mux.include_router(sample)
    return mux
