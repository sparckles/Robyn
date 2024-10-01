from robyn import SubRouter

router = SubRouter(__name__, prefix="/sample/")


class SampleHandlers:
    @router.post("one/")
    @staticmethod
    def one(global_dependencies):
        with global_dependencies.get("pool") as session:
            # invoke your mutators/selectors here
            ...

    @router.get("two/")
    @staticmethod
    def two(): ...
