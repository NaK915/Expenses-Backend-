from app.store import ensure_indexes, ping_db


async def initialize_database() -> None:
    await ensure_indexes()
