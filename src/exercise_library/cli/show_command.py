from uuid import UUID

from exercise_library.application import ExerciseApplication
from exercise_library.cli.exceptions import CLIError
from exercise_library.models import Exercise


class ShowError(CLIError):
    pass


def show_exercise(
    application: ExerciseApplication,
    id: UUID | None = None,
    identifier: str | None = None,
    show_prompt: bool = False,
    show_answer: bool = False,
) -> None:
    if id is None and identifier is None:
        raise ShowError("At least one of 'id' or 'identifier' must be provided.")

    exercise: Exercise

    if id:
        exercise = application.get_exercise_by_id(id)
    else:
        assert identifier is not None
        exercise = application.get_exercise_by_identifier(identifier)

    output = ""

    if exercise.identifier:
        output += f"Exercise: {exercise.identifier}\n\n"
    else:
        output += f"Exercise: {exercise.id}\n\n"

    if show_prompt:
        output += f"Prompt:\n{exercise.prompt}\n\n"

    if show_answer:
        output += f"Answer:\n{exercise.answer}\n"

    print(output)
