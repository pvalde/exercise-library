import argparse
from collections.abc import Callable

from exercise_library.application import ExerciseApplication

from .env_editor import edit_in_env_editor, inline_prompt
from .exceptions import CLIError


class AddInteractiveError(CLIError):
    pass


def _add_exercise(
    application: ExerciseApplication,
    args: argparse.Namespace,
    editor: Callable[[str, dict[str, str]], str | None],
    identifier_prompt: Callable[[str], str | None],
) -> None:
    if args.interactive:
        exercise_identifier = args.identifier
        if exercise_identifier is None:
            exercise_identifier = identifier_prompt("Identifier (optional): ")

        exercise_prompt = editor("prompt", {"identifier": exercise_identifier})

        if exercise_prompt is None or not exercise_prompt.strip():
            raise AddInteractiveError("Prompt cannot be empty.")

        exercise_answer = editor(
            "answer", {"identifier": exercise_identifier, "prompt": exercise_prompt}
        )

        if exercise_answer is None or not exercise_answer.strip():
            raise AddInteractiveError("Answer cannot be empty.")

    else:
        exercise_prompt = "" if args.prompt is None else args.prompt
        exercise_answer = "" if args.answer is None else args.answer
        exercise_identifier = args.identifier

    application.add_exercise(
        prompt=exercise_prompt,
        answer=exercise_answer,
        identifier=exercise_identifier,
    )


def add_exercise(
    application: ExerciseApplication,
    args: argparse.Namespace,
) -> None:
    return _add_exercise(
        application,
        args,
        edit_in_env_editor,
        inline_prompt,
    )
