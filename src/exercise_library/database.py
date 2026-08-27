import sqlite3
from pathlib import Path

from exercise_library.config import DATABASE_NAME
from exercise_library.migrations import migrate
from exercise_library.paths import app_data_dir_path


def database_path() -> Path:
    return app_data_dir_path() / DATABASE_NAME


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(database_path())
    connection.row_factory = sqlite3.Row
    return connection


def initialize() -> sqlite3.Connection:
    connection = connect()
    migrate(connection)
    return connection
