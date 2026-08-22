import sqlite3

from exercise_library.migrations import CURRENT_VERSION, migrate


def test_migrate_creates_schema() -> None:
    connection = sqlite3.connect(":memory:")

    migrate(connection)

    version = connection.execute("PRAGMA user_version").fetchone()[0]

    assert version == CURRENT_VERSION

    columns = connection.execute("PRAGMA table_info(exercises)").fetchall()

    assert [column[1] for column in columns] == [
        "id",
        "prompt",
        "answer",
    ]


def test_migrate_is_idempotent() -> None:
    connection = sqlite3.connect(":memory:")

    migrate(connection)
    migrate(connection)

    version = connection.execute("PRAGMA user_version").fetchone()[0]

    assert version == CURRENT_VERSION
