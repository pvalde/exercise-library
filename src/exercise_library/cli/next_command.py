import sys
from datetime import UTC, datetime

from exercise_library.application import ExerciseApplication
from exercise_library.models import ReviewStatus
from exercise_library.review import compute_weight, select_next_exercise

from .table import print_three_column_table

_DRY_RUN_LIMIT = 10


def next_exercise(
    application: ExerciseApplication,
    identifier: str | None = None,
    status: ReviewStatus = ReviewStatus.ALL,
    dry_run: bool = False,
) -> None:
    if dry_run:
        _print_dry_run(application, identifier, status)
        return

    exercise = select_next_exercise(application, identifier=identifier, status=status)

    if exercise is None:
        print("No exercises match the given filters.", file=sys.stderr)
        return

    print(exercise.identifier if exercise.identifier else str(exercise.uuid))


def _print_dry_run(
    application: ExerciseApplication,
    identifier: str | None,
    status: ReviewStatus,
) -> None:
    rows: list[tuple[float, str, str]] = []
    now = datetime.now(tz=UTC)

    for exercise in application.browse_exercises(identifier):
        assert exercise.uuid is not None
        stats = application.review_stats(exercise.uuid)

        if status is ReviewStatus.NEW and stats.total_reviews > 0:
            continue
        if status is ReviewStatus.REVIEWED and stats.total_reviews == 0:
            continue

        weight = compute_weight(stats, now=now)
        label = exercise.identifier or str(exercise.uuid)
        prompt_preview = exercise.prompt.split("\n")[0]
        rows.append((weight, label, prompt_preview))

    if not rows:
        print("No exercises match the given filters.")
        return

    rows.sort(key=lambda row: row[0], reverse=True)

    print_three_column_table(
        first_col_width=10,
        second_col_max=40,
        headers=["WEIGHT", "IDENTIFIER", "PROMPT"],
        rows=[
            [f"{weight:.3f}", label, preview]
            for weight, label, preview in rows[:_DRY_RUN_LIMIT]
        ],
    )
