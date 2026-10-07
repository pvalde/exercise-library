from exercise_library.application import ExerciseApplication


def rate_exercise(
    application: ExerciseApplication,
    selector: str,
    rating: str,
) -> None:
    application.record_review(selector, rating)

    print(f"Review recorded: {selector} rated as {rating}.")
