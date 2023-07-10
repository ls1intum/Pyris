import pytest
from datetime import datetime
from freezegun import freeze_time


class TestInMemoryCacheStore:
    def test_set_and_get(self, test_cache_store):
        test_cache_store.set("test_key", "test_value")
        assert test_cache_store.get("test_key") == "test_value"
        assert test_cache_store._cache["test_key"].ttl is None

    @freeze_time("2023-06-16 03:21:34 +02:00")
    def test_set_and_get_an_existing_key(self, test_cache_store):
        test_cache_store.set("test_key", "test_value", ex=30)
        assert test_cache_store.get("test_key") == "test_value"
        assert test_cache_store._cache["test_key"].ttl == datetime(
            year=2023, month=6, day=16, hour=1, minute=22, second=4
        )

        test_cache_store.set("test_key", "test_value2")
        assert test_cache_store.get("test_key") == "test_value2"
        assert test_cache_store._cache["test_key"].ttl is None

    def test_set_and_get_before_ttl(self, test_cache_store):
        initial_datetime = datetime(
            year=1, month=1, day=1, hour=15, minute=2, second=3
        )
        other_datetime = datetime(
            year=1, month=1, day=1, hour=15, minute=2, second=34
        )

        with freeze_time(initial_datetime) as frozen_datetime:
            test_cache_store.set("test_key", "test_value", ex=40)
            assert test_cache_store.get("test_key") == "test_value"
            assert test_cache_store._cache["test_key"].ttl == datetime(
                year=1, month=1, day=1, hour=15, minute=2, second=43
            )

            frozen_datetime.move_to(other_datetime)

            assert test_cache_store.get("test_key") == "test_value"
            assert test_cache_store._cache["test_key"].ttl == datetime(
                year=1, month=1, day=1, hour=15, minute=2, second=43
            )

    def test_set_and_get_after_ttl(self, test_cache_store):
        initial_datetime = datetime(
            year=1, month=1, day=1, hour=15, minute=2, second=3
        )
        other_datetime = datetime(
            year=1, month=1, day=1, hour=15, minute=2, second=34
        )

        with freeze_time(initial_datetime) as frozen_datetime:
            test_cache_store.set("test_key", "test_value", ex=30)
            assert test_cache_store.get("test_key") == "test_value"
            assert test_cache_store._cache["test_key"].ttl == datetime(
                year=1, month=1, day=1, hour=15, minute=2, second=33
            )

            frozen_datetime.move_to(other_datetime)

            assert test_cache_store.get("test_key") is None
            assert "test_key" not in test_cache_store._cache

    @freeze_time("2023-06-16 03:21:34 +02:00")
    def test_expire_a_existing_key(self, test_cache_store):
        test_cache_store.set("test_key", "test_value")
        test_cache_store.expire("test_key", 30)
        assert test_cache_store._cache["test_key"].ttl == datetime(
            year=2023, month=6, day=16, hour=1, minute=22, second=4
        )

    @freeze_time("2023-06-16 03:21:34 +02:00")
    def test_expire_a_non_existing_key(self, test_cache_store):
        test_cache_store.expire("test_key", 30)
        assert "test_key" not in test_cache_store._cache

    def test_incr_a_non_existing_key(self, test_cache_store):
        response = test_cache_store.incr("test_key")
        assert response == 1
        assert test_cache_store.get("test_key") == 1

    def test_incr_a_existing_key(self, test_cache_store):
        test_cache_store.set("test_key", 1)
        response = test_cache_store.incr("test_key")
        assert response == 2
        assert test_cache_store.get("test_key") == 2

    def test_incr_a_existing_key_not_a_number(self, test_cache_store):
        test_cache_store.set("test_key", "not a number")

        with pytest.raises(TypeError, match="value is not an integer"):
            test_cache_store.incr("test_key")

    def test_flushdb(self, test_cache_store):
        test_cache_store.set("test_key", "test_value")
        test_cache_store.flushdb()

        assert test_cache_store._cache == {}

    def test_delete_a_non_existing_key(self, test_cache_store):
        test_cache_store.delete("test_key")

        assert test_cache_store.get("test_key") is None
        assert "test_key" not in test_cache_store._cache

    def test_delete_a_existing_key(self, test_cache_store):
        test_cache_store.set("test_key", "test_value", ex=1000)
        test_cache_store.delete("test_key")

        assert test_cache_store.get("test_key") is None
        assert "test_key" not in test_cache_store._cache
