import re
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from exercise_library.backup import BackupError, SQLiteBackupError, create_backup
from exercise_library.models import Exercise
from exercise_library.repository import (
    DuplicateIdentifierError,
    ExerciseRepository,
    InvalidExerciseValues,
)

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_-]+(?:::[A-Za-z0-9_-]+)*$")


class ExerciseApplicationError(Exception):
    pass


class InvalidExerciseError(ExerciseApplicationError):
    pass


class InvalidDepthError(ExerciseApplicationError):
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


@dataclass
class IdentifierPrefix:
    prefix: str
    exercise_count: int


@dataclass
class ExerciseApplication:
    repository: ExerciseRepository

    def _is_valid_identifier(self, identifier: str) -> bool:
        return bool(_IDENTIFIER_PATTERN.fullmatch(identifier))

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
