from robyn import SubRouter


router = SubRouter("/")


@router.get("/livez/")
def livez() -> str:
    return "live"


@router.get("/healthz/")
def healthz() -> str:
    return "healthy"
