from robyn import SubRouter

router = SubRouter("/sample")


class SampleHandlers:

    @router.get("/one")
    @staticmethod
    def one():
        ...

    @router.get("/two")
    @staticmethod
    def two():
        ...
