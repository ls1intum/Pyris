from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Union, Any
from pydantic import BaseModel


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
    class CacheValue(BaseModel):
        value: Any
        ttl: Union[datetime, None]

    def __init__(self):
        self._cache: dict[str, Union[InMemoryCacheStore.CacheValue, None]] = {}

    def get(self, name: str):
        current_time = datetime.now()
        data = self._cache.get(name)
        if data is None:
            return None
        if data.ttl and current_time > data.ttl:
            del self._cache[name]
            return None
        return data.value

    def set(self, name: str, value, ex: Union[int, None] = None):
        self._cache[name] = InMemoryCacheStore.CacheValue(
            value=value, ttl=None
        )
        if ex is not None:
            self.expire(name, ex)

    def expire(self, name: str, ex: int):
        current_time = datetime.now()
        ttl = current_time + timedelta(seconds=ex)
        data = self._cache.get(name)
        if data is None:
            return
        data.ttl = ttl

    def incr(self, name: str):
        value = self.get(name)
        if value is None:
            self._cache[name] = InMemoryCacheStore.CacheValue(
                value=1, ttl=None
            )
            return 1
        if isinstance(value, int):
            value += 1
            self.set(name, value)
            return value
        raise TypeError("value is not an integer")

    def flushdb(self):
        self._cache = {}

    def delete(self, name: str):
        if name in self._cache:
            del self._cache[name]


cache_store = InMemoryCacheStore()
