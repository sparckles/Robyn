import time
from typing import Dict


class RateLimiter:
    def __init__(
        self,
        *,
        calls_limit: int = 0,
        limit_ttl: int = 0,
    ) -> None:
        self.calls_limit = calls_limit
        self.limit_ttl = limit_ttl

    @property
    def has_limit(self) -> bool:
        return self.limit_ttl > 0 and self.calls_limit > 0

    def limit_exceeded(self, headers: Dict[str, str]) -> bool:
        if not self.has_limit:
            return False
        calls = headers.get("x-robyncc", "").split(",")
        if not calls:
            return False
        current_timestamp = int(time.time())
        ttl = current_timestamp - self.limit_ttl
        valid_calls = [c for c in calls if int(c) >= ttl]
        return len(valid_calls) > self.calls_limit
