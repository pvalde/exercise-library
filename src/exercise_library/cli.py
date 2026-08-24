import argparse
import os
import shlex
import subprocess
import sys
import tempfile

import shtab

from exercise_library.application import ExerciseApplication
from exercise_library.config import APP_NAME
from exercise_library.database import initialize
from exercise_library.repository import ExerciseRepository


def edit_in_editor(field_name: str) -> str:
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if not editor:
        print("Error: Neither $VISUAL nor $EDITOR environment variable is set.")
        sys.exit(1)

    initial_content = (
        f"<!-- [{APP_NAME}]: Enter the exercise {field_name}"
        + " below using Markdown. -->\n"
        f"<!-- [{APP_NAME}]: This comment will be automatically removed. -->\n\n"
    )

    with tempfile.NamedTemporaryFile(
        mode="w+",
        suffix=".md",
        delete=False,
        encoding="utf-8",
    ) as tf:
        tf.write(initial_content)
        tf_name = tf.name

    try:
        subprocess.run(shlex.split(editor) + [tf_name], check=True)

        with open(tf_name, encoding="utf-8") as tf:
            content = tf.read()

        if content == initial_content:
            return ""

        lines = content.splitlines(keepends=True)

        # Filter out generated HTML comment lines.
        content = "".join(
            line for line in lines if not line.strip().startswith(f"<!-- [{APP_NAME}]:")
        ).strip()

        return content

    except subprocess.CalledProcessError:
        print("Error: Editor exited with a non-zero status.")
        return ""

    finally:
        if os.path.exists(tf_name):
            os.unlink(tf_name)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage your exercise library.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    add_parser = subparsers.add_parser(
        "add",
        help="Add a new exercise",
    )

    add_parser.add_argument(
        "prompt",
        nargs="?",
        help="The exercise prompt",
    )

    add_parser.add_argument(
        "answer",
        nargs="?",
        help="The exercise answer",
    )

    add_parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Open markdown editor for prompt and answer",
    )

    add_parser.add_argument(
        "-I",
        "--identifier",
        help="Optional identifier for the exercise",
    )

    browse_parser = subparsers.add_parser(
        "browse",
        help="List all exercises",
    )

    browse_parser.add_argument(
        "-I",
        "--identifier",
        help="Browse exercises under this identifier prefix",
    )

    shtab.add_argument_to(parser)

    return parser


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


def browse_exercises(
    application: ExerciseApplication,
    identifier: str | None,
) -> None:
    exercises = application.browse_exercises(identifier)

    if not exercises:
        print("No exercises found.")
        return

    for exercise in exercises:
        print(f"\n[{exercise.id}]")

        if exercise.identifier:
            print(f"Identifier: {exercise.identifier}")

        print(f"Prompt:\n{exercise.prompt}")
        print(f"Answer:\n{exercise.answer}")
        print("-" * 40)


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    connection = initialize()
    repository = ExerciseRepository(connection)
    application = ExerciseApplication(repository)

    if args.command == "add":
        add_exercise(application, args)
    elif args.command == "browse":
        browse_exercises(application, args.identifier)
