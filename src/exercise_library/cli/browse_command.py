from exercise_library.application import ExerciseApplication


def browse_exercises(
    application: ExerciseApplication,
    identifier: str | None,
) -> None:
    exercises = application.browse_exercises(identifier)

    if not exercises:
        print("No exercises found.")
        return

    for exercise in exercises:
        print(f"\n[{exercise.uuid}]")

        if exercise.identifier:
            print(f"Identifier: {exercise.identifier}")

        print(f"Prompt:\n{exercise.prompt}")
        print(f"Answer:\n{exercise.answer}")
        print("-" * 40)
