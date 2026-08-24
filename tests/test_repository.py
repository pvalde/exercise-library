from pathlib import Path
from uuid import UUID

import pytest

from exercise_library.database import initialize
from exercise_library.models import Exercise
from exercise_library.repository import DuplicateIdentifierError, ExerciseRepository


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
            identifier="book::exset::01",
        )

        exercise_id = repository.add(exercise)

        assert exercise_id is not None

        row = connection.execute(
            "SELECT id, identifier, prompt, answer FROM exercises WHERE id = ?",
            (str(exercise_id),),
        ).fetchone()

        assert row is not None
        assert row["identifier"] == exercise.identifier
        assert row["prompt"] == exercise.prompt
        assert row["answer"] == exercise.answer
    finally:
        connection.close()


def test_add_exercise_without_identifier(
    tmp_path: Path,
) -> None:
    connection = initialize()

    try:
        repository = ExerciseRepository(connection)

        exercise = Exercise(
            prompt="What is 2 + 2?",
            answer="4",
        )

        exercise_id = repository.add(exercise)

        exercises = repository.list_all()

        assert exercise_id is not None
        assert len(exercises) == 1
        assert exercises[0].identifier is None
        assert exercises[0].prompt == exercise.prompt
        assert exercises[0].answer == exercise.answer
    finally:
        connection.close()


def test_cannot_add_duplicate_identifier(
    tmp_path: Path,
) -> None:
    connection = initialize()

    try:
        repository = ExerciseRepository(connection)

        identifier = "book::exset::01"

        repository.add(
            Exercise(
                prompt="Question 1",
                answer="Answer 1",
                identifier=identifier,
            )
        )

        with pytest.raises(DuplicateIdentifierError):
            repository.add(
                Exercise(
                    prompt="Question 2",
                    answer="Answer 2",
                    identifier=identifier,
                )
            )
    finally:
        connection.close()


def test_list_all_returns_exercises(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:

    connection = initialize()

    try:
        repo = ExerciseRepository(connection)

        ex1 = Exercise(
            prompt="Question 1", answer="Answer 1", identifier="book-a::exset::01"
        )
        ex2 = Exercise(
            prompt="Question 2", answer="Answer 2", identifier="book-b::exset::02"
        )
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
    assert exercises[0].id is not None
    assert isinstance(exercises[0].id, UUID)
    assert exercises[0].identifier == "book-a::exset::01"

    assert exercises[1].prompt == "Question 2"
    assert exercises[1].answer == "Answer 2"
    assert exercises[0].id is not None
    assert isinstance(exercises[0].id, UUID)
    assert exercises[1].identifier == "book-b::exset::02"


def test_browse_matches_exact_identifier(
    tmp_path: Path,
) -> None:
    connection = initialize()

    try:
        repository = ExerciseRepository(connection)

        repository.add(
            Exercise(
                prompt="Question 1",
                answer="Answer 1",
                identifier="book::chapter01",
            )
        )
        repository.add(
            Exercise(
                prompt="Question 2",
                answer="Answer 2",
                identifier="book::chapter02",
            )
        )

        exercises = repository.browse("book::chapter01")

        assert len(exercises) == 1
        assert exercises[0].identifier == "book::chapter01"
    finally:
        connection.close()


def test_browse_matches_identifier_prefix(
    tmp_path: Path,
) -> None:
    connection = initialize()

    try:
        repository = ExerciseRepository(connection)

        repository.add(
            Exercise(
                prompt="Question 1",
                answer="Answer 1",
                identifier="book::chapter01",
            )
        )
        repository.add(
            Exercise(
                prompt="Question 2",
                answer="Answer 2",
                identifier="book::chapter01::section03",
            )
        )
        repository.add(
            Exercise(
                prompt="Question 3",
                answer="Answer 3",
                identifier="book::chapter02",
            )
        )

        exercises = repository.browse("book::chapter01")

        assert len(exercises) == 2
        assert exercises[0].identifier == "book::chapter01"
        assert exercises[1].identifier == "book::chapter01::section03"
    finally:
        connection.close()


def test_browse_does_not_match_similar_identifier(
    tmp_path: Path,
) -> None:
    connection = initialize()

    try:
        repository = ExerciseRepository(connection)

        repository.add(
            Exercise(
                prompt="Question 1",
                answer="Answer 1",
                identifier="book::chapter01",
            )
        )
        repository.add(
            Exercise(
                prompt="Question 2",
                answer="Answer 2",
                identifier="book::chapter010",
            )
        )

        exercises = repository.browse("book::chapter01")

        assert len(exercises) == 1
        assert exercises[0].identifier == "book::chapter01"
    finally:
        connection.close()


def test_browse_returns_empty_list_when_no_identifier_matches(
    tmp_path: Path,
) -> None:
    connection = initialize()

    try:
        repository = ExerciseRepository(connection)

        repository.add(
            Exercise(
                prompt="Question",
                answer="Answer",
                identifier="book::chapter01",
            )
        )

        exercises = repository.browse("book::chapter99")

        assert exercises == []
    finally:
        connection.close()
