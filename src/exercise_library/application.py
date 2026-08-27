import re
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from exercise_library.backup import BackupError, SQLiteBackupError, create_backup
from exercise_library.models import Exercise
from exercise_library.repository import DuplicateIdentifierError, ExerciseRepository

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_-]+(?:::[A-Za-z0-9_-]+)*$")


class ExerciseApplicationError(Exception):
    pass


class InvalidExerciseError(ExerciseApplicationError):
    pass


@dataclass
class ExerciseApplication:
    repository: ExerciseRepository

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

        if identifier is not None and not _IDENTIFIER_PATTERN.fullmatch(identifier):
            raise InvalidExerciseError(
                "Identifier can only contain letters, numbers, "
                "dash, underscore, and '::' separators."
            )

        exercise = Exercise(
            prompt=prompt,
            answer=answer,
            identifier=identifier,
        )

        try:
            exercise_id = self.repository.add(exercise)

        except DuplicateIdentifierError as error:
            raise InvalidExerciseError(
                f"Exercise identifier already exists: {identifier}."
            ) from error

        return exercise_id

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
