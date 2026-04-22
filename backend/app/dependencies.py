from functools import lru_cache

from app.config import Settings
from app.db.store import TripStore


@lru_cache
def get_settings() -> Settings:
    return Settings()


_store: TripStore | None = None


async def get_store() -> TripStore:
    global _store
    if _store is None:
        _store = TripStore()
        await _store.init()
    return _store
