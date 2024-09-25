from robyn.helpers import discover_routes
from robyn import Robyn

from conf import settings

app: Robyn = discover_routes("api.handlers")
# note: if you prefer to manuall refine routes, use your build_routes function instead


if __name__ == "__main__":
    app.start(host="0.0.0.0", port=settings.service_port)
