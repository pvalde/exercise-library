import argparse
import sys

from exercise_library.application import ExerciseApplication

from .editor import edit_in_editor


def add_exercise(
    application: ExerciseApplication,
    args: argparse.Namespace,
) -> None:
    if args.interactive:
        print("Opening editor for prompt...")
        prompt = edit_in_editor("prompt")

        print("Opening editor for answer...")
        answer = edit_in_editor("answer")

        identifier = args.identifier

        if identifier is None:
            identifier = input("Identifier (optional): ").strip() or None

    else:
        if not args.prompt or not args.answer:
            print(
                "Error: prompt and answer are required unless using --interactive (-i)."
            )
            sys.exit(1)

        prompt = args.prompt
        answer = args.answer
        identifier = args.identifier

    if not prompt or not answer:
        print("Error: Prompt and answer cannot be empty.")
        sys.exit(1)

    try:
        exercise_id = application.add_exercise(
            prompt=prompt,
            answer=answer,
            identifier=identifier,
        )
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    print(f"\nSuccessfully added exercise with ID {exercise_id}")
