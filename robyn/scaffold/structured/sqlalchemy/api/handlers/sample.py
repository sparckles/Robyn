from robyn import SubRouter
from adaptors.selectors.misc import sample_selector
from utils.db import get_db_connection

router = SubRouter(__name__, prefix="/sample/")


class SampleHandlers:
    @router.post("one/")
    @staticmethod
    async def one(global_dependencies):
        pool = global_dependencies.get("pool")
        async with get_db_connection(pool) as conn:
            # invoke your mutators/selectors here
            await sample_selector(conn)

    @router.get("two/")
    @staticmethod
    def two(): ...
