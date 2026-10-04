import sqlite3

CURRENT_VERSION = 2


def migrate(connection: sqlite3.Connection) -> None:
    version = connection.execute("PRAGMA user_version").fetchone()[0]

    if version < 1:
        _migrate_to_v1(connection)
        connection.execute("PRAGMA user_version = 1")

    if version < 2:
        _migrate_to_v2(connection)
        connection.execute("PRAGMA user_version = 2")

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
