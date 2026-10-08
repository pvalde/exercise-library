from collections.abc import Sequence

from exercise_library.application import ExerciseApplication
from exercise_library.models import Exercise, ReviewStatus

from .table import Adapt, ColumnWidth, Fill, Fixed, print_table


def browse_exercises(
    application: ExerciseApplication,
    identifier: str | None,
    status: ReviewStatus = ReviewStatus.ALL,
    show: Sequence[str] = (),
) -> None:
    exercises = application.browse_exercises(identifier, status)

    if not exercises:
        print("No exercises found.")
        return

    _print_table(application, exercises, show_status="status" in show)


def _print_table(
    application: ExerciseApplication,
    exercises: list[Exercise],
    show_status: bool,
) -> None:
    headers: list[str] = ["UUID", "IDENTIFIER"]
    widths: list[ColumnWidth] = [Fixed(36), Adapt(40)]

    if show_status:
        headers.append("STATUS")
        widths.append(Adapt())

    headers.append("PROMPT")
    widths.append(Fill())

    rows: list[list[str]] = []
    for exercise in exercises:
        row = [str(exercise.uuid), exercise.identifier or "(no identifier)"]
        if show_status:
            assert exercise.uuid is not None
            stats = application.review_stats(exercise.uuid)
            status = (
                ReviewStatus.REVIEWED.value
                if stats.total_reviews > 0
                else ReviewStatus.NEW.value
            )
            row.append(status)
        row.append(exercise.prompt.split("\n")[0])
        rows.append(row)

    print_table(
        headers=headers,
        rows=rows,
        widths=widths,
    )
