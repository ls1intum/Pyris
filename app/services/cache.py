from abc import ABC, abstractmethod
from datetime import datetime, timedelta


class CacheStoreInterface(ABC):
    @abstractmethod
    def get(self, name):
        """
        Return the value at key ``name``, or None if the key doesn't exist
        """
        pass

    @abstractmethod
    def set(self, name, value, ex=None):
        """
        Set the value at key ``name`` to ``value``

        ``ex`` sets an expire flag on key ``name`` for ``ex`` seconds.
        """
        pass

    @abstractmethod
    def expire(self, name, ex):
        """
        Set an expire flag on key ``name`` for ``ex`` seconds
        """
        pass

    @abstractmethod
    def incr(self, name):
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
    def delete(self, name):
        """
        Delete the key specified by ``name``
        """
        pass


class InMemoryCacheStore(CacheStoreInterface):
    def __init__(self):
        self._cache = {}

    def get(self, name):
        current_time = datetime.now()
        ttl = self._cache.get(f"{name}:ttl")
        if ttl and current_time > ttl:
            del self._cache[name]
            del self._cache[f"{name}:ttl"]
            return None

        return self._cache.get(name)

    def set(self, name, value, ex=None):
        self._cache[name] = value
        self.expire(name, ex)

    def expire(self, name, ex):
        if ex is None:
            ttl = None
        else:
            current_time = datetime.now()
            ttl = current_time + timedelta(seconds=ex)

        self._cache[f"{name}:ttl"] = ttl

    def incr(self, name):
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

    def delete(self, name):
        if name in self._cache:
            del self._cache[name]
            del self._cache[f"{name}:ttl"]


cache_store = InMemoryCacheStore()
