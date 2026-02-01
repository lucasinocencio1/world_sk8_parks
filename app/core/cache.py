import time
from typing import Any, Optional


class TTLCache:
    """
    Simple in-memory cache with TTL.
    Suitable for MVPs. Can be replaced with Redis later.
    """

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if not item:
            return None

        value, expires_at = item
        if time.time() > expires_at:
            self._store.pop(key, None)
            return None

        return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        expires_at = time.time() + ttl_seconds
        self._store[key] = (value, expires_at)