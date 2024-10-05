
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine
from conf import settings

def get_pool():
    return create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_pool_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        echo=settings.db_pool_echo,
        query_cache_size=0,
    )

@asynccontextmanager
async def get_db_connection(engine):
    async with engine.connect() as conn:
        yield conn


