import time
from functools import wraps
from typing import Callable, Any, Dict


class SimpleTTLCache:
    def __init__(self, ttl: int = 120):
        self.ttl = ttl
        self.store: Dict[str, tuple] = {}

    def get(self, key: str):
        entry = self.store.get(key)
        if not entry:
            return None
        val, expires = entry
        if time.time() > expires:
            del self.store[key]
            return None
        return val

    def set(self, key: str, value: Any):
        self.store[key] = (value, time.time() + self.ttl)


def ttl_cache(ttl: int = 120):
    cache = SimpleTTLCache(ttl=ttl)

    def decorator(func: Callable):
        @wraps(func)
        def wrapped(*args, **kwargs):
            # build a simple key from args/kwargs (not perfect but OK for our use)
            key = func.__name__ + '|' + '|'.join(map(str, args)) + '|' + str(kwargs)
            val = cache.get(key)
            if val is not None:
                return val
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        return wrapped

    return decorator
