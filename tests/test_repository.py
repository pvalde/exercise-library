import sqlite3
import time
from pathlib import Path
from uuid import UUID, uuid7

import pytest

from exercise_library.database import initialize
from exercise_library.models import Exercise
from exercise_library.repository import (
    DuplicateIdentifierError,
    ExerciseRepository,
    InvalidExerciseValues,
)

# FIXTURES ---------------------------------------------------------------------


@pytest.fixture
def existing_exercise() -> Exercise:
    connection = initialize()

    exercise = Exercise(
        prompt="existing_prompt",
        answer="existing_answer",
        identifier="existing_exercise",
    )

    exercise_id = ExerciseRepository(connection).add(exercise)

    exercise = Exercise(
        id=exercise_id,
        prompt=exercise.prompt,
        answer=exercise.answer,
        identifier=exercise.identifier,
    )

    return exercise


# add --------------------------------------------------------------------------


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


# list -------------------------------------------------------------------------


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


# browse -----------------------------------------------------------------------


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


# update -----------------------------------------------------------------------


def test_update_exercise(
    existing_exercise: Exercise,
) -> None:
    updated_exercise = Exercise(
        id=existing_exercise.id,
        identifier="updated_exercise",
        prompt="updated_prompt",
        answer="updated_answer",
    )

    connection = initialize()
    result = ExerciseRepository(connection).update(updated_exercise)

    assert result == updated_exercise.id

    row = connection.execute(
        """
        SELECT id, identifier, prompt, answer
        FROM exercises
        WHERE id = ?;
        """,
        (str(updated_exercise.id),),
    ).fetchone()

    assert row["id"] == str(updated_exercise.id)
    assert row["identifier"] == "updated_exercise"
    assert row["prompt"] == "updated_prompt"
    assert row["answer"] == "updated_answer"


def test_update_sets_updated_at_to_a_newer_time(
    existing_exercise: Exercise,
) -> None:
    connection: sqlite3.Connection = initialize()

    original_row: sqlite3.Row | None = connection.execute(
        """
        SELECT updated_at
        FROM exercises
        WHERE id = ?;
        """,
        (str(existing_exercise.id),),
    ).fetchone()

    assert original_row is not None
    original_updated_at = original_row["updated_at"]

    assert isinstance(original_updated_at, (int, float))

    # _to_db_datetime stores milliseconds, so wait briefly before updating.
    time.sleep(0.01)

    updated_exercise = Exercise(
        id=existing_exercise.id,
        identifier="updated_exercise",
        prompt="updated_prompt",
        answer="updated_answer",
    )

    result = ExerciseRepository(connection).update(updated_exercise)

    assert result == updated_exercise.id

    updated_row: sqlite3.Row | None = connection.execute(
        """
        SELECT updated_at
        FROM exercises
        WHERE id = ?;
        """,
        (str(existing_exercise.id),),
    ).fetchone()

    assert updated_row is not None

    updated_updated_at = updated_row["updated_at"]

    assert isinstance(updated_updated_at, (int, float))
    assert updated_updated_at > original_updated_at


def test_update_requires_an_id() -> None:
    connection = initialize()
    repository = ExerciseRepository(connection)

    exercise = Exercise(
        id=None,
        identifier="exercise",
        prompt="prompt",
        answer="answer",
    )

    with pytest.raises(
        InvalidExerciseValues,
        match="Exercise ID has not been provided",
    ):
        repository.update(exercise)


def test_update_rejects_unknown_id() -> None:
    connection = initialize()
    repository = ExerciseRepository(connection)

    unknown_id = uuid7()

    exercise = Exercise(
        id=unknown_id,
        identifier="exercise",
        prompt="prompt",
        answer="answer",
    )

    with pytest.raises(
        InvalidExerciseValues,
        match=f"No exercise found with id {unknown_id}",
    ):
        repository.update(exercise)


def test_update_rejects_duplicate_identifier(
    existing_exercise: Exercise,
) -> None:
    connection = initialize()

    ExerciseRepository(connection).add(
        Exercise(
            identifier="other_exercise",
            prompt="other_prompt",
            answer="other_answer",
        )
    )

    updated_exercise = Exercise(
        id=existing_exercise.id,
        identifier="other_exercise",
        prompt="updated_prompt",
        answer="updated_answer",
    )

    with pytest.raises(
        DuplicateIdentifierError,
        match="Exercise identifier already exists",
    ):
        ExerciseRepository(connection).update(updated_exercise)


def test_update_duplicate_identifier_does_not_change_row(
    existing_exercise: Exercise,
) -> None:
    connection: sqlite3.Connection = initialize()

    ExerciseRepository(connection).add(
        Exercise(
            identifier="other_exercise",
            prompt="other_prompt",
            answer="other_answer",
        )
    )

    updated_exercise = Exercise(
        id=existing_exercise.id,
        identifier="other_exercise",
        prompt="updated_prompt",
        answer="updated_answer",
    )

    with pytest.raises(
        DuplicateIdentifierError,
        match="Exercise identifier already exists",
    ):
        ExerciseRepository(connection).update(updated_exercise)

    row: sqlite3.Row | None = connection.execute(
        """
        SELECT id, identifier, prompt, answer
        FROM exercises
        WHERE id = ?;
        """,
        (str(existing_exercise.id),),
    ).fetchone()

    assert row is not None
    assert row["id"] == str(existing_exercise.id)
    assert row["identifier"] == existing_exercise.identifier
    assert row["prompt"] == existing_exercise.prompt
    assert row["answer"] == existing_exercise.answer
