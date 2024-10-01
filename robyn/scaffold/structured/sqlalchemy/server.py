from robyn.helpers import discover_routes
from robyn import Robyn

from utils.db import get_pool
from conf import settings

app: Robyn = discover_routes("api.handlers")
# note: if you prefer to manuall refine routes, use your build_routes function instead

app.inject_global(pool=get_pool())


if __name__ == "__main__":
    app.start(host="0.0.0.0", port=settings.service_port)
