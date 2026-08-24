import sqlite3

CURRENT_VERSION = 1


def migrate(connection: sqlite3.Connection) -> None:
    version = connection.execute("PRAGMA user_version").fetchone()[0]

    if version < 1:
        _migrate_to_v1(connection)
        connection.execute("PRAGMA user_version = 1")

    connection.commit()


def _migrate_to_v1(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE exercises (
            id TEXT PRIMARY KEY NOT NULL,
            identifier TEXT UNIQUE,
            prompt TEXT NOT NULL,
            answer TEXT NOT NULL
        )
        """
    )
