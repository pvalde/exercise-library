import os
import shutil

import pytest

from exercise_library.application import ExerciseApplication
from exercise_library.cli.browse_command import browse_exercises
from exercise_library.models import Exercise, ReviewStatus


def test_browse_exercises_prints_no_exercises_message(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    browse_exercises(application, None)

    assert capsys.readouterr().out == "No exercises found.\n"


def test_browse_exercises_prints_exercises(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first_uuid = application.repository.add(
        Exercise(
            prompt="What is Python?",
            answer="A programming language.",
        )
    )
    second_uuid = application.repository.add(
        Exercise(
            prompt="What is pytest?",
            answer="A testing framework.",
        )
    )

    browse_exercises(application, None)

    output = capsys.readouterr().out

    assert str(first_uuid) in output
    assert "What is Python?" in output
    assert str(second_uuid) in output
    assert "What is pytest?" in output

    assert "UUID" in output
    assert "IDENTIFIER" in output
    assert "PROMPT" in output

    assert "(no identifier)" in output


def test_browse_exercises_prints_filtered_exercises(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exercise_uuid = application.repository.add(
        Exercise(
            identifier="book::chapter01::exercise05",
            prompt="What is the derivative of x^2?",
            answer="2x",
        )
    )

    monkeypatch.setattr(
        shutil,
        "get_terminal_size",
        lambda: os.terminal_size((200, 24)),
    )

    browse_exercises(
        application,
        "book::chapter01",
    )

    output = capsys.readouterr().out

    assert str(exercise_uuid) in output
    assert "book::chapter01::exercise05" in output
    assert "What is the derivative of x^2?" in output


def test_browse_exercises_prints_identifier(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    application.repository.add(
        Exercise(
            identifier="book::chapter01::exercise05",
            prompt="What is Python?",
            answer="A programming language.",
        )
    )

    browse_exercises(application, None)

    output = capsys.readouterr().out

    assert "book::chapter01::exercise05" in output


def test_browse_exercises_does_not_print_missing_identifier(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    application.repository.add(
        Exercise(
            prompt="What is Python?",
            answer="A programming language.",
        )
    )

    browse_exercises(application, None)

    output = capsys.readouterr().out

    assert "(no identifier)" in output


def test_browse_exercises_preserves_multiline_content(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    application.repository.add(
        Exercise(
            prompt="Line one\nLine two",
            answer="Answer one\nAnswer two",
        )
    )

    browse_exercises(application, None)

    output = capsys.readouterr().out

    assert "Line one" in output
    assert "Line two" not in output


def test_browse_exercises_hides_status_column_by_default(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    application.repository.add(Exercise(prompt="First prompt", answer="a"))

    browse_exercises(application, None)

    lines = capsys.readouterr().out.splitlines()

    assert lines[0].split() == ["UUID", "IDENTIFIER", "PROMPT"]


def test_browse_exercises_shows_status_column(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    new_uuid = application.repository.add(Exercise(prompt="First prompt", answer="a"))
    seen_uuid = application.repository.add(Exercise(prompt="Second prompt", answer="a"))
    application.record_review(seen_uuid, "good")

    browse_exercises(application, None, show=("status",))

    lines = capsys.readouterr().out.splitlines()

    assert lines[0].split() == ["UUID", "IDENTIFIER", "STATUS", "PROMPT"]

    data_rows = lines[2:]
    new_row = next(line for line in data_rows if str(new_uuid) in line)
    seen_row = next(line for line in data_rows if str(seen_uuid) in line)

    assert "new" in new_row
    assert "reviewed" in seen_row


def test_browse_exercises_filters_reviewed(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    new_uuid = application.repository.add(Exercise(prompt="First prompt", answer="a"))
    seen_uuid = application.repository.add(Exercise(prompt="Second prompt", answer="a"))
    application.record_review(seen_uuid, "good")

    browse_exercises(application, None, status=ReviewStatus.REVIEWED)

    output = capsys.readouterr().out

    assert str(seen_uuid) in output
    assert str(new_uuid) not in output


def test_browse_exercises_filters_new(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    new_uuid = application.repository.add(Exercise(prompt="First prompt", answer="a"))
    seen_uuid = application.repository.add(Exercise(prompt="Second prompt", answer="a"))
    application.record_review(seen_uuid, "good")

    browse_exercises(application, None, status=ReviewStatus.NEW)

    output = capsys.readouterr().out

    assert str(new_uuid) in output
    assert str(seen_uuid) not in output
