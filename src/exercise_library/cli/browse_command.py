from exercise_library.application import ExerciseApplication
from exercise_library.models import Exercise

from .table import print_three_column_table


def browse_exercises(
    application: ExerciseApplication,
    identifier: str | None,
) -> None:
    exercises = application.browse_exercises(identifier)

    if not exercises:
        print("No exercises found.")
        return

    _print_table(exercises)


def _print_table(exercises: list[Exercise]) -> None:
    headers: list[str] = ["UUID", "IDENTIFIER", "PROMPT"]

    rows: list[list[str]] = []
    for exercise in exercises:
        uuid_str = str(exercise.uuid)
        id_str = exercise.identifier or "(no identifier)"
        prompt_str = exercise.prompt.split("\n")[0]
        rows.append([uuid_str, id_str, prompt_str])

    print_three_column_table(
        first_col_width=36,
        second_col_max=40,
        headers=headers,
        rows=rows,
    )
