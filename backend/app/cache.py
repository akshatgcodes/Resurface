"""Redis: a versioned cache for digest/stat computations, and a lock for the scheduler.

Invalidation uses a version counter instead of deleting keys: every write to the library
bumps `resurface:version`, and cache keys include the version. Old entries become
unreachable at once and simply expire, so there's no "which keys depend on this
highlight?" bookkeeping.

Redis is optional. Without REDIS_URL (or if Redis is down) everything is computed fresh.
"""

import json
import logging
import secrets
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import redis

from app.config import settings

log = logging.getLogger("resurface.cache")

PREFIX = "resurface"
VERSION_KEY = f"{PREFIX}:version"

# Delete the lock only if we still own it (a slow holder must not free someone else's lock)
RELEASE_LOCK = """
if redis.call("get", KEYS[1]) == ARGV[1] then return redis.call("del", KEYS[1]) end
return 0
"""

_client: redis.Redis | None = None


def get_redis() -> redis.Redis | None:
    global _client
    if _client is None and settings.redis_url:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def set_redis(client: redis.Redis | None) -> None:
    """Swap the client (tests use fakeredis)."""
    global _client
    _client = client


def bump_version() -> None:
    r = get_redis()
    if r is None:
        return
    try:
        r.incr(VERSION_KEY)
    except redis.RedisError:
        log.warning("couldn't bump cache version; cached views may be stale until TTL")


def cached_json(name: str, ttl: int, compute: Callable[[], Any]) -> tuple[Any, str]:
    """Returns (value, status) where status is HIT, MISS or BYPASS."""
    r = get_redis()
    if r is None:
        return compute(), "BYPASS"
    try:
        version = r.get(VERSION_KEY) or "0"
        key = f"{PREFIX}:v{version}:{name}"
        hit = r.get(key)
        if hit is not None:
            return json.loads(hit), "HIT"
    except redis.RedisError:
        log.warning("redis unavailable, computing %s without cache", name)
        return compute(), "BYPASS"
    value = compute()
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
    except redis.RedisError:
        pass
    return value, "MISS"


@contextmanager
def lock(name: str, ttl: int) -> Iterator[bool]:
    """Yields True if this process got the lock. With several API replicas, only one runs
    the scheduled digest. Without Redis there's a single process, so it always gets it."""
    r = get_redis()
    if r is None:
        yield True
        return
    key, token = f"{PREFIX}:lock:{name}", secrets.token_hex(8)
    try:
        acquired = bool(r.set(key, token, nx=True, ex=ttl))
    except redis.RedisError:
        acquired = True  # better a rare duplicate digest than none at all
        r = None
    try:
        yield acquired
    finally:
        if acquired and r is not None:
            try:
                r.eval(RELEASE_LOCK, 1, key, token)
            except redis.RedisError:
                pass


def claim_once(name: str, ttl: int) -> bool:
    """SET NX without release: marks a one-off job (like today's digest) as done."""
    r = get_redis()
    if r is None:
        return True
    try:
        return bool(r.set(f"{PREFIX}:once:{name}", "1", nx=True, ex=ttl))
    except redis.RedisError:
        return True
