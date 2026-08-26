import re
from dataclasses import dataclass
from uuid import UUID

from exercise_library.models import Exercise
from exercise_library.repository import DuplicateIdentifierError, ExerciseRepository

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_-]+(?:::[A-Za-z0-9_-]+)*$")


@dataclass
class ExerciseApplication:
    repository: ExerciseRepository

    def add_exercise(
        self,
        prompt: str,
        answer: str,
        identifier: str | None = None,
    ) -> UUID:
        if not prompt:
            raise ValueError("Prompt and answer cannot be empty.")

        if not answer:
            raise ValueError("Prompt and answer cannot be empty.")

        if identifier is not None and not _IDENTIFIER_PATTERN.fullmatch(identifier):
            raise ValueError(
                "Identifier can only contain letters, numbers, "
                "dash, underscore, and '::' separators."
            )

        try:
            exercise = Exercise(
                prompt=prompt,
                answer=answer,
                identifier=identifier,
            )
        except DuplicateIdentifierError as e:
            raise ValueError("Identifier already exists") from e

        return self.repository.add(exercise)

    def browse_exercises(
        self,
        identifier: str | None = None,
    ) -> list[Exercise]:
        return self.repository.browse(identifier)
