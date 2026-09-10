from collections.abc import Callable

from exercise_library.application import ExerciseApplication

from .env_editor import edit_in_env_editor, inline_prompt
from .exceptions import CLIError


class AddInteractiveError(CLIError):
    pass


def _add_exercise_in_env_editor(
    application: ExerciseApplication,
    editor_launcher: Callable[[str, dict[str, str]], str | None],
    identifier_prompt: Callable[[str], str | None],
) -> None:
    exercise_identifier: str | None = identifier_prompt("Identifier (optional): ")

    if exercise_identifier:
        if not application.is_valid_identifier(exercise_identifier):
            raise AddInteractiveError(
                f"'{exercise_identifier}' is an invalid identifier."
                + "\nIt can only contain "
                + "letters, numbers, dash, underscore and '::' separators."
            )

        if application.identifier_exists(exercise_identifier):
            raise AddInteractiveError(f"'{exercise_identifier}' already exists.")

    exercise_prompt = editor_launcher(
        "prompt",
        {"identifier": exercise_identifier if exercise_identifier is not None else ""},
    )

    if exercise_prompt is None or not exercise_prompt.strip():
        raise AddInteractiveError("Prompt cannot be empty.")

    exercise_answer: str | None = editor_launcher(
        "answer",
        {
            "identifier": exercise_identifier
            if exercise_identifier is not None
            else "",
            "prompt": exercise_prompt,
        },
    )

    if exercise_answer is None or not exercise_answer.strip():
        raise AddInteractiveError("Answer cannot be empty.")

    application.add_exercise(
        prompt=exercise_prompt,
        answer=exercise_answer,
        identifier=exercise_identifier,
    )


def add_exercise_in_env_editor(application: ExerciseApplication) -> None:
    _add_exercise_in_env_editor(
        application=application,
        editor_launcher=edit_in_env_editor,
        identifier_prompt=inline_prompt,
    )


def add_exercise(
    application: ExerciseApplication,
    identifier: str | None,
    prompt: str,
    answer: str,
) -> None:

    application.add_exercise(
        prompt=prompt,
        answer=answer,
        identifier=identifier,
    )
