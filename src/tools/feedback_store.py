import sqlite3
from contextlib import closing
from pathlib import Path


class FeedbackStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating IN (-1, 1)),
                    correction TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path, timeout=10)

    def save(
        self, session_id: str, query: str, rating: int, correction: str | None
    ) -> int:
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                "INSERT INTO feedback (session_id, query, rating, correction) "
                "VALUES (?, ?, ?, ?)",
                (session_id, query, rating, correction),
            )
            connection.commit()
            return int(cursor.lastrowid)
