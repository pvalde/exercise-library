import pytest

from exercise_library.application import ExerciseApplication
from exercise_library.cli.browse_command import browse_exercises
from exercise_library.models import Exercise


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
    first_id = application.repository.add(
        Exercise(
            prompt="What is Python?",
            answer="A programming language.",
        )
    )
    second_id = application.repository.add(
        Exercise(
            prompt="What is pytest?",
            answer="A testing framework.",
        )
    )

    browse_exercises(application, None)

    output = capsys.readouterr().out

    assert f"[{first_id}]" in output
    assert "Prompt:\nWhat is Python?" in output
    assert "Answer:\nA programming language." in output

    assert f"[{second_id}]" in output
    assert "Prompt:\nWhat is pytest?" in output
    assert "Answer:\nA testing framework." in output

    assert output.count("-" * 40) == 2


def test_browse_exercises_prints_filtered_exercises(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exercise_id = application.repository.add(
        Exercise(
            identifier="book::chapter01::exercise05",
            prompt="What is the derivative of x^2?",
            answer="2x",
        )
    )

    browse_exercises(
        application,
        "book::chapter01",
    )

    output = capsys.readouterr().out

    assert f"[{exercise_id}]" in output
    assert "book::chapter01::exercise05" in output
    assert "Prompt:\nWhat is the derivative of x^2?" in output
    assert "Answer:\n2x" in output


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

    assert "Identifier: book::chapter01::exercise05" in output


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

    assert "Identifier:" not in output


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

    assert "Prompt:\nLine one\nLine two" in output
    assert "Answer:\nAnswer one\nAnswer two" in output
