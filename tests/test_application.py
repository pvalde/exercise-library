from uuid import UUID

import pytest

from exercise_library.application import ExerciseApplication, InvalidExerciseError
from exercise_library.database import initialize
from exercise_library.models import Exercise
from exercise_library.repository import ExerciseRepository


@pytest.fixture
def application() -> ExerciseApplication:
    connection = initialize()
    repository = ExerciseRepository(connection)
    return ExerciseApplication(repository)


@pytest.mark.parametrize(
    "prompt",
    [
        "",
        " ",
    ],
)
def test_add_exercise_raises_if_invalid_prompt(
    application: ExerciseApplication,
    prompt: str,
) -> None:

    with pytest.raises(InvalidExerciseError):
        application.add_exercise(
            identifier=None,
            prompt=prompt,
            answer="some content",
        )


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
    with pytest.raises(InvalidExerciseError, match="Prompt cannot be empty."):
        application.add_exercise(
            prompt="",
            answer="An answer.",
        )


def test_add_exercise_rejects_empty_answer(
    application: ExerciseApplication,
) -> None:
    with pytest.raises(InvalidExerciseError, match="Answer cannot be empty."):
        application.add_exercise(
            prompt="A prompt.",
            answer="",
        )


def test_add_exercise_raises_with_duplicated_identifier(
    application: ExerciseApplication,
) -> None:

    identifier = "identifier"
    assert isinstance(
        application.add_exercise(
            identifier=identifier,
            prompt="some content",
            answer="some more content",
        ),
        UUID,
    )

    exc_msg = f"Exercise identifier already exists: {identifier}."

    with pytest.raises(InvalidExerciseError, match=exc_msg):
        application.add_exercise(
            identifier=identifier,
            prompt="some content",
            answer="some more content",
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
        "",
        "",
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
        InvalidExerciseError,
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


# update_exercise --------------------------------------------------------------


def test_update_exercise_success(application: ExerciseApplication) -> None:
    existing_exercise_id = application.add_exercise(
        prompt="prompt",
        answer="answer",
    )

    updated_exercise = Exercise(
        id=existing_exercise_id,
        identifier="updated-exercise",
        prompt="updated prompt",
        answer="updated answer",
    )

    updated_exercise_id = application.update_exercise(updated_exercise)

    assert existing_exercise_id == updated_exercise_id

    exercises = application.browse_exercises(identifier="updated-exercise")

    assert exercises[0].id == updated_exercise_id
    assert exercises[0].identifier == "updated-exercise"
    assert exercises[0].prompt == "updated prompt"
    assert exercises[0].answer == "updated answer"


def test_update_exercise_raises_if_invalid_identifier(
    application: ExerciseApplication,
) -> None:
    existing_exercise_id = application.add_exercise(
        prompt="prompt",
        answer="answer",
    )

    updated_exercise = Exercise(
        id=existing_exercise_id,
        identifier="invalid identifier",
        prompt="updated prompt",
        answer="updated answer",
    )

    with pytest.raises(
        InvalidExerciseError,
        match="Identifier can only contain letters, numbers, dash, underscore"
        + ", and '::' separators.",
    ):
        application.update_exercise(updated_exercise)


def test_update_exercise_raises_if_non_existent_id(
    application: ExerciseApplication,
) -> None:
    exercise = Exercise(prompt="prompt", answer="answer")
    with pytest.raises(InvalidExerciseError, match="No exercise found with id"):
        application.update_exercise(exercise)


def test_update_exercise_raises_if_existing_identifier(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(
        identifier="exercise1",
        prompt="prompt1",
        answer="answer1",
    )

    exercise2_id = application.add_exercise(
        identifier="exercise2",
        prompt="prompt2",
        answer="answer2",
    )

    assert len(application.browse_exercises()) == 2

    updated_exercise2 = Exercise(
        id=exercise2_id,
        identifier="exercise1",
        prompt="updated prompt2",
        answer="updated answer2",
    )

    with pytest.raises(
        InvalidExerciseError,
        match=f"Exercise identifier already exists: {updated_exercise2.identifier}",
    ):
        application.update_exercise(updated_exercise2)


def test_update_exercise_success_with_the_same_identifier(
    application: ExerciseApplication,
) -> None:
    exercise_id = application.add_exercise(
        identifier="exercise1",
        prompt="prompt1",
        answer="answer1",
    )

    updated_exercise = Exercise(
        id=exercise_id,
        identifier="exercise1",
        prompt="updated_prompt",
        answer="updated_answer",
    )

    exercise_id = application.update_exercise(updated_exercise)

    assert exercise_id is not None
    assert isinstance(exercise_id, UUID)
