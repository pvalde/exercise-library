import sqlite3
from uuid import UUID, uuid7

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

    def add(self, exercise: Exercise) -> UUID:

        exercise_id = uuid7()

        try:
            self._connection.execute(
                """
                INSERT INTO exercises (id, identifier, prompt, answer)
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(exercise_id),
                    exercise.identifier,
                    exercise.prompt,
                    exercise.answer,
                ),
            )
            self._connection.commit()
        except sqlite3.IntegrityError as error:
            if "UNIQUE constraint failed: exercises.identifier" in str(error):
                raise DuplicateIdentifierError(
                    f"Exercise identifier already exists: {exercise.identifier!r}"
                ) from error
            raise

        return exercise_id

    def list_all(self) -> list[Exercise]:
        cursor = self._connection.execute(
            """
            SELECT id, identifier, prompt, answer
            FROM exercises
            """
        )
        return [
            Exercise(
                id=UUID(row["id"]),
                identifier=row["identifier"],
                prompt=row["prompt"],
                answer=row["answer"],
            )
            for row in cursor.fetchall()
        ]

    def browse(self, identifier: str | None = None) -> list[Exercise]:
        if identifier is None:
            cursor = self._connection.execute(
                """
                SELECT id, identifier, prompt, answer
                FROM exercises
                ORDER BY id
                """
            )

        else:
            cursor = self._connection.execute(
                """
                SELECT id, identifier, prompt, answer
                FROM exercises
                WHERE identifier = ?
                   OR identifier LIKE ? || '::%'
                ORDER BY id
                """,
                (identifier, identifier),
            )

        return [
            Exercise(
                id=UUID(row["id"]),
                identifier=row["identifier"],
                prompt=row["prompt"],
                answer=row["answer"],
            )
            for row in cursor.fetchall()
        ]
