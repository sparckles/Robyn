import time
from typing import Dict


class RateLimiter:
    """
    A rate limiter class that checks if a limit of API calls has been exceeded.
    """

    def __init__(
        self,
        *,
        calls_limit: int = 0,
        limit_ttl: int = 0,
    ) -> None:
        """
        Initialize the RateLimiter with the given rate limit parameters.

        :param calls_limit: The maximum number of API calls allowed within the given limit_ttl window.
                            Default is 0, which means no rate limit is applied.
        :param limit_ttl: The time-to-live (TTL) in seconds for the rate limit window.
                          Default is 0, which means no rate limit is applied.
        """

        self.calls_limit = calls_limit
        self.limit_ttl = limit_ttl

    @property
    def has_limit(self) -> bool:
        """
        Check if the RateLimiter has a valid rate limit set.

        :return: True if the rate limit is valid (calls_limit and limit_ttl > 0), False otherwise.
        """

        return self.limit_ttl > 0 and self.calls_limit > 0

    def limit_exceeded(self, headers: Dict[str, str]) -> bool:
        """
        Check if the rate limit has been exceeded based on the provided headers.

        :param headers: The headers containing the API call timestamps.

        :return: True if the rate limit has been exceeded, False otherwise.
        """

        if not self.has_limit:
            return False
        calls = headers.get("x-robyncc", "").split(",")
        if not calls:
            return False
        current_timestamp = int(time.time())
        ttl = current_timestamp - self.limit_ttl
        valid_calls = [c for c in calls if int(c) >= ttl]
        return len(valid_calls) > self.calls_limit
