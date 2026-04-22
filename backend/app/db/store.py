import aiosqlite

from app.models.trip import Trip

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS trips (
    id TEXT PRIMARY KEY,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    state TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


class TripStore:
    def __init__(self, db_path: str = "tourguide.db"):
        self.db_path = db_path
        self._initialized = False

    async def _ensure_table(self, db: aiosqlite.Connection) -> None:
        if not self._initialized:
            await db.execute(CREATE_TABLE_SQL)
            await db.commit()
            self._initialized = True

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_table(db)

    async def save(self, trip: Trip) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_table(db)
            await db.execute(
                """
                INSERT INTO trips (id, origin, destination, state, data)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    state = excluded.state,
                    data = excluded.data,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (trip.id, trip.origin, trip.destination, trip.state.value, trip.model_dump_json()),
            )
            await db.commit()

    async def get(self, trip_id: str) -> Trip | None:
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_table(db)
            cursor = await db.execute("SELECT data FROM trips WHERE id = ?", (trip_id,))
            row = await cursor.fetchone()
            if row is None:
                return None
            return Trip.model_validate_json(row[0])

    async def list_trips(self, limit: int = 50) -> list[Trip]:
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_table(db)
            cursor = await db.execute(
                "SELECT data FROM trips ORDER BY updated_at DESC LIMIT ?", (limit,)
            )
            rows = await cursor.fetchall()
            return [Trip.model_validate_json(row[0]) for row in rows]
