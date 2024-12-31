from robyn.helpers import BaseConfig


class Settings(BaseConfig):
    service_port: int
    database_url: str
    db_pool_size: int
    db_pool_max_overflow: int
    db_pool_timeout: int
    db_pool_recycle: int
    db_pool_echo: bool


settings = Settings()
