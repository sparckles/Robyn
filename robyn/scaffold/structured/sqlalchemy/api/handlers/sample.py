from robyn import SubRouter
from adaptors.selectors.misc import sample_selector

router = SubRouter(__name__, prefix="/sample/")


class SampleHandlers:
    @router.post("one/")
    @staticmethod
    def one(global_dependencies):
        with global_dependencies.get("pool") as session:
            # invoke your mutators/selectors here
            sample_selector(session)

    @router.get("two/")
    @staticmethod
    def two(): ...
