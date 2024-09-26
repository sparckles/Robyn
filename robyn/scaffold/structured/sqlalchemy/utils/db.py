from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from conf import settings

import logging

logger = logging.getLogger(__name__)


def get_pool():
    dsn = settings.database_url
    logger.info(f"creating client db pool with dsn: {dsn}")
    engine = create_engine(
        dsn,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_pool_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        echo=settings.db_pool_recycle,
    )
    return sessionmaker(bind=engine)()
