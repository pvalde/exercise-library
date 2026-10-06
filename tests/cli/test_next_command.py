import pytest

from exercise_library.application import ExerciseApplication
from exercise_library.cli.next_command import next_exercise
from exercise_library.models import ReviewStatus


def test_next_prints_selector_line(
    application: ExerciseApplication, capsys: pytest.CaptureFixture[str]
) -> None:
    application.add_exercise(prompt="p", answer="a", identifier="math::limits")

    next_exercise(application)

    out = capsys.readouterr().out.strip()
    assert out == "math::limits"


def test_next_prints_uuid_when_no_identifier(
    application: ExerciseApplication, capsys: pytest.CaptureFixture[str]
) -> None:
    exercise_uuid = application.add_exercise(prompt="p", answer="a")

    next_exercise(application)

    out = capsys.readouterr().out.strip()
    assert out == str(exercise_uuid)


def test_next_no_match_goes_to_stderr(
    application: ExerciseApplication, capsys: pytest.CaptureFixture[str]
) -> None:
    next_exercise(application)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "No exercises match" in captured.err


def test_next_dry_run_lists_weights(
    application: ExerciseApplication, capsys: pytest.CaptureFixture[str]
) -> None:
    application.add_exercise(prompt="p1", answer="a", identifier="x::one")

    next_exercise(application, dry_run=True)

    out = capsys.readouterr().out
    assert "WEIGHT" in out
    assert "x::one" in out


def test_next_status_filter(
    application: ExerciseApplication, capsys: pytest.CaptureFixture[str]
) -> None:
    application.add_exercise(prompt="p", answer="a", identifier="y::seen")
    application.record_review("y::seen", "good")

    next_exercise(application, status=ReviewStatus.NEW)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "No exercises match" in captured.err
