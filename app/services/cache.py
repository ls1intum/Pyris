from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Union


class CacheStoreInterface(ABC):
    @abstractmethod
    def get(self, name: str):
        """
        Return the value at key ``name``, or None if the key doesn't exist
        """
        pass

    @abstractmethod
    def set(self, name: str, value, ex: Union[int, None] = None):
        """
        Set the value at key ``name`` to ``value``

        ``ex`` sets an expire flag on key ``name`` for ``ex`` seconds.
        """
        pass

    @abstractmethod
    def expire(self, name: str, ex: int):
        """
        Set an expire flag on key ``name`` for ``ex`` seconds
        """
        pass

    @abstractmethod
    def incr(self, name: str):
        """Increase the integer value of a key ``name`` by 1.
        If the key does not exist, it is set to 0
        before performing the operation.
        """
        pass

    @abstractmethod
    def flushdb(self):
        """
        Delete all keys in the current database
        """
        pass

    @abstractmethod
    def delete(self, name: str):
        """
        Delete the key specified by ``name``
        """
        pass


class InMemoryCacheStore(CacheStoreInterface):
    def __init__(self):
        self._cache = {}

    def get(self, name: str):
        current_time = datetime.now()
        ttl = self._cache.get(f"{name}:ttl")
        if ttl and current_time > ttl:
            del self._cache[name]
            del self._cache[f"{name}:ttl"]
            return None

        return self._cache.get(name)

    def set(self, name: str, value, ex: Union[int, None] = None):
        self._cache[name] = value
        if ex is None:
            self._cache[f"{name}:ttl"] = None
        else:
            self.expire(name, ex)

    def expire(self, name: str, ex: int):
        current_time = datetime.now()
        ttl = current_time + timedelta(seconds=ex)

        self._cache[f"{name}:ttl"] = ttl

    def incr(self, name: str):
        value = self.get(name)
        if value is None:
            self._cache[name] = 1
        elif isinstance(value, int):
            self._cache[name] += 1
        else:
            raise TypeError("value is not an integer")

        return self._cache[name]

    def flushdb(self):
        self._cache = {}

    def delete(self, name: str):
        if name in self._cache:
            del self._cache[name]
            del self._cache[f"{name}:ttl"]


cache_store = InMemoryCacheStore()
