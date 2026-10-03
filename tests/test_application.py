from uuid import UUID, uuid7

import pytest

from exercise_library.application import (
    ExerciseApplication,
    IdentifierPrefix,
    InvalidDepthError,
    InvalidExerciseError,
)
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


def test_add_exercise_returns_uuid(
    application: ExerciseApplication,
) -> None:
    exercise_uuid = application.add_exercise(
        prompt="What is Python?",
        answer="A programming language.",
    )

    assert exercise_uuid is not None
    assert isinstance(exercise_uuid, UUID)


def test_add_exercise_persists_exercise(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(
        prompt="What is Python?",
        answer="A programming language.",
        identifier="book::chapter01::exercise05",
    )

    exercises = application.repository.browse()

    assert exercises[0].uuid is not None
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

    assert exercises[0].uuid is not None
    assert exercises[0].prompt == "What is Python?"
    assert exercises[0].answer == "A programming language."

    assert exercises[1].uuid is not None
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

    assert exercises[0].uuid is not None
    assert exercises[0].prompt == "Exercise 1"
    assert exercises[0].answer == "Answer 1"
    assert exercises[0].identifier == "book::chapter01::exercise01"

    assert exercises[1].uuid is not None
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
    exercise_uuid = application.add_exercise(
        prompt="What is Python?",
        answer="A programming language.",
        identifier=identifier,
    )

    assert exercise_uuid is not None


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
        match=f"'{identifier}' is an invalid identifier."
        + "\nIt can only contain letters, numbers, dash,"
        + " underscore and '::' separators.",
    ):
        application.add_exercise(
            prompt="What is Python?",
            answer="A programming language.",
            identifier=identifier,
        )


def test_add_exercise_allows_identifier_to_be_none(
    application: ExerciseApplication,
) -> None:
    exercise_uuid = application.add_exercise(
        prompt="What is Python?",
        answer="A programming language.",
        identifier=None,
    )

    assert exercise_uuid is not None


# update_exercise --------------------------------------------------------------


def test_update_exercise_success(application: ExerciseApplication) -> None:
    existing_exercise_uuid = application.add_exercise(
        prompt="prompt",
        answer="answer",
    )

    updated_exercise = Exercise(
        uuid=existing_exercise_uuid,
        identifier="updated-exercise",
        prompt="updated prompt",
        answer="updated answer",
    )

    updated_exercise_uuid = application.update_exercise(updated_exercise)

    assert existing_exercise_uuid == updated_exercise_uuid

    exercises = application.browse_exercises(identifier="updated-exercise")

    assert exercises[0].uuid == updated_exercise_uuid
    assert exercises[0].identifier == "updated-exercise"
    assert exercises[0].prompt == "updated prompt"
    assert exercises[0].answer == "updated answer"


def test_update_exercise_raises_if_invalid_identifier(
    application: ExerciseApplication,
) -> None:
    existing_exercise_uuid = application.add_exercise(
        prompt="prompt",
        answer="answer",
    )

    updated_exercise = Exercise(
        uuid=existing_exercise_uuid,
        identifier="invalid identifier",
        prompt="updated prompt",
        answer="updated answer",
    )

    with pytest.raises(
        InvalidExerciseError,
        match="'invalid identifier' is an invalid identifier."
        + "\nIt can only contain letters, numbers, dash, underscore"
        + " and '::' separators.",
    ):
        application.update_exercise(updated_exercise)


def test_update_exercise_raises_if_non_existent_uuid(
    application: ExerciseApplication,
) -> None:
    exercise = Exercise(prompt="prompt", answer="answer")
    with pytest.raises(InvalidExerciseError, match="No exercise found with uuid"):
        application.update_exercise(exercise)


def test_update_exercise_raises_if_existing_identifier(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(
        identifier="exercise1",
        prompt="prompt1",
        answer="answer1",
    )

    exercise2_uuid = application.add_exercise(
        identifier="exercise2",
        prompt="prompt2",
        answer="answer2",
    )

    assert len(application.browse_exercises()) == 2

    updated_exercise2 = Exercise(
        uuid=exercise2_uuid,
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
    exercise_uuid = application.add_exercise(
        identifier="exercise1",
        prompt="prompt1",
        answer="answer1",
    )

    updated_exercise = Exercise(
        uuid=exercise_uuid,
        identifier="exercise1",
        prompt="updated_prompt",
        answer="updated_answer",
    )

    exercise_uuid = application.update_exercise(updated_exercise)

    assert exercise_uuid is not None
    assert isinstance(exercise_uuid, UUID)


# get_exercise_by_uuid -----------------------------------------------------------


def test_get_exercise_by_uuid(application: ExerciseApplication) -> None:
    exercise_uuid = application.add_exercise(prompt="prompt", answer="answer")

    assert exercise_uuid is not None

    exercise = application.get_exercise_by_uuid(exercise_uuid)

    assert exercise.uuid == exercise_uuid
    assert exercise.prompt == "prompt"
    assert exercise.answer == "answer"


def test_get_exercise_by_uuid_raises_if_no_exercise(
    application: ExerciseApplication,
) -> None:
    with pytest.raises(InvalidExerciseError):
        application.get_exercise_by_uuid(uuid7())


# get_exercise_by_identifier ---------------------------------------------------


def test_get_exercise_by_identifer(application: ExerciseApplication) -> None:
    identifier = "exercise1"
    exercise_uuid = application.add_exercise(
        prompt="prompt",
        answer="answer",
        identifier=identifier,
    )
    assert exercise_uuid is not None

    exercise = application.get_exercise_by_identifier(identifier)

    assert exercise.uuid == exercise_uuid
    assert exercise.identifier == identifier
    assert exercise.prompt == "prompt"
    assert exercise.answer == "answer"


def test_get_exercise_by_identifier_raises_if_invalid_identifier(
    application: ExerciseApplication,
) -> None:
    with pytest.raises(
        InvalidExerciseError,
        match="'invalid identifier' is an invalid identifier.\nIt can only contain",
    ):
        application.get_exercise_by_identifier("invalid identifier")


def test_get_exercise_by_identifer_raises_if_non_existent_identifier(
    application: ExerciseApplication,
) -> None:
    with pytest.raises(InvalidExerciseError, match="Exercise not found"):
        application.get_exercise_by_identifier("non-existent-identifier")


# list_identifier_prefixes ------------------------------------------------------


def test_list_identifier_prefixes_returns_empty_list(
    application: ExerciseApplication,
) -> None:
    assert application.list_identifier_prefixes() == []


def test_list_identifier_prefixes_returns_all_prefixes_sorted(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(
        prompt="p1",
        answer="a1",
        identifier="book::chapter01::exercise01",
    )
    application.add_exercise(
        prompt="p2",
        answer="a2",
        identifier="book::chapter02::exercise01",
    )
    application.add_exercise(
        prompt="p3",
        answer="a3",
        identifier="other",
    )

    prefixes = application.list_identifier_prefixes()

    assert prefixes == [
        IdentifierPrefix(prefix="book::chapter01::exercise01", exercise_count=1),
        IdentifierPrefix(prefix="book::chapter02::exercise01", exercise_count=1),
        IdentifierPrefix(prefix="other", exercise_count=1),
    ]


def test_list_identifier_prefixes_ignores_exercises_without_identifier(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(prompt="p1", answer="a1")
    application.add_exercise(
        prompt="p2",
        answer="a2",
        identifier="book::chapter01",
    )

    prefixes = application.list_identifier_prefixes()

    assert prefixes == [
        IdentifierPrefix(prefix="book::chapter01", exercise_count=1),
    ]


def test_list_identifier_prefixes_respects_depth(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(
        prompt="p1",
        answer="a1",
        identifier="book::chapter01::exercise01",
    )
    application.add_exercise(
        prompt="p2",
        answer="a2",
        identifier="book::chapter01::exercise02",
    )
    application.add_exercise(
        prompt="p3",
        answer="a3",
        identifier="book::chapter02::exercise01",
    )

    prefixes = application.list_identifier_prefixes(depth=2)

    assert prefixes == [
        IdentifierPrefix(prefix="book::chapter01", exercise_count=2),
        IdentifierPrefix(prefix="book::chapter02", exercise_count=1),
    ]


def test_list_identifier_prefixes_filters_by_identifier(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(
        prompt="p1",
        answer="a1",
        identifier="book::chapter01::exercise01",
    )
    application.add_exercise(
        prompt="p2",
        answer="a2",
        identifier="book::chapter02::exercise01",
    )

    prefixes = application.list_identifier_prefixes(identifier="book::chapter01")

    assert prefixes == [
        IdentifierPrefix(prefix="book::chapter01::exercise01", exercise_count=1),
    ]


def test_list_identifier_prefixes_combines_identifier_and_depth(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(
        prompt="p1",
        answer="a1",
        identifier="book::chapter01::exercise01",
    )
    application.add_exercise(
        prompt="p2",
        answer="a2",
        identifier="book::chapter01::exercise02",
    )
    application.add_exercise(
        prompt="p3",
        answer="a3",
        identifier="book::chapter02::exercise01",
    )

    prefixes = application.list_identifier_prefixes(
        identifier="book",
        depth=2,
    )

    assert prefixes == [
        IdentifierPrefix(prefix="book::chapter01", exercise_count=2),
        IdentifierPrefix(prefix="book::chapter02", exercise_count=1),
    ]


def test_list_identifier_prefixes_counts_exact_prefix_matches(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(prompt="p1", answer="a1", identifier="book")
    application.add_exercise(
        prompt="p2",
        answer="a2",
        identifier="book::chapter01",
    )
    application.add_exercise(
        prompt="p3",
        answer="a3",
        identifier="book::chapter01::exercise01",
    )

    prefixes = application.list_identifier_prefixes()

    assert prefixes[0] == IdentifierPrefix(prefix="book", exercise_count=3)


def test_list_identifier_prefixes_raises_if_invalid_identifier(
    application: ExerciseApplication,
) -> None:
    with pytest.raises(
        InvalidExerciseError,
        match="'invalid identifier' is an invalid identifier.",
    ):
        application.list_identifier_prefixes(identifier="invalid identifier")


@pytest.mark.parametrize("depth", [0, -1])
def test_list_identifier_prefixes_raises_if_invalid_depth(
    application: ExerciseApplication,
    depth: int,
) -> None:
    with pytest.raises(InvalidDepthError, match="Depth must be a positive integer."):
        application.list_identifier_prefixes(depth=depth)
