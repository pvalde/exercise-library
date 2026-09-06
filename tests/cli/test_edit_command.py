from unittest.mock import Mock
from uuid import UUID, uuid7

import pytest

from exercise_library.cli.edit_command import EditError, edit_exercise
from exercise_library.models import Exercise


def test_edit_exercise_raises_if_both_exercise_id_and_identifier_are_none() -> None:
    application = Mock()
    with pytest.raises(
        EditError,
        match="At least one of 'id' or 'identifier' must be provided.",
    ):
        edit_exercise(application)


def test_edit_exercise_success_if_at_least_exercise_id_is_provided() -> None:
    id = uuid7()
    application = Mock()

    def fake_get_exercise_by_id(id: UUID) -> Exercise:
        return Exercise(
            id=id,
            identifier="exercise1",
            prompt="prompt",
            answer="answer",
        )

    application.get_exercise_by_id.side_effect = Mock(
        side_effect=fake_get_exercise_by_id
    )

    edit_exercise(application, exercise_id=id)

    application.get_exercise_by_id.assert_called_once()
    application.update_exercise.assert_called_once_with(
        Exercise(
            id=id,
            identifier="exercise1",
            prompt="prompt",
            answer="answer",
        )
    )


def test_edit_exercise_success_if_at_least_exercise_identifier_is_provided() -> None:
    original_identifier = "exercise1"
    id = uuid7()
    application = Mock()

    def fake_get_exercise_by_identifier(identifier: str) -> Exercise:
        return Exercise(
            id=id,
            identifier=original_identifier,
            prompt="prompt",
            answer="answer",
        )

    application.get_exercise_by_identifier.side_effect = Mock(
        side_effect=fake_get_exercise_by_identifier
    )

    edit_exercise(application, identifier=original_identifier)

    application.get_exercise_by_identifier.assert_called_once()
    application.update_exercise.assert_called_once_with(
        Exercise(
            id=id,
            identifier=original_identifier,
            prompt="prompt",
            answer="answer",
        )
    )


def test_edit_exercise_updates_provided_fields() -> None:
    id = uuid7()
    application = Mock()

    def fake_get_exercise_by_id(id: UUID) -> Exercise:
        return Exercise(
            id=id,
            identifier="exercise1",
            prompt="prompt",
            answer="answer",
        )

    application.get_exercise_by_id.side_effect = Mock(
        side_effect=fake_get_exercise_by_id
    )

    edit_exercise(
        application,
        exercise_id=id,
        new_prompt="new_prompt",
        new_answer="new_answer",
        new_identifier="new_identifier",
    )

    application.get_exercise_by_id.assert_called_once()
    application.update_exercise.assert_called_once_with(
        Exercise(
            id=id,
            identifier="new_identifier",
            prompt="new_prompt",
            answer="new_answer",
        )
    )
