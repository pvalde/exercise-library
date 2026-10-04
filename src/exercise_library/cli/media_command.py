from pathlib import Path

from exercise_library.application import ExerciseApplication


def add_media(application: ExerciseApplication, source: Path) -> None:
    name = application.add_media(source)
    print(f"Media was successfully added: {name}")


def list_media(application: ExerciseApplication) -> None:
    media = application.list_media()

    if not media:
        print("No media found.")
        return

    for item in media:
        print(item.name)
