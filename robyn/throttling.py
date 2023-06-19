import time
from typing import Optional
from redis import ConnectionPool, Redis

from robyn.robyn import HttpMethod


def initialize_redis_pool(host: Optional[str]) -> Optional[ConnectionPool]:
    if host is None:
        return None
    return ConnectionPool(host=host, port=6379, db=0)


class RateLimiter:
    def __init__(
        self,
        *,
        app=None,
        calls_limit: int = 0,
        limit_ttl: int = 0,
    ) -> None:
        self.app = app
        self.calls_limit = calls_limit
        self.limit_ttl = limit_ttl

    @property
    def has_limit(self) -> bool:
        return self.limit_ttl > 0 and self.calls_limit > 0

    def limit_exceeded(
        self,
        route_type: HttpMethod,
        endpoint: str,
        client: str,
        pool: Optional[ConnectionPool],
    ) -> bool:
        if not self.has_limit:
            return False
        limit_key = f"{endpoint}::{route_type}::{client}"
        current_timestamp = int(time.time())
        if pool:
            conn = Redis(connection_pool=pool)
            conn.zadd(limit_key, {str(current_timestamp): current_timestamp})
            conn.zremrangebyscore(limit_key, "-inf", current_timestamp - self.limit_ttl)
            conn.expire(limit_key, self.limit_ttl)
            calls_count = conn.zcard(limit_key)
        elif self.app:
            calls = self.app.get_calls_list(
                limit_key, self.limit_ttl, current_timestamp
            )
            calls_count = len(calls)
        else:
            raise ValueError("Both app and pool are None, no cache exists!")
        return calls_count > self.calls_limit
