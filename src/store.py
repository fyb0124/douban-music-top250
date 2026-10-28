"""存储层：SQLite 增量落库（幂等 upsert），支持断点续爬。"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from . import config

DDL = """
CREATE TABLE IF NOT EXISTS albums (
    rank       INTEGER PRIMARY KEY,
    title      TEXT    NOT NULL,
    artist     TEXT    NOT NULL,
    year       TEXT    NOT NULL,
    genre      TEXT    NOT NULL,
    rating     REAL    NOT NULL,
    votes      INTEGER NOT NULL,
    crawled_at TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_albums_rating ON albums(rating);
CREATE INDEX IF NOT EXISTS idx_albums_artist ON albums(artist);
"""

UPSERT = """
INSERT INTO albums (rank, title, artist, year, genre, rating, votes, crawled_at)
VALUES (:rank, :title, :artist, :year, :genre, :rating, :votes, :crawled_at)
ON CONFLICT(rank) DO UPDATE SET
    title      = excluded.title,
    artist     = excluded.artist,
    year       = excluded.year,
    genre      = excluded.genre,
    rating     = excluded.rating,
    votes      = excluded.votes,
    crawled_at = excluded.crawled_at;
"""


class AlbumStore:
    """封装 SQLite 读写，保证重复抓取不会产生重复行。"""

    def __init__(self, db_path: Path | str = config.DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(DDL)
        self._conn.commit()

    def __enter__(self) -> "AlbumStore":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def upsert_many(self, records: Iterable[dict]) -> int:
        stamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        rows = [{**rec, "crawled_at": stamp} for rec in records]
        with self._conn:
            self._conn.executemany(UPSERT, rows)
        return len(rows)

    def count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM albums").fetchone()[0])

    def max_rank(self) -> int:
        row = self._conn.execute("SELECT MAX(rank) FROM albums").fetchone()
        return int(row[0] or 0)

    def fetch_all(self) -> list[dict]:
        cursor = self._conn.execute("SELECT * FROM albums ORDER BY rank")
        return [dict(row) for row in cursor.fetchall()]

    def close(self) -> None:
        self._conn.close()