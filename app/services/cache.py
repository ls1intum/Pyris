from abc import ABC, abstractmethod
from datetime import datetime, timedelta


class CacheStoreInterface(ABC):
    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def set(self, key, value, ex=None):
        pass

    @abstractmethod
    def expire(self, key, ex):
        pass

    @abstractmethod
    def incr(self, key):
        """Increase the integer value of a key by 1.
        If the key does not exist, it is set to 0
        before performing the operation.
        """
        pass

    @abstractmethod
    def flushdb(self):
        pass

    @abstractmethod
    def delete(self, key):
        pass


class InMemoryCacheStore(CacheStoreInterface):
    def __init__(self):
        self._cache = {}

    def get(self, key):
        current_time = datetime.now()
        ttl = self._cache.get(f"{key}:ttl")
        if ttl and current_time > ttl:
            del self._cache[key]
            del self._cache[f"{key}:ttl"]
            return None

        return self._cache.get(key)

    def set(self, key, value, ex=None):
        self._cache[key] = value
        self.expire(key, ex)

    def expire(self, key, ex):
        if ex is None:
            ttl = None
        else:
            current_time = datetime.now()
            ttl = current_time + timedelta(seconds=ex)

        self._cache[f"{key}:ttl"] = ttl

    def incr(self, key):
        value = self.get(key)
        if value is None:
            self._cache[key] = 1
        elif isinstance(value, int):
            self._cache[key] += 1
        else:
            raise TypeError("value is not an integer")

        return self._cache[key]

    def flushdb(self):
        self._cache = {}

    def delete(self, key):
        if key in self._cache:
            del self._cache[key]
            del self._cache[f"{key}:ttl"]


cache_store = InMemoryCacheStore()
