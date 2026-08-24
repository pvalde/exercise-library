from uuid import UUID

import pytest

from exercise_library.application import ExerciseApplication
from exercise_library.database import initialize
from exercise_library.models import Exercise
from exercise_library.repository import ExerciseRepository


@pytest.fixture
def application() -> ExerciseApplication:
    connection = initialize()
    repository = ExerciseRepository(connection)
    return ExerciseApplication(repository)


def test_add_exercise_returns_id(
    application: ExerciseApplication,
) -> None:
    exercise_id = application.add_exercise(
        prompt="What is Python?",
        answer="A programming language.",
    )

    assert exercise_id is not None
    assert isinstance(exercise_id, UUID)


def test_add_exercise_persists_exercise(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(
        prompt="What is Python?",
        answer="A programming language.",
        identifier="book::chapter01::exercise05",
    )

    exercises = application.repository.browse()

    assert exercises[0].id is not None
    assert exercises[0].prompt == "What is Python?"
    assert exercises[0].answer == "A programming language."
    assert exercises[0].identifier == "book::chapter01::exercise05"


def test_add_exercise_rejects_empty_prompt(
    application: ExerciseApplication,
) -> None:
    with pytest.raises(ValueError, match="Prompt and answer cannot be empty."):
        application.add_exercise(
            prompt="",
            answer="An answer.",
        )


def test_add_exercise_rejects_empty_answer(
    application: ExerciseApplication,
) -> None:
    with pytest.raises(ValueError, match="Prompt and answer cannot be empty."):
        application.add_exercise(
            prompt="A prompt.",
            answer="",
        )


def test_browse_exercises_returns_exercises(
    application: ExerciseApplication,
) -> None:
    application.repository.add(
        Exercise(
            prompt="What is Python?",
            answer="A programming language.",
        )
    )
    application.repository.add(
        Exercise(
            prompt="What is pytest?",
            answer="A testing framework.",
        )
    )

    exercises = application.browse_exercises()

    assert exercises[0].id is not None
    assert exercises[0].prompt == "What is Python?"
    assert exercises[0].answer == "A programming language."

    assert exercises[1].id is not None
    assert exercises[1].prompt == "What is pytest?"
    assert exercises[1].answer == "A testing framework."


def test_browse_exercises_filters_by_identifier(
    application: ExerciseApplication,
) -> None:
    application.repository.add(
        Exercise(
            prompt="Exercise 1",
            answer="Answer 1",
            identifier="book::chapter01::exercise01",
        )
    )
    application.repository.add(
        Exercise(
            prompt="Exercise 2",
            answer="Answer 2",
            identifier="book::chapter01::exercise02",
        )
    )
    application.repository.add(
        Exercise(
            prompt="Exercise 3",
            answer="Answer 3",
            identifier="book::chapter02::exercise01",
        )
    )

    exercises = application.browse_exercises("book::chapter01")

    assert exercises[0].id is not None
    assert exercises[0].prompt == "Exercise 1"
    assert exercises[0].answer == "Answer 1"
    assert exercises[0].identifier == "book::chapter01::exercise01"

    assert exercises[1].id is not None
    assert exercises[1].prompt == "Exercise 2"
    assert exercises[1].answer == "Answer 2"
    assert exercises[1].identifier == "book::chapter01::exercise02"


@pytest.mark.parametrize(
    "identifier",
    [
        "book",
        "book01",
        "book_01",
        "book-01",
        "book::chapter01",
        "book_01::chapter-02",
        "book::chapter01::exercise_05",
        "Book-01_foo::Chapter-02::Exercise_05",
    ],
)
def test_add_exercise_accepts_valid_identifier(
    application: ExerciseApplication,
    identifier: str,
) -> None:
    exercise_id = application.add_exercise(
        prompt="What is Python?",
        answer="A programming language.",
        identifier=identifier,
    )

    assert exercise_id is not None


@pytest.mark.parametrize(
    "identifier",
    [
        "book:chapter",
        "book:::chapter",
        "book::chapter:01",
        "book/chapter",
        "book chapter",
        "book.chapter",
        "book::chapter::",
        "::book",
        "book::",
        ":book",
        "book:",
        "book::chapter::exercise/01",
        "book::chapter::exercise 01",
    ],
)
def test_add_exercise_rejects_invalid_identifier(
    application: ExerciseApplication,
    identifier: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="Identifier can only contain letters, numbers, dash,"
        + " underscore, and '::' separators.",
    ):
        application.add_exercise(
            prompt="What is Python?",
            answer="A programming language.",
            identifier=identifier,
        )


def test_add_exercise_allows_identifier_to_be_none(
    application: ExerciseApplication,
) -> None:
    exercise_id = application.add_exercise(
        prompt="What is Python?",
        answer="A programming language.",
        identifier=None,
    )

    assert exercise_id is not None
