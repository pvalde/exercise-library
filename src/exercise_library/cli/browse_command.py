import shutil

from exercise_library.application import ExerciseApplication
from exercise_library.models import Exercise


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

    UUID_WIDTH = 36
    MAX_IDENTIFIER_WIDTH = 40
    MIN_PROMPT_WIDTH = 20
    COLUMN_GAP = "  "
    ELLIPSIS = "..."

    rows: list[list[str]] = []
    for exercise in exercises:
        uuid_str = str(exercise.uuid)
        id_str = exercise.identifier or "(no identifier)"
        prompt_str = exercise.prompt.split("\n")[0]
        rows.append([uuid_str, id_str, prompt_str])

    max_width = shutil.get_terminal_size().columns - 1

    id_width = max(len(row[1]) for row in rows + [headers])
    id_width = min(id_width, MAX_IDENTIFIER_WIDTH)

    prompt_width = max_width - UUID_WIDTH - id_width - (2 * len(COLUMN_GAP))
    prompt_width = max(prompt_width, MIN_PROMPT_WIDTH)

    for row in rows:
        if len(row[2]) > prompt_width:
            row[2] = row[2][: prompt_width - len(ELLIPSIS)] + ELLIPSIS

    header_line = (
        f"{headers[0]:<{UUID_WIDTH}}{COLUMN_GAP}"
        + f"{headers[1]:<{id_width}}{COLUMN_GAP}{headers[2]}"
    )
    separator = "-" * len(header_line)

    print(header_line)
    print(separator)

    for row in rows:
        print(
            f"{row[0]:<{UUID_WIDTH}}{COLUMN_GAP}",
            f"{row[1]:<{id_width}}{COLUMN_GAP}{row[2]}",
        )
