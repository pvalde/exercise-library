import sqlite3
from datetime import UTC, datetime
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

    @staticmethod
    def _to_db_datetime(value: datetime) -> int:
        """
        Convert a timezone-aware datetime to Unix time in milliseconds.

        SQLite stores timestamps as INTEGER values representing the number of
        milliseconds since the Unix epoch (1970-01-01 00:00:00 UTC).
        """
        if value.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")

        return int(value.timestamp() * 1000)

    @staticmethod
    def _from_db_datetime(value: int) -> datetime:
        """
        Convert a Unix timestamp in milliseconds to a timezone-aware UTC datetime.

        The value is expected to represent the number of milliseconds since the
        Unix epoch (1970-01-01 00:00:00 UTC).
        """
        return datetime.fromtimestamp(value / 1000, tz=UTC)

    def add(self, exercise: Exercise) -> UUID:

        exercise_id = uuid7()

        try:
            self._connection.execute(
                """
                INSERT INTO exercises (id, identifier, prompt, answer, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(exercise_id),
                    exercise.identifier,
                    exercise.prompt,
                    exercise.answer,
                    self._to_db_datetime(datetime.now(tz=UTC)),
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
