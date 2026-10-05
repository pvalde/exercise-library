import sqlite3
from datetime import UTC, datetime
from uuid import UUID, uuid7

from exercise_library.locking import application_lock
from exercise_library.models import (
    ArchivedReviewStats,
    Exercise,
    Media,
    Review,
    ReviewRating,
)

RETAINED_REVIEWS_PER_EXERCISE = 25


class RepositoryError(Exception):
    """Base exception for repository-layer failures."""


class RepositoryInsertError(RepositoryError):
    """Raised when an inserted record does not produce and ID"""


class DuplicateIdentifierError(RepositoryError):
    """Raised when an exercise identifier already exists."""


class DuplicateMediaError(RepositoryError):
    """Raised when a media name already exists."""


class InvalidExerciseValues(RepositoryError):
    """Raises when some provided exercise's value is invalid."""


def _now_unix_millis() -> int:
    return int(datetime.now(tz=UTC).timestamp() * 1000)


def _to_db_datetime(value: datetime) -> int:
    """
    Convert a timezone-aware datetime to Unix time in milliseconds.

    SQLite stores timestamps as INTEGER values representing the number of
    milliseconds since the Unix epoch (1970-01-01 00:00:00 UTC).
    """
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")

    return int(value.timestamp() * 1000)


def _from_db_datetime(value: int) -> datetime:
    """
    Convert a Unix timestamp in milliseconds to a timezone-aware UTC
    datetime.

    The value is expected to represent the number of milliseconds since the
    Unix epoch (1970-01-01 00:00:00 UTC).
    """
    return datetime.fromtimestamp(value / 1000, tz=UTC)


class ExerciseRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, exercise: Exercise) -> UUID:
        with application_lock():
            exercise_uuid = uuid7()

            try:
                current_time = datetime.now(tz=UTC)
                self._connection.execute(
                    """
                    INSERT INTO exercises
                    (uuid, identifier, prompt, answer, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                        """,
                    (
                        str(exercise_uuid),
                        exercise.identifier,
                        exercise.prompt,
                        exercise.answer,
                        _to_db_datetime(current_time),
                        _to_db_datetime(current_time),
                    ),
                )
                self._connection.commit()
            except sqlite3.IntegrityError as error:
                if "UNIQUE constraint failed: exercises.identifier" in str(error):
                    raise DuplicateIdentifierError(
                        f"Exercise identifier already exists: {exercise.identifier!r}"
                    ) from error
                raise

            return exercise_uuid

    def update(self, exercise: Exercise) -> UUID:
        if not exercise.uuid:
            raise InvalidExerciseValues("Exercise UUID has not been provided.")

        with application_lock():
            row = self._connection.execute(
                "SELECT 1 FROM exercises WHERE uuid = ?;",
                (str(exercise.uuid),),
            ).fetchone()

            if row is None:
                raise InvalidExerciseValues(
                    f"No exercise found with uuid {str(exercise.uuid)}",
                )

            try:
                self._connection.execute(
                    """
                    UPDATE exercises
                    SET identifier  = ?,
                        prompt      = ?,
                        answer      = ?,
                        updated_at = ?
                    WHERE uuid = ?;
                    """,
                    (
                        exercise.identifier,
                        exercise.prompt,
                        exercise.answer,
                        _to_db_datetime(datetime.now(tz=UTC)),
                        str(exercise.uuid),
                    ),
                )
                self._connection.commit()
            except sqlite3.IntegrityError as error:
                if "UNIQUE constraint failed: exercises.identifier" in str(error):
                    raise DuplicateIdentifierError(
                        f"Exercise identifier already exists: {exercise.identifier!r}"
                    ) from error
                raise
            return exercise.uuid

    def list_all(self) -> list[Exercise]:
        cursor = self._connection.execute(
            """
            SELECT uuid, identifier, prompt, answer
            FROM exercises
            """
        )
        return [
            Exercise(
                uuid=UUID(row["uuid"]),
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
                SELECT uuid, identifier, prompt, answer
                FROM exercises
                ORDER BY uuid
                """
            )

        else:
            cursor = self._connection.execute(
                """
                SELECT uuid, identifier, prompt, answer
                FROM exercises
                WHERE identifier = ?
                   OR identifier LIKE ? || '::%'
                ORDER BY uuid
                """,
                (identifier, identifier),
            )

        return [
            Exercise(
                uuid=UUID(row["uuid"]),
                identifier=row["identifier"],
                prompt=row["prompt"],
                answer=row["answer"],
            )
            for row in cursor.fetchall()
        ]

    def get_by_identifier(self, identifier: str) -> Exercise:
        cursor = self._connection.execute(
            """
            SELECT uuid, identifier, prompt, answer
            FROM exercises
            WHERE identifier = ?;
            """,
            (identifier,),
        )

        row = cursor.fetchone()

        if row is None:
            raise InvalidExerciseValues(f"Exercise not found: {identifier}")
        return Exercise(
            uuid=UUID(row["uuid"]),
            identifier=row["identifier"],
            prompt=row["prompt"],
            answer=row["answer"],
        )

    def get_by_uuid(self, uuid: UUID) -> Exercise:
        cursor = self._connection.execute(
            """
            SELECT uuid, identifier, prompt, answer
            FROM exercises
            WHERE uuid = ?;
            """,
            (str(uuid),),
        )

        row = cursor.fetchone()

        if row is None:
            raise InvalidExerciseValues(f"Exercise not found: {str(uuid)}.")

        return Exercise(
            uuid=UUID(row["uuid"]),
            identifier=row["identifier"],
            prompt=row["prompt"],
            answer=row["answer"],
        )

    def identifier_exists(self, identifier: str) -> bool:
        cursor = self._connection.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM exercises
                WHERE identifier = ?
            )
            """,
            (identifier,),
        )

        row = cursor.fetchone()

        return bool(row[0])


class MediaRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, media: Media) -> None:
        with application_lock():
            try:
                self._connection.execute(
                    """
                    INSERT INTO media
                    (name, media_type, sha256, size_bytes, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        media.name,
                        media.media_type,
                        media.sha256,
                        media.size_bytes,
                        _now_unix_millis(),
                    ),
                )
                self._connection.commit()
            except sqlite3.IntegrityError as error:
                if "UNIQUE constraint failed: media.name" in str(error):
                    raise DuplicateMediaError(
                        f"Media name already exists: {media.name!r}"
                    ) from error
                raise

    def get(self, name: str) -> Media | None:
        cursor = self._connection.execute(
            """
            SELECT name, media_type, sha256, size_bytes
            FROM media
            WHERE name = ?;
            """,
            (name,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return Media(
            name=row["name"],
            media_type=row["media_type"],
            sha256=row["sha256"],
            size_bytes=row["size_bytes"],
        )

    def exists(self, name: str) -> bool:
        cursor = self._connection.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM media
                WHERE name = ?
            )
            """,
            (name,),
        )

        row = cursor.fetchone()

        return bool(row[0])

    def list_all(self) -> list[Media]:
        cursor = self._connection.execute(
            """
            SELECT name, media_type, sha256, size_bytes
            FROM media
            ORDER BY name;
            """
        )

        return [
            Media(
                name=row["name"],
                media_type=row["media_type"],
                sha256=row["sha256"],
                size_bytes=row["size_bytes"],
            )
            for row in cursor.fetchall()
        ]


class ReviewRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _row_to_review(row: sqlite3.Row) -> Review:
        return Review(
            uuid=UUID(row["uuid"]),
            exercise_uuid=UUID(row["exercise_uuid"]),
            reviewed_at=_from_db_datetime(row["reviewed_at"]),
            rating=ReviewRating(row["rating"]),
        )

    def add(
        self,
        exercise_uuid: UUID,
        rating: ReviewRating,
        reviewed_at: datetime | None = None,
    ) -> UUID:
        if reviewed_at is None:
            reviewed_at = datetime.now(tz=UTC)
        elif reviewed_at.tzinfo is None:
            raise ValueError("reviewed_at must be timezone-aware")

        with application_lock():
            review_uuid = uuid7()
            self._connection.execute(
                """
                INSERT INTO reviews (uuid, exercise_uuid, reviewed_at, rating)
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(review_uuid),
                    str(exercise_uuid),
                    _to_db_datetime(reviewed_at),
                    int(rating),
                ),
            )
            self._enforce_retention(exercise_uuid)
            self._connection.commit()

        return review_uuid

    def _enforce_retention(self, exercise_uuid: UUID) -> None:
        rows = self._connection.execute(
            """
            SELECT uuid, reviewed_at, rating
            FROM reviews
            WHERE exercise_uuid = ?
            ORDER BY reviewed_at ASC, uuid ASC
            """,
            (str(exercise_uuid),),
        ).fetchall()

        overflow = len(rows) - RETAINED_REVIEWS_PER_EXERCISE
        if overflow <= 0:
            return

        to_fold = rows[:overflow]
        fold_failures = sum(
            1 for row in to_fold if ReviewRating(row["rating"]).is_failure
        )
        fold_oldest = _from_db_datetime(to_fold[0]["reviewed_at"])

        existing = self._connection.execute(
            """
            SELECT total_reviews, failures, first_reviewed_at
            FROM archived_review_stats
            WHERE exercise_uuid = ?
            """,
            (str(exercise_uuid),),
        ).fetchone()

        now_millis = _now_unix_millis()

        if existing is None:
            self._connection.execute(
                """
                INSERT INTO archived_review_stats
                (exercise_uuid, total_reviews, failures, first_reviewed_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(exercise_uuid),
                    len(to_fold),
                    fold_failures,
                    _to_db_datetime(fold_oldest),
                    now_millis,
                ),
            )
        else:
            existing_first = existing["first_reviewed_at"]
            first_reviewed_at = (
                min(existing_first, _to_db_datetime(fold_oldest))
                if existing_first is not None
                else _to_db_datetime(fold_oldest)
            )
            self._connection.execute(
                """
                UPDATE archived_review_stats
                SET total_reviews = total_reviews + ?,
                    failures = failures + ?,
                    first_reviewed_at = ?,
                    updated_at = ?
                WHERE exercise_uuid = ?
                """,
                (
                    len(to_fold),
                    fold_failures,
                    first_reviewed_at,
                    now_millis,
                    str(exercise_uuid),
                ),
            )

        placeholders = ",".join("?" for _ in to_fold)
        self._connection.execute(
            f"DELETE FROM reviews WHERE uuid IN ({placeholders})",
            tuple(row["uuid"] for row in to_fold),
        )

    def list_by_exercise(self, exercise_uuid: UUID) -> list[Review]:
        cursor = self._connection.execute(
            """
            SELECT uuid, exercise_uuid, reviewed_at, rating
            FROM reviews
            WHERE exercise_uuid = ?
            ORDER BY reviewed_at, uuid
            """,
            (str(exercise_uuid),),
        )
        return [self._row_to_review(row) for row in cursor.fetchall()]

    def get_archived_stats(self, exercise_uuid: UUID) -> ArchivedReviewStats | None:
        row = self._connection.execute(
            """
            SELECT exercise_uuid, total_reviews, failures, first_reviewed_at, updated_at
            FROM archived_review_stats
            WHERE exercise_uuid = ?
            """,
            (str(exercise_uuid),),
        ).fetchone()

        if row is None:
            return None

        return ArchivedReviewStats(
            exercise_uuid=UUID(row["exercise_uuid"]),
            total_reviews=row["total_reviews"],
            failures=row["failures"],
            updated_at=_from_db_datetime(row["updated_at"]),
            first_reviewed_at=(
                _from_db_datetime(row["first_reviewed_at"])
                if row["first_reviewed_at"] is not None
                else None
            ),
        )

    def latest_per_exercise(self) -> dict[UUID, Review]:
        cursor = self._connection.execute(
            """
            SELECT r.uuid, r.exercise_uuid, r.reviewed_at, r.rating
            FROM reviews r
            JOIN (
                SELECT exercise_uuid, MAX(reviewed_at) AS max_reviewed_at
                FROM reviews
                GROUP BY exercise_uuid
            ) latest
              ON r.exercise_uuid = latest.exercise_uuid
             AND r.reviewed_at = latest.max_reviewed_at
            """
        )
        return {
            UUID(row["exercise_uuid"]): self._row_to_review(row)
            for row in cursor.fetchall()
        }
