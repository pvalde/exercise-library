import sqlite3

import pytest

from exercise_library.migrations import CURRENT_VERSION, migrate


def test_migrate_creates_schema() -> None:
    connection = sqlite3.connect(":memory:")

    migrate(connection)

    version = connection.execute("PRAGMA user_version").fetchone()[0]

    assert version == CURRENT_VERSION

    columns = connection.execute("PRAGMA table_info(exercises)").fetchall()

    assert [column[1] for column in columns] == [
        "uuid",
        "identifier",
        "prompt",
        "answer",
        "created_at",
        "updated_at",
    ]


def test_migrate_creates_media_table() -> None:
    connection = sqlite3.connect(":memory:")

    migrate(connection)

    columns = connection.execute("PRAGMA table_info(media)").fetchall()

    assert [column[1] for column in columns] == [
        "name",
        "media_type",
        "sha256",
        "size_bytes",
        "created_at",
    ]


def test_migrate_from_v1_adds_media_table() -> None:
    connection = sqlite3.connect(":memory:")

    migrate(connection)
    connection.execute("DROP TABLE media")
    connection.execute("DROP TABLE archived_review_stats")
    connection.execute("DROP INDEX idx_reviews_exercise_time")
    connection.execute("DROP TABLE reviews")
    connection.execute("PRAGMA user_version = 1")
    connection.commit()

    migrate(connection)

    version = connection.execute("PRAGMA user_version").fetchone()[0]

    assert version == CURRENT_VERSION

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }

    assert "media" in tables


def test_migrate_is_idempotent() -> None:
    connection = sqlite3.connect(":memory:")

    migrate(connection)
    migrate(connection)

    version = connection.execute("PRAGMA user_version").fetchone()[0]

    assert version == CURRENT_VERSION


def test_migrate_creates_reviews_tables() -> None:
    connection = sqlite3.connect(":memory:")

    migrate(connection)

    columns = connection.execute("PRAGMA table_info(reviews)").fetchall()

    assert [column[1] for column in columns] == [
        "uuid",
        "exercise_uuid",
        "reviewed_at",
        "rating",
    ]

    summary_columns = connection.execute(
        "PRAGMA table_info(archived_review_stats)"
    ).fetchall()

    assert [column[1] for column in summary_columns] == [
        "exercise_uuid",
        "total_reviews",
        "failures",
        "first_reviewed_at",
        "updated_at",
    ]


def test_migrate_from_v2_adds_review_tables() -> None:
    connection = sqlite3.connect(":memory:")

    migrate(connection)
    connection.execute("DROP TABLE archived_review_stats")
    connection.execute("DROP INDEX idx_reviews_exercise_time")
    connection.execute("DROP TABLE reviews")
    connection.execute("PRAGMA user_version = 2")
    connection.commit()

    migrate(connection)

    version = connection.execute("PRAGMA user_version").fetchone()[0]

    assert version == CURRENT_VERSION

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }

    assert "reviews" in tables
    assert "archived_review_stats" in tables

    indexes = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        ).fetchall()
    }

    assert "idx_reviews_exercise_time" in indexes


def test_reviews_rating_check_constraint() -> None:
    connection = sqlite3.connect(":memory:")

    migrate(connection)

    connection.execute(
        "INSERT INTO exercises"
        " (uuid, identifier, prompt, answer, created_at, updated_at)"
        " VALUES ('u1', NULL, 'p', 'a', 0, 0)"
    )

    connection.execute(
        "INSERT INTO reviews (uuid, exercise_uuid, reviewed_at, rating)"
        " VALUES ('r1', 'u1', 0, 2)"
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO reviews (uuid, exercise_uuid, reviewed_at, rating)"
            " VALUES ('r2', 'u1', 0, 4)"
        )
