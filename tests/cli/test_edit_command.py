from unittest.mock import Mock
from uuid import UUID, uuid7

import pytest

from exercise_library.application import ExerciseApplication
from exercise_library.cli.edit_command import (
    EditError,
    _edit_exercise_env_editor,
    edit_exercise,
    edit_exercise_env_editor,
)
from exercise_library.database import initialize
from exercise_library.models import Exercise
from exercise_library.repository import ExerciseRepository

# ------------------------------------------------------------------------------
# edit_exercises
# ------------------------------------------------------------------------------


def test_edit_exercise_raises_if_both_exercise_id_and_identifier_are_none() -> None:
    application = Mock()
    with pytest.raises(
        EditError,
        match="At least one of 'uuid' or 'identifier' must be provided.",
    ):
        edit_exercise(application)


def test_edit_exercise_success_if_at_least_exercise_uuid_is_provided() -> None:
    exercise_uuid = uuid7()
    application = Mock()

    def fake_get_exercise_by_uuid(uuid: UUID) -> Exercise:
        return Exercise(
            uuid=uuid,
            identifier="exercise1",
            prompt="prompt",
            answer="answer",
        )

    application.get_exercise_by_uuid.side_effect = Mock(
        side_effect=fake_get_exercise_by_uuid
    )

    edit_exercise(application, exercise_uuid=exercise_uuid)

    application.get_exercise_by_uuid.assert_called_once()
    application.update_exercise.assert_called_once_with(
        Exercise(
            uuid=exercise_uuid,
            identifier="exercise1",
            prompt="prompt",
            answer="answer",
        )
    )


def test_edit_exercise_success_if_at_least_exercise_identifier_is_provided() -> None:
    original_identifier = "exercise1"
    uuid = uuid7()
    application = Mock()

    def fake_get_exercise_by_identifier(identifier: str) -> Exercise:
        return Exercise(
            uuid=uuid,
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
            uuid=uuid,
            identifier=original_identifier,
            prompt="prompt",
            answer="answer",
        )
    )


def test_edit_exercise_uses_uuid_over_identifier() -> None:
    uuid = uuid7()
    identifier = "identifier"
    application = Mock()
    application.get_exercise_by_uuid = Mock()
    application.get_exercise_by_identifier = Mock()

    edit_exercise(application, exercise_uuid=uuid, identifier=identifier)

    application.get_exercise_by_uuid.assert_called_once()
    application.get_exercise_by_identifier.assert_not_called()


def test_edit_exercise_updates_provided_fields() -> None:
    uuid = uuid7()
    application = Mock()

    def fake_get_exercise_by_uuid(uuid: UUID) -> Exercise:
        return Exercise(
            uuid=uuid,
            identifier="exercise1",
            prompt="prompt",
            answer="answer",
        )

    application.get_exercise_by_uuid.side_effect = Mock(
        side_effect=fake_get_exercise_by_uuid
    )

    edit_exercise(
        application,
        exercise_uuid=uuid,
        new_prompt="new_prompt",
        new_answer="new_answer",
        new_identifier="new_identifier",
    )

    application.get_exercise_by_uuid.assert_called_once()
    application.update_exercise.assert_called_once_with(
        Exercise(
            uuid=uuid,
            identifier="new_identifier",
            prompt="new_prompt",
            answer="new_answer",
        )
    )


# ------------------------------------------------------------------------------
# edit_exercise_env_editor
# ------------------------------------------------------------------------------


def test_edit_ex_env_editor_raises_if_both_exercise_uuid_and_identifier_are_none() -> (
    None
):
    application = Mock()

    with pytest.raises(
        EditError, match="At least one of 'uuid' or 'identifier' must be provided."
    ):
        edit_exercise_env_editor(application)


def test_edit_ex_env_success_if_at_least_exercise_uuid_is_provided() -> None:
    uuid = uuid7()
    application = Mock()
    application.is_valid_idenfifier.return_value = True
    application.identifier_exists.return_value = False

    def fake_get_exercise_by_uuid(uuid: UUID) -> Exercise:
        return Exercise(
            uuid=uuid,
            identifier="exercise1",
            prompt="prompt",
            answer="answer",
        )

    application.get_exercise_by_uuid.side_effect = Mock(
        side_effect=fake_get_exercise_by_uuid
    )

    def fake_identifier_prompt(msg: str, identifier: str | None) -> str | None:
        return "identifier"

    def fake_editor_launcher(
        field_name: str,
        context: dict[str, str],
        initial_field_value: str | None,
    ) -> str | None:
        return field_name

    _edit_exercise_env_editor(
        application,
        fake_identifier_prompt,
        fake_editor_launcher,
        uuid,
    )

    application.get_exercise_by_uuid.assert_called_once()
    application.update_exercise.assert_called_once_with(
        Exercise(
            uuid=uuid,
            identifier="identifier",
            prompt="prompt",
            answer="answer",
        )
    )


def test_edit_ex_env_success_if_at_least_exercise_identifier_is_provided() -> None:
    uuid = uuid7()
    identifier = "identifier"
    application = Mock()

    def fake_get_exercise_by_identifier(identifier: str) -> Exercise:
        return Exercise(
            uuid=uuid,
            identifier=identifier,
            prompt="prompt",
            answer="answer",
        )

    application.get_exercise_by_identifier.side_effect = Mock(
        side_effect=fake_get_exercise_by_identifier
    )

    def fake_identifier_prompt(msg: str, identifier: str | None) -> str | None:
        return "identifier"

    def fake_editor_launcher(
        field_name: str,
        context: dict[str, str],
        initial_field_value: str | None,
    ) -> str | None:
        return field_name

    _edit_exercise_env_editor(
        application,
        fake_identifier_prompt,
        fake_editor_launcher,
        identifier=identifier,
    )

    application.get_exercise_by_identifier.assert_called_once()
    application.update_exercise.assert_called_once_with(
        Exercise(
            uuid=uuid,
            identifier="identifier",
            prompt="prompt",
            answer="answer",
        )
    )


def test_edit_ex_env_uses_uuid_over_identifier() -> None:
    uuid = uuid7()
    identifier = "identifier"
    application = Mock()
    application.is_valid_idenfifier.return_value = True
    application.identifier_exists.return_value = False
    application.get_exercise_by_uuid = Mock()
    application.get_exercise_by_identifier = Mock()

    def fake_identifier_prompt(msg: str, identifier: str | None) -> str | None:
        return "identifier"

    def fake_editor_launcher(
        field_name: str,
        context: dict[str, str],
        initial_field_value: str | None,
    ) -> str | None:
        return field_name

    _edit_exercise_env_editor(
        application,
        fake_identifier_prompt,
        fake_editor_launcher,
        exercise_uuid=uuid,
        identifier=identifier,
    )

    application.get_exercise_by_uuid.assert_called_once()
    application.get_exercise_by_identifier.assert_not_called()


def test_edit_ex_env_updates_provided_fields() -> None:
    uuid = uuid7()
    application = Mock()
    application.is_valid_idenfifier.return_value = True
    application.identifier_exists.return_value = False

    def fake_get_exercise_by_uuid(uuid: UUID) -> Exercise:
        return Exercise(
            uuid=uuid,
            identifier="old_identifier",
            prompt="old_prompt",
            answer="old_answer",
        )

    application.get_exercise_by_uuid.side_effect = Mock(
        side_effect=fake_get_exercise_by_uuid
    )

    def fake_identifier_prompt(msg: str, identifier: str | None) -> str | None:
        return "new_identifier"

    def fake_editor_launcher(
        field_name: str,
        context: dict[str, str],
        initial_field_value: str | None,
    ) -> str | None:
        return f"new {field_name}"

    _edit_exercise_env_editor(
        application,
        fake_identifier_prompt,
        fake_editor_launcher,
        uuid,
    )

    application.get_exercise_by_uuid.assert_called_once()
    application.update_exercise.assert_called_once_with(
        Exercise(
            uuid=uuid,
            identifier="new_identifier",
            prompt="new prompt",
            answer="new answer",
        )
    )


def test_edit_exercise_in_env_editor_raises_if_identifier_already_exists() -> None:

    application = ExerciseApplication(
        ExerciseRepository(initialize()),
    )
    exercise_uuid = application.add_exercise(
        prompt="prompt1",
        answer="answer1",
        identifier="exercise1",
    )

    exercise2_uuid = application.add_exercise(
        prompt="prompt2", answer="answer2", identifier="exercise2"
    )

    assert exercise_uuid is not None
    assert exercise2_uuid is not None

    editor_launcher = Mock()

    def fake_identifier_prompt(msg: str, identifier: str | None) -> str | None:
        return "exercise2"

    identifier_prompt = Mock(side_effect=fake_identifier_prompt)

    with pytest.raises(
        EditError,
        match="'exercise2' already exists.",
    ):
        _edit_exercise_env_editor(
            application,
            identifier_prompt,
            editor_launcher,
            exercise_uuid=exercise_uuid,
        )


def test_edit_exercise_in_env_editor_raises_if_identifier_is_invalid() -> None:

    application = ExerciseApplication(
        ExerciseRepository(initialize()),
    )
    exercise_uuid = application.add_exercise(
        prompt="prompt1",
        answer="answer1",
        identifier="exercise1",
    )

    assert exercise_uuid is not None

    editor_launcher = Mock()

    def fake_identifier_prompt(msg: str, identifier: str | None) -> str | None:
        return "invalid identifier"

    with pytest.raises(
        EditError,
        match="'invalid identifier' is an invalid identifier.",
    ):
        _edit_exercise_env_editor(
            application,
            fake_identifier_prompt,
            editor_launcher,
            exercise_uuid=exercise_uuid,
        )


def test_edit_exercise_in_env_editor_do_not_raise_if_same_identifier_provided() -> None:
    application = ExerciseApplication(
        ExerciseRepository(initialize()),
    )
    exercise_uuid = application.add_exercise(
        prompt="prompt1",
        answer="answer1",
        identifier="exercise1",
    )

    assert exercise_uuid is not None

    def fake_editor_launcher(
        field_name: str,
        context: dict[str, str],
        field_previous_content: str | None,
    ) -> str | None:
        return "some content"

    def fake_identifier_prompt(msg: str, identifier: str | None) -> str | None:
        return "exercise1"

    _edit_exercise_env_editor(
        application,
        fake_identifier_prompt,
        fake_editor_launcher,
        exercise_uuid=exercise_uuid,
    )
