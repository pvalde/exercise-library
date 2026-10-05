import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from exercise_library.backup import BackupError, SQLiteBackupError, create_backup
from exercise_library.media import (
    hash_file,
    invalid_media_references,
    is_valid_media_name,
    media_type_for_name,
    referenced_media_names,
)
from exercise_library.models import Exercise, Media, ReviewRating
from exercise_library.paths import media_dir_path
from exercise_library.repository import (
    DuplicateIdentifierError,
    ExerciseRepository,
    InvalidExerciseValues,
    MediaRepository,
    ReviewRepository,
)
from exercise_library.repository import (
    DuplicateMediaError as RepositoryDuplicateMediaError,
)

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_-]+(?:::[A-Za-z0-9_-]+)*$")


class ExerciseApplicationError(Exception):
    pass


class InvalidExerciseError(ExerciseApplicationError):
    pass


class InvalidDepthError(ExerciseApplicationError):
    pass


class InvalidMediaError(ExerciseApplicationError):
    pass


class DuplicateMediaError(ExerciseApplicationError):
    pass


class InvalidReviewRatingError(ExerciseApplicationError):
    pass


INVALID_IDENTIFIER_MSG = (
    "Identifier can only contain letters, numbers, "
    + "dash, underscore, and '::' separators."
)


def invalid_identifier_msg(identifier: str) -> str:
    return (
        f"'{identifier}' is an invalid identifier.\nIt can only contain "
        + "letters, numbers, dash, underscore and '::' separators."
    )


def invalid_media_name_msg(name: str) -> str:
    return (
        f"'{name}' is an invalid media file name.\nIt can only contain "
        + "letters, numbers, dot, dash and underscore, and must start "
        + "with a letter or number."
    )


def unsupported_media_type_msg(name: str) -> str:
    return f"'{name}' is not a supported media type."


def duplicate_media_name_msg(name: str) -> str:
    return (
        f"A different media file is already stored as '{name}'.\n"
        + "Rename the file and try again."
    )


def missing_media_msg(names: list[str]) -> str:
    return "Referenced media not found: " + ", ".join(names) + "."


def invalid_media_reference_msg(destinations: list[str]) -> str:
    return (
        "Invalid media references: "
        + ", ".join(destinations)
        + ".\nOnly stored media can be referenced, by file name, "
        + "e.g. 'diagram.png'."
    )


@dataclass
class IdentifierPrefix:
    prefix: str
    exercise_count: int


@dataclass(frozen=True)
class ReviewExerciseStats:
    exercise_uuid: UUID
    total_reviews: int
    failures: int
    last_reviewed_at: datetime | None


@dataclass
class ExerciseApplication:
    repository: ExerciseRepository
    media_repository: MediaRepository
    review_repository: ReviewRepository

    def _is_valid_identifier(self, identifier: str) -> bool:
        return bool(_IDENTIFIER_PATTERN.fullmatch(identifier))

    def _check_media_references(self, *texts: str) -> None:
        invalid: set[str] = set()
        missing: set[str] = set()

        for text in texts:
            invalid.update(invalid_media_references(text))

            for name in referenced_media_names(text):
                if not self.media_repository.exists(name):
                    missing.add(name)

        if invalid:
            raise InvalidMediaError(invalid_media_reference_msg(sorted(invalid)))

        if missing:
            raise InvalidMediaError(missing_media_msg(sorted(missing)))

    def add_exercise(
        self,
        prompt: str,
        answer: str,
        identifier: str | None = None,
    ) -> UUID:
        if not prompt.strip() and not answer.strip():
            raise InvalidExerciseError("Prompt and answer cannot be empty.")

        if not prompt.strip():
            raise InvalidExerciseError("Prompt cannot be empty.")

        if not answer.strip():
            raise InvalidExerciseError("Answer cannot be empty.")

        if identifier is not None and not self._is_valid_identifier(identifier):
            raise InvalidExerciseError(invalid_identifier_msg(identifier))

        self._check_media_references(prompt, answer)

        exercise = Exercise(
            prompt=prompt,
            answer=answer,
            identifier=identifier,
        )

        try:
            exercise_uuid = self.repository.add(exercise)

        except DuplicateIdentifierError as error:
            raise InvalidExerciseError(
                f"Exercise identifier already exists: {identifier}."
            ) from error

        return exercise_uuid

    def browse_exercises(
        self,
        identifier: str | None = None,
    ) -> list[Exercise]:
        return self.repository.browse(identifier)

    def backup_data(
        self,
        backup_file_path: Path | None = None,
    ) -> Path:
        try:
            return create_backup(backup_file_path)
        except SQLiteBackupError as exc:
            raise ExerciseApplicationError(
                "Could not create the backup. ",
                "Make sure the database is accessible and try again.",
            ) from exc
        except BackupError as exc:
            raise ExerciseApplicationError(str(exc)) from exc

    def update_exercise(self, exercise: Exercise) -> UUID:
        if exercise.identifier and not self._is_valid_identifier(exercise.identifier):
            raise InvalidExerciseError(invalid_identifier_msg(exercise.identifier))

        self._check_media_references(exercise.prompt, exercise.answer)

        try:
            exercise_uuid = self.repository.update(exercise)
        except InvalidExerciseValues as exc:
            raise InvalidExerciseError(
                f"No exercise found with uuid {str(exercise.uuid)}"
            ) from exc
        except DuplicateIdentifierError as exc:
            raise InvalidExerciseError(
                f"Exercise identifier already exists: {exercise.identifier}"
            ) from exc

        return exercise_uuid

    def get_exercise_by_uuid(self, uuid: UUID) -> Exercise:
        try:
            return self.repository.get_by_uuid(uuid)
        except InvalidExerciseValues as exc:
            raise InvalidExerciseError(str(exc)) from exc

    def get_exercise_by_identifier(self, identifier: str) -> Exercise:
        if not self._is_valid_identifier(identifier):
            raise InvalidExerciseError(invalid_identifier_msg(identifier))
        try:
            return self.repository.get_by_identifier(identifier)
        except InvalidExerciseValues as exc:
            raise InvalidExerciseError(str(exc)) from exc

    def is_valid_identifier(self, identifier: str) -> bool:
        return self._is_valid_identifier(identifier)

    def identifier_exists(self, identifier: str) -> bool:
        return self.repository.identifier_exists(identifier)

    def list_identifier_prefixes(
        self,
        identifier: str | None = None,
        depth: int | None = None,
    ) -> list[IdentifierPrefix]:
        if identifier is not None and not self._is_valid_identifier(identifier):
            raise InvalidExerciseError(invalid_identifier_msg(identifier))

        if depth is not None and depth < 1:
            raise InvalidDepthError("Depth must be a positive integer.")

        exercises = [
            exercise
            for exercise in self.repository.browse(identifier)
            if exercise.identifier is not None
        ]

        prefixes: set[str] = set()

        for exercise in exercises:
            assert exercise.identifier is not None
            parts = exercise.identifier.split("::")
            if depth is not None:
                parts = parts[:depth]
            prefixes.add("::".join(parts))

        id_prefixes: list[IdentifierPrefix] = list()
        for prefix in sorted(prefixes):
            count = 0

            for exercise in exercises:
                assert exercise.identifier is not None
                if exercise.identifier == prefix or exercise.identifier.startswith(
                    f"{prefix}::"
                ):
                    count += 1

            id_prefixes.append(
                IdentifierPrefix(
                    prefix=prefix,
                    exercise_count=count,
                )
            )

        return id_prefixes

    def add_media(self, source: Path) -> str:
        name = source.name

        if not is_valid_media_name(name):
            raise InvalidMediaError(invalid_media_name_msg(name))

        media_type = media_type_for_name(name)
        if media_type is None:
            raise InvalidMediaError(unsupported_media_type_msg(name))

        if not source.is_file():
            raise InvalidMediaError(f"Media file does not exist: {source}")

        digest = hash_file(source)

        existing = self.media_repository.get(name)
        if existing is not None:
            if existing.sha256 == digest:
                return name
            raise DuplicateMediaError(duplicate_media_name_msg(name))

        destination = media_dir_path() / name
        same_file = source.resolve() == destination.resolve()

        if not same_file:
            try:
                shutil.copy2(source, destination)
            except OSError as exc:
                raise InvalidMediaError(f"Could not store media file: {name}") from exc

        try:
            self.media_repository.add(
                Media(
                    name=name,
                    media_type=media_type,
                    sha256=digest,
                    size_bytes=source.stat().st_size,
                )
            )
        except RepositoryDuplicateMediaError as exc:
            if not same_file:
                destination.unlink(missing_ok=True)
            raise DuplicateMediaError(duplicate_media_name_msg(name)) from exc

        return name

    def media_exists(self, name: str) -> bool:
        return self.media_repository.exists(name)

    def list_media(self) -> list[Media]:
        return self.media_repository.list_all()

    def _resolve_exercise(self, identifier_or_uuid: str | UUID) -> Exercise:
        if isinstance(identifier_or_uuid, UUID):
            return self.get_exercise_by_uuid(identifier_or_uuid)
        return self.get_exercise_by_identifier(identifier_or_uuid)

    @staticmethod
    def _parse_rating(rating: ReviewRating | str) -> ReviewRating:
        if isinstance(rating, ReviewRating):
            return rating
        try:
            return ReviewRating[rating.strip().upper()]
        except KeyError as exc:
            valid = ", ".join(r.name.lower() for r in ReviewRating)
            raise InvalidReviewRatingError(
                f"Invalid rating: {rating!r}. Valid values: {valid}."
            ) from exc

    def record_review(
        self,
        identifier_or_uuid: str | UUID,
        rating: ReviewRating | str,
    ) -> UUID:
        exercise = self._resolve_exercise(identifier_or_uuid)
        parsed_rating = self._parse_rating(rating)
        assert exercise.uuid is not None
        return self.review_repository.add(exercise.uuid, parsed_rating)

    def review_stats(self, identifier_or_uuid: str | UUID) -> ReviewExerciseStats:
        exercise = self._resolve_exercise(identifier_or_uuid)
        assert exercise.uuid is not None

        archived = self.review_repository.get_archived_stats(exercise.uuid)
        window = self.review_repository.list_by_exercise(exercise.uuid)

        window_failures = sum(1 for review in window if review.rating.is_failure)
        last_reviewed_at = max((r.reviewed_at for r in window), default=None)

        return ReviewExerciseStats(
            exercise_uuid=exercise.uuid,
            total_reviews=(archived.total_reviews if archived else 0) + len(window),
            failures=(archived.failures if archived else 0) + window_failures,
            last_reviewed_at=last_reviewed_at,
        )
