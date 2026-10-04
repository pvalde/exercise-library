import webbrowser
from pathlib import Path
from unittest.mock import Mock

import pytest

from exercise_library.application import ExerciseApplication
from exercise_library.cli.show_command import ShowError, show_exercise
from exercise_library.paths import media_dir_path


def test_show_exercise_raises_if_not_uuid_and_identifier() -> None:
    application = Mock()

    with pytest.raises(
        ShowError,
        match="At least one of 'uuid' or 'identifier' must be provided.",
    ):
        show_exercise(application, uuid=None, identifier=None)


def test_show_exercise_renders_terminal_placeholder(
    application: ExerciseApplication,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "diagram.png"
    source.write_bytes(b"image")
    application.add_media(source)
    application.add_exercise(
        prompt="![diagram](diagram.png)",
        answer="See above.",
        identifier="exercise1",
    )

    show_exercise(
        application,
        identifier="exercise1",
        show_prompt=True,
        show_answer=True,
    )

    output = capsys.readouterr().out

    assert "[image: diagram.png]" in output
    assert "![diagram]" not in output


def test_show_exercise_leaves_plain_text_untouched(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    application.add_exercise(
        prompt="What is 2 + 2?",
        answer="4",
        identifier="exercise1",
    )

    show_exercise(
        application,
        identifier="exercise1",
        show_prompt=True,
        show_answer=True,
    )

    output = capsys.readouterr().out

    assert "What is 2 + 2?" in output
    assert "4" in output


def test_show_exercise_renders_browser_image(
    application: ExerciseApplication,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "diagram.png"
    source.write_bytes(b"image")
    application.add_media(source)
    application.add_exercise(
        prompt="![diagram](diagram.png)",
        answer="See above.",
        identifier="exercise1",
    )

    opened: dict[str, str] = {}
    monkeypatch.setattr(
        webbrowser,
        "open",
        lambda uri: opened.setdefault("uri", uri),
    )

    show_exercise(
        application,
        identifier="exercise1",
        show_prompt=True,
        show_answer=True,
        show_in_webbrowser=True,
    )

    html = Path(opened["uri"].removeprefix("file://")).read_text(encoding="utf-8")

    assert (media_dir_path() / "diagram.png").as_uri() in html
    assert "![diagram](diagram.png)" not in html


def test_show_exercise_escapes_raw_html(
    application: ExerciseApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application.add_exercise(
        prompt="This is <b>bold</b>",
        answer='<img src="https://example.com/evil.png">',
        identifier="exercise1",
    )

    opened: dict[str, str] = {}
    monkeypatch.setattr(
        webbrowser,
        "open",
        lambda uri: opened.setdefault("uri", uri),
    )

    show_exercise(
        application,
        identifier="exercise1",
        show_prompt=True,
        show_answer=True,
        show_in_webbrowser=True,
    )

    html = Path(opened["uri"].removeprefix("file://")).read_text(encoding="utf-8")

    assert "<b>bold</b>" not in html
    assert "&lt;b&gt;bold&lt;/b&gt;" in html
    assert "&lt;img" in html
