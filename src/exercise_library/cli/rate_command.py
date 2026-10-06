from uuid import UUID

from exercise_library.application import ExerciseApplication


def rate_exercise(
    application: ExerciseApplication,
    rating: str,
    identifier: str | None = None,
    uuid: UUID | None = None,
) -> None:
    selector: str | UUID
    if uuid is not None:
        selector = uuid
    elif identifier is not None:
        selector = identifier
    else:
        raise ValueError("Either identifier or uuid must be provided.")

    application.record_review(selector, rating)

    label = identifier if identifier is not None else str(uuid)
    print(f"Review recorded: {label} rated as {rating}.")
