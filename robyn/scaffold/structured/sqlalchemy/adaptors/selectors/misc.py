from sqlalchemy import text


async def sample_selector(conn):
    await conn.execute(text("select * from sample;"))
