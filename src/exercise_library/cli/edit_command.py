from uuid import UUID

from exercise_library.application import ExerciseApplication
from exercise_library.models import Exercise

from .exceptions import CLIError


class EditError(CLIError):
    pass


def edit_exercise(
    application: ExerciseApplication,
    exercise_id: UUID | None = None,
    identifier: str | None = None,
    new_prompt: str | None = None,
    new_answer: str | None = None,
    new_identifier: str | None = None,
) -> None:

    if exercise_id is None and identifier is None:
        raise EditError("At least one of 'id' or 'identifier' must be provided.")

    if exercise_id:
        exercise = application.get_exercise_by_id(exercise_id)
    else:
        assert identifier is not None
        exercise = application.get_exercise_by_identifier(identifier)

    exercise = Exercise(
        id=exercise.id,
        identifier=exercise.identifier if new_identifier is None else new_identifier,
        prompt=exercise.prompt if new_prompt is None else new_prompt,
        answer=exercise.answer if new_answer is None else new_answer,
    )
    application.update_exercise(exercise)
