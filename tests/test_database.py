import sqlite3
from pathlib import Path

import pytest

from exercise_library.config import APP_NAME, DATABASE_NAME
from exercise_library.database import connect, database_path, initialize


def test_database_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    assert database_path() == tmp_path / APP_NAME / DATABASE_NAME


def test_connect(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:

    connection = connect()

    try:
        assert isinstance(connection, sqlite3.Connection)
        assert database_path().is_file()

    finally:
        connection.close()


def test_initialize(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:

    connection = initialize()

    try:
        assert connection.execute("SELECT 1 FROM exercises LIMIT 1").fetchone() is None

    finally:
        connection.close()
