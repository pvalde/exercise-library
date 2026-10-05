import sqlite3

CURRENT_VERSION = 3


def migrate(connection: sqlite3.Connection) -> None:
    version = connection.execute("PRAGMA user_version").fetchone()[0]

    if version < 1:
        _migrate_to_v1(connection)
        connection.execute("PRAGMA user_version = 1")

    if version < 2:
        _migrate_to_v2(connection)
        connection.execute("PRAGMA user_version = 2")

    if version < 3:
        _migrate_to_v3(connection)
        connection.execute("PRAGMA user_version = 3")

    connection.commit()


def _migrate_to_v1(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE exercises (
            uuid TEXT PRIMARY KEY NOT NULL,
            identifier TEXT UNIQUE,
            prompt TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at INT NOT NULL,
            updated_at INT NOT NULL
        )
        """
    )


def _migrate_to_v2(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE media (
            name TEXT PRIMARY KEY NOT NULL,
            media_type TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        )
        """
    )


def _migrate_to_v3(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE reviews (
            uuid TEXT PRIMARY KEY NOT NULL,
            exercise_uuid TEXT NOT NULL REFERENCES exercises(uuid),
            reviewed_at INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating IN (0, 1, 2, 3))
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX idx_reviews_exercise_time
        ON reviews (exercise_uuid, reviewed_at)
        """
    )
    connection.execute(
        """
        CREATE TABLE archived_review_stats (
            exercise_uuid TEXT PRIMARY KEY REFERENCES exercises(uuid),
            total_reviews INTEGER NOT NULL DEFAULT 0,
            failures INTEGER NOT NULL DEFAULT 0,
            first_reviewed_at INTEGER,
            updated_at INTEGER NOT NULL
        )
        """
    )
