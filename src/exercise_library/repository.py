import sqlite3

from exercise_library.models import Exercise


class RepositoryError(Exception):
    """Base exception for repository-layer failures."""


class RepositoryInsertError(RepositoryError):
    """Raised when an inserted record does not produce and ID"""


class ExerciseRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, exercise: Exercise) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO exercises (prompt, answer)
            VALUES (?, ?)
            """,
            (exercise.prompt, exercise.answer),
        )
        self._connection.commit()

        row_id = cursor.lastrowid
        if row_id is None:
            raise RepositoryInsertError("Failed to retrieve ID of newly created user")
        return row_id

    def list_all(self) -> list[Exercise]:
        cursor = self._connection.execute(
            """
            SELECT id, prompt, answer
            FROM exercises
            """
        )
        return [
            Exercise(
                id=row["id"],
                prompt=row["prompt"],
                answer=row["answer"],
            )
            for row in cursor.fetchall()
        ]
