from exercise_library.application import ExerciseApplication


def list_identifiers(
    application: ExerciseApplication,
    identifier: str | None,
    depth: int | None,
    count: bool,
) -> None:
    items = application.list_identifier_prefixes(
        identifier=identifier,
        depth=depth,
    )

    if not items:
        print("No identifiers found.")
        return

    for item in items:
        if count is False:
            print(item.prefix)
        else:
            print(f"{item.prefix} ({item.exercise_count})")
