from robyn import SubRouter

router = SubRouter(__name__, prefix="/")


@router.get("livez/")
def livez() -> str:
    return "live"


@router.get("healthz/")
def healthz() -> str:
    return "healthy"
