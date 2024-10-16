from robyn import SubRouter

router = SubRouter(__name__, "/sample")


@router.post("/one")
def one(): ...


@router.get("/two")
def two(): ...


@router.get("three/")
def three():
    return {}
