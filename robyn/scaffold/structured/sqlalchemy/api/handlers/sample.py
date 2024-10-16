from adaptors.selectors.misc import sample_selector
from utils.db import get_db_connection

from robyn import SubRouter

router = SubRouter(__name__, prefix="/sample/")


@router.post("one/")
async def one(global_dependencies):
    pool = global_dependencies.get("pool")
    async with get_db_connection(pool) as conn:
        # invoke your mutators/selectors here
        res = await sample_selector(conn)
        print(res)
    return {}


@router.get("two/")
def two():
    return {}


@router.get("three/")
def three():
    return {}
