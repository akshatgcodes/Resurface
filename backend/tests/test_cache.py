import redis as redis_lib

from app import cache


def test_miss_then_hit(redis):
    calls = []
    compute = lambda: calls.append(1) or {"n": len(calls)}  # noqa: E731
    assert cache.cached_json("x", 60, compute) == ({"n": 1}, "MISS")
    assert cache.cached_json("x", 60, compute) == ({"n": 1}, "HIT")
    assert len(calls) == 1


def test_version_bump_invalidates(redis):
    cache.cached_json("x", 60, lambda: 1)
    cache.bump_version()
    assert cache.cached_json("x", 60, lambda: 2) == (2, "MISS")


def test_bypass_without_redis():
    cache.set_redis(None)
    assert cache.cached_json("x", 60, lambda: 5) == (5, "BYPASS")
    with cache.lock("job", 10) as got:
        assert got


class BrokenRedis:
    def __getattr__(self, name):
        def fail(*a, **k):
            raise redis_lib.ConnectionError("down")

        return fail


def test_redis_outage_falls_back():
    cache.set_redis(BrokenRedis())
    assert cache.cached_json("x", 60, lambda: 7) == (7, "BYPASS")
    cache.bump_version()  # must not raise
    assert cache.claim_once("today", 60) is True


def test_lock_is_exclusive_and_released(redis):
    with cache.lock("job", 30) as first:
        with cache.lock("job", 30) as second:
            assert first and not second
    with cache.lock("job", 30) as again:
        assert again


def test_lock_not_released_by_other_owner(redis):
    with cache.lock("job", 30) as got:
        assert got
        # Simulate expiry + someone else taking the lock
        redis.set("resurface:lock:job", "someone-else")
    assert redis.get("resurface:lock:job") == "someone-else"


def test_claim_once(redis):
    assert cache.claim_once("digest:2024-09-20", 60) is True
    assert cache.claim_once("digest:2024-09-20", 60) is False
    assert cache.claim_once("digest:2024-09-21", 60) is True
