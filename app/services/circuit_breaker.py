from enum import Enum
from app.services.cache import cache_store


class CircuitBreaker:
    MAX_FAILURES = 3
    STATUS_CACHE_CLOSED_TTL = 300
    STATUS_CACHE_OPEN_TTL = 30

    class Status(str, Enum):
        OPEN = "OPEN"
        CLOSED = "CLOSED"

    @classmethod
    def protected_call(cls, func, cache_key: str, accepted_exceptions: tuple):
        num_failures_key = f"{cache_key}:num_failures"
        status_key = f"{cache_key}:status"

        status = cache_store.get(status_key)
        if status == cls.Status.OPEN:
            raise ValueError("Too many failures! Please try again later.")

        try:
            return func()
        except accepted_exceptions as e:
            raise e
        except Exception as e:
            num_failures = cache_store.incr(num_failures_key)
            cache_store.expire(num_failures_key, cls.STATUS_CACHE_OPEN_TTL)
            if num_failures >= cls.MAX_FAILURES:
                cache_store.set(
                    status_key, cls.Status.OPEN, ex=cls.STATUS_CACHE_OPEN_TTL
                )

            raise e

    @classmethod
    def get_status(cls, func, cache_key: str):
        status_key = f"{cache_key}:status"
        status = cache_store.get(status_key)

        if status:
            return cls.Status(status)

        is_up = False
        try:
            is_up = func()
        except Exception:
            ...

        if is_up:
            cache_store.set(
                status_key, cls.Status.CLOSED, ex=cls.STATUS_CACHE_CLOSED_TTL
            )
            return cls.Status.CLOSED

        cache_store.set(
            status_key, cls.Status.OPEN, ex=cls.STATUS_CACHE_OPEN_TTL
        )
        return cls.Status.OPEN
