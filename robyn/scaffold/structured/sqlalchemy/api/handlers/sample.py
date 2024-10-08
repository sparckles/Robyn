from robyn import SubRouter
from adaptors.selectors.misc import sample_selector
from utils.db import get_db_connection

router = SubRouter(__name__, prefix="/sample/")


class SampleHandlers:
    """
    note: the handles being grouped in a class like this is complete optional, and doesn't have any impact on routing
    """

    @staticmethod
    @router.post("one/")
    async def one(global_dependencies):
        pool = global_dependencies.get("pool")
        async with get_db_connection(pool) as conn:
            # invoke your mutators/selectors here
            res = await sample_selector(conn)
            print(res)
        return {}

    @staticmethod
    @router.get("two/")
    def two():
        return {}

@router.get("three/")
def three():
    return {}
