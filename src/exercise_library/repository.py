import sqlite3

from exercise_library.models import Exercise


class RepositoryError(Exception):
    """Base exception for repository-layer failures."""


class RepositoryInsertError(RepositoryError):
    """Raised when an inserted record does not produce and ID"""


class DuplicateIdentifierError(RepositoryError):
    """Raised when an exercise identifier already exists."""


class ExerciseRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, exercise: Exercise) -> int:
        try:
            cursor = self._connection.execute(
                """
                INSERT INTO exercises (identifier, prompt, answer)
                VALUES (?, ?, ?)
                """,
                (exercise.identifier, exercise.prompt, exercise.answer),
            )
            self._connection.commit()
        except sqlite3.IntegrityError as error:
            if "UNIQUE constraint failed: exercises.identifier" in str(error):
                raise DuplicateIdentifierError(
                    f"Exercise identifier already exists: {exercise.identifier!r}"
                ) from error
            raise

        row_id = cursor.lastrowid
        if row_id is None:
            raise RepositoryInsertError(
                "Failed to retrieve ID of newly created exercise"
            )
        return row_id

    def list_all(self) -> list[Exercise]:
        cursor = self._connection.execute(
            """
            SELECT id, identifier, prompt, answer
            FROM exercises
            """
        )
        return [
            Exercise(
                id=row["id"],
                identifier=row["identifier"],
                prompt=row["prompt"],
                answer=row["answer"],
            )
            for row in cursor.fetchall()
        ]
