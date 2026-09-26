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

    exercise_uuid = ExerciseRepository(connection).add(exercise)

    exercise = Exercise(
        uuid=exercise_uuid,
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

        exercise_uuid = repository.add(exercise)

        assert exercise_uuid is not None

        row = connection.execute(
            "SELECT uuid, identifier, prompt, answer FROM exercises WHERE uuid = ?",
            (str(exercise_uuid),),
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

        exercise_uuid = repository.add(exercise)

        exercises = repository.list_all()

        assert exercise_uuid is not None
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
    assert exercises[0].uuid is not None
    assert isinstance(exercises[0].uuid, UUID)
    assert exercises[0].identifier == "book-a::exset::01"

    assert exercises[1].prompt == "Question 2"
    assert exercises[1].answer == "Answer 2"
    assert exercises[0].uuid is not None
    assert isinstance(exercises[0].uuid, UUID)
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
        uuid=existing_exercise.uuid,
        identifier="updated_exercise",
        prompt="updated_prompt",
        answer="updated_answer",
    )

    connection = initialize()
    result = ExerciseRepository(connection).update(updated_exercise)

    assert result == updated_exercise.uuid

    row = connection.execute(
        """
        SELECT uuid, identifier, prompt, answer
        FROM exercises
        WHERE uuid = ?;
        """,
        (str(updated_exercise.uuid),),
    ).fetchone()

    assert row["uuid"] == str(updated_exercise.uuid)
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
        WHERE uuid = ?;
        """,
        (str(existing_exercise.uuid),),
    ).fetchone()

    assert original_row is not None
    original_updated_at = original_row["updated_at"]

    assert isinstance(original_updated_at, (int, float))

    # _to_db_datetime stores milliseconds, so wait briefly before updating.
    time.sleep(0.01)

    updated_exercise = Exercise(
        uuid=existing_exercise.uuid,
        identifier="updated_exercise",
        prompt="updated_prompt",
        answer="updated_answer",
    )

    result = ExerciseRepository(connection).update(updated_exercise)

    assert result == updated_exercise.uuid

    updated_row: sqlite3.Row | None = connection.execute(
        """
        SELECT updated_at
        FROM exercises
        WHERE uuid = ?;
        """,
        (str(existing_exercise.uuid),),
    ).fetchone()

    assert updated_row is not None

    updated_updated_at = updated_row["updated_at"]

    assert isinstance(updated_updated_at, (int, float))
    assert updated_updated_at > original_updated_at


def test_update_requires_an_uuid() -> None:
    connection = initialize()
    repository = ExerciseRepository(connection)

    exercise = Exercise(
        uuid=None,
        identifier="exercise",
        prompt="prompt",
        answer="answer",
    )

    with pytest.raises(
        InvalidExerciseValues,
        match="Exercise UUID has not been provided",
    ):
        repository.update(exercise)


def test_update_rejects_unknown_uuid() -> None:
    connection = initialize()
    repository = ExerciseRepository(connection)

    unknown_uuid = uuid7()

    exercise = Exercise(
        uuid=unknown_uuid,
        identifier="exercise",
        prompt="prompt",
        answer="answer",
    )

    with pytest.raises(
        InvalidExerciseValues,
        match=f"No exercise found with uuid {unknown_uuid}",
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
        uuid=existing_exercise.uuid,
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
        uuid=existing_exercise.uuid,
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
        SELECT uuid, identifier, prompt, answer
        FROM exercises
        WHERE uuid = ?;
        """,
        (str(existing_exercise.uuid),),
    ).fetchone()

    assert row is not None
    assert row["uuid"] == str(existing_exercise.uuid)
    assert row["identifier"] == existing_exercise.identifier
    assert row["prompt"] == existing_exercise.prompt
    assert row["answer"] == existing_exercise.answer


# get --------------------------------------------------------------------------


def test_get_by_identifier_returns_exercise(
    existing_exercise: Exercise,
) -> None:
    connection = initialize()

    assert existing_exercise.identifier is not None
    result = ExerciseRepository(connection).get_by_identifier(
        existing_exercise.identifier
    )

    assert result.uuid == existing_exercise.uuid
    assert result.prompt == existing_exercise.prompt
    assert result.answer == existing_exercise.answer
    assert result.identifier == existing_exercise.identifier


def test_get_by_identifier_raises_when_exercise_does_not_exists(
    existing_exercise: Exercise,
) -> None:
    with pytest.raises(InvalidExerciseValues, match="Exercise not found"):
        connection = initialize()
        ExerciseRepository(connection).get_by_identifier("non-existent-identifier")


def test_get_by_uuid_returns_exercise(
    existing_exercise: Exercise,
) -> None:
    connection = initialize()

    assert existing_exercise.uuid is not None
    result = ExerciseRepository(connection).get_by_uuid(existing_exercise.uuid)

    assert result.uuid == existing_exercise.uuid
    assert result.prompt == existing_exercise.prompt
    assert result.answer == existing_exercise.answer
    assert result.identifier == existing_exercise.identifier


def test_get_by_uuid_raises_when_exercise_does_not_exists(
    existing_exercise: Exercise,
) -> None:
    with pytest.raises(InvalidExerciseValues, match="Exercise not found"):
        connection = initialize()
        ExerciseRepository(connection).get_by_identifier(str(uuid7()))


def test_get_by_identifier_and_get_by_uuid_return_same_exercise(
    existing_exercise: Exercise,
) -> None:

    assert existing_exercise.uuid is not None
    assert existing_exercise.identifier is not None

    connection = initialize()
    repo = ExerciseRepository(connection)
    by_identifier = repo.get_by_identifier(existing_exercise.identifier)
    by_uuid = repo.get_by_uuid(existing_exercise.uuid)

    assert by_identifier == by_uuid


# identifier_exists ------------------------------------------------------------


def test_identifier_exists(
    existing_exercise: Exercise,
) -> None:

    assert existing_exercise.uuid is not None
    assert existing_exercise.identifier is not None

    connection = initialize()
    repo = ExerciseRepository(connection)

    assert repo.identifier_exists(existing_exercise.identifier)
    assert not repo.identifier_exists("non-existent-identifier")
