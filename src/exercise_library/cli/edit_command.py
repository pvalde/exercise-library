from collections.abc import Callable
from uuid import UUID

from prompt_toolkit import prompt as tk_prompt

from exercise_library.application import ExerciseApplication
from exercise_library.models import Exercise

from .env_editor import edit_in_env_editor
from .exceptions import CLIError


class EditError(CLIError):
    pass


def _get_exercise(
    application: ExerciseApplication,
    exercise_id: UUID | None = None,
    identifier: str | None = None,
) -> Exercise:
    if exercise_id is None and identifier is None:
        raise EditError("At least one of 'id' or 'identifier' must be provided.")

    if exercise_id:
        exercise = application.get_exercise_by_id(exercise_id)
    else:
        assert identifier is not None
        exercise = application.get_exercise_by_identifier(identifier)

    return exercise


def _identifier_prompt(identifier: str | None) -> str | None:
    msg = "Identifier (optional): "
    answer = (
        tk_prompt(
            msg,
            default=identifier,
        )
        if identifier
        else tk_prompt(msg)
    )

    return answer.strip() if answer.strip() != "" else None


def edit_exercise(
    application: ExerciseApplication,
    exercise_id: UUID | None = None,
    identifier: str | None = None,
    new_prompt: str | None = None,
    new_answer: str | None = None,
    new_identifier: str | None = None,
) -> None:

    exercise = _get_exercise(application, exercise_id, identifier)

    exercise = Exercise(
        id=exercise.id,
        identifier=exercise.identifier if new_identifier is None else new_identifier,
        prompt=exercise.prompt if new_prompt is None else new_prompt,
        answer=exercise.answer if new_answer is None else new_answer,
    )
    application.update_exercise(exercise)


def _edit_exercise_env_editor(
    application: ExerciseApplication,
    identifier_prompt: Callable[[str | None], str | None],
    editor_launcher: Callable[[str, dict[str, str], str | None], str | None],
    exercise_id: UUID | None = None,
    identifier: str | None = None,
) -> None:
    exercise = _get_exercise(application, exercise_id, identifier)

    new_identifier: str | None = identifier_prompt(exercise.identifier)

    new_exercise_prompt: str | None = editor_launcher(
        "prompt",
        {"identifier": new_identifier if new_identifier else ""},
        exercise.prompt,
    )

    new_exercise_answer: str | None = editor_launcher(
        "answer",
        {
            "identifier": new_identifier if new_identifier else "",
            "prompt": new_exercise_prompt if new_exercise_prompt else "",
        },
        exercise.answer,
    )

    updated_exercise = Exercise(
        id=exercise.id,
        identifier=new_identifier if new_identifier else exercise.identifier,
        prompt=new_exercise_prompt if new_exercise_prompt else exercise.prompt,
        answer=new_exercise_answer if new_exercise_answer else exercise.answer,
    )

    application.update_exercise(updated_exercise)


def edit_exercise_env_editor(
    application: ExerciseApplication,
    exercise_id: UUID | None = None,
    identifier: str | None = None,
) -> None:

    return _edit_exercise_env_editor(
        application=application,
        identifier_prompt=_identifier_prompt,
        editor_launcher=edit_in_env_editor,
        exercise_id=exercise_id,
        identifier=identifier,
    )
