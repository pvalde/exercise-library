import pytest

from exercise_library.application import ExerciseApplication, InvalidExerciseError
from exercise_library.cli.rate_command import rate_exercise


def test_rate_records_and_confirms(
    application: ExerciseApplication, capsys: pytest.CaptureFixture[str]
) -> None:
    application.add_exercise(prompt="p", answer="a", identifier="math::limits")

    rate_exercise(application, selector="math::limits", rating="good")

    out = capsys.readouterr().out
    assert "math::limits" in out
    assert "good" in out

    stats = application.review_stats("math::limits")
    assert stats.total_reviews == 1
    assert stats.failures == 0


def test_rate_with_uuid(application: ExerciseApplication) -> None:
    exercise_uuid = application.add_exercise(prompt="p", answer="a")

    rate_exercise(application, selector=str(exercise_uuid), rating="wrong")

    stats = application.review_stats(exercise_uuid)
    assert stats.total_reviews == 1
    assert stats.failures == 1


def test_rate_unknown_selector_raises(
    application: ExerciseApplication,
) -> None:
    with pytest.raises(InvalidExerciseError):
        rate_exercise(application, selector="nope::none", rating="good")
