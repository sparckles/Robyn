from robyn import SubRouter

router = SubRouter(__name__, "/sample")


class SampleHandlers:
    @router.post("/one")
    @staticmethod
    def one(): ...

    @router.get("/two")
    @staticmethod
    def two(): ...
