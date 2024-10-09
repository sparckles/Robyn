from robyn import SubRouter

router = SubRouter(__name__, "/sample")


class SampleHandlers:
    """
    note: the handles being grouped in a class like this is complete optional, and doesn't have any impact on routing
    """

    @router.post("/one")
    @staticmethod
    def one(): ...

    @router.get("/two")
    @staticmethod
    def two(): ...


@router.get("three/")
def three():
    return {}
