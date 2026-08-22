from exercise_library.models import Exercise


def test_exercise() -> None:
    exercise = Exercise(
        prompt="What is the derivative of x^2?",
        answer="2x",
    )

    assert exercise.prompt == "What is the derivative of x^2?"
    assert exercise.answer == "2x"
