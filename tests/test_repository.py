from pathlib import Path

import pytest

from exercise_library.database import initialize
from exercise_library.models import Exercise
from exercise_library.repository import ExerciseRepository


def test_add_exercise(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:

    connection = initialize()

    try:
        repository = ExerciseRepository(connection)

        exercise = Exercise(
            prompt="What is the derivative of x^2?",
            answer="2x",
        )

        exercise_id = repository.add(exercise)

        assert exercise_id == 1

        row = connection.execute(
            "SELECT id, prompt, answer FROM exercises WHERE id = ?",
            (exercise_id,),
        ).fetchone()

        assert row is not None
        assert row["prompt"] == exercise.prompt
        assert row["answer"] == exercise.answer
    finally:
        connection.close()


def test_list_all_returns_exercises(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:

    connection = initialize()

    try:
        repo = ExerciseRepository(connection)

        ex1 = Exercise(prompt="Question 1", answer="Answer 1")
        ex2 = Exercise(prompt="Question 2", answer="Answer 2")
        repo.add(ex1)
        repo.add(ex2)
    finally:
        connection.close()

    connection = initialize()
    try:
        repo = ExerciseRepository(connection)

        exercises = repo.list_all()

    finally:
        connection.close()

    assert len(exercises) == 2
    assert exercises[0].prompt == "Question 1"
    assert exercises[0].answer == "Answer 1"
    assert exercises[0].id == 1

    assert exercises[1].prompt == "Question 2"
    assert exercises[1].answer == "Answer 2"
    assert exercises[1].id == 2
