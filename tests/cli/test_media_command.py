from pathlib import Path

import pytest

from exercise_library.application import ExerciseApplication
from exercise_library.cli.media_command import add_media, list_media


def _write_image(tmp_path: Path, name: str = "diagram.png") -> Path:
    path = tmp_path / name
    path.write_bytes(b"image bytes")
    return path


def test_add_media_prints_success_message(
    application: ExerciseApplication,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = _write_image(tmp_path)

    add_media(application, source)

    assert capsys.readouterr().out == "Media was successfully added: diagram.png\n"


def test_list_media_prints_no_media_message(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    list_media(application)

    assert capsys.readouterr().out == "No media found.\n"


def test_list_media_prints_stored_names(
    application: ExerciseApplication,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    application.add_media(_write_image(tmp_path, "zebra.png"))
    application.add_media(_write_image(tmp_path, "apple.png"))

    list_media(application)

    assert capsys.readouterr().out == "apple.png\nzebra.png\n"
