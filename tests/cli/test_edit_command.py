from unittest.mock import Mock

import pytest

from exercise_library.application import ExerciseApplication, InvalidExerciseError
from exercise_library.cli.edit_command import (
    EditError,
    _edit_exercise_env_editor,
    edit_exercise,
)

# ------------------------------------------------------------------------------
# edit_exercise
# ------------------------------------------------------------------------------


def test_edit_exercise_raises_for_unknown_selector(
    application: ExerciseApplication,
) -> None:
    with pytest.raises(InvalidExerciseError, match="No exercise found"):
        edit_exercise(application, selector="missing")


def test_edit_exercise_with_uuid_selector(
    application: ExerciseApplication,
) -> None:
    exercise_uuid = application.add_exercise(
        prompt="prompt", answer="answer", identifier="exercise1"
    )

    edit_exercise(application, selector=str(exercise_uuid))

    exercise = application.get_exercise_by_uuid(exercise_uuid)
    assert exercise.identifier == "exercise1"
    assert exercise.prompt == "prompt"
    assert exercise.answer == "answer"


def test_edit_exercise_with_identifier_selector(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(prompt="prompt", answer="answer", identifier="exercise1")

    edit_exercise(application, selector="exercise1", new_prompt="new prompt")

    exercise = application.get_exercise_by_identifier("exercise1")
    assert exercise.prompt == "new prompt"
    assert exercise.answer == "answer"


def test_edit_exercise_updates_provided_fields(
    application: ExerciseApplication,
) -> None:
    exercise_uuid = application.add_exercise(
        prompt="prompt", answer="answer", identifier="exercise1"
    )

    edit_exercise(
        application,
        selector="exercise1",
        new_prompt="new_prompt",
        new_answer="new_answer",
        new_identifier="new_identifier",
    )

    exercise = application.get_exercise_by_uuid(exercise_uuid)
    assert exercise.identifier == "new_identifier"
    assert exercise.prompt == "new_prompt"
    assert exercise.answer == "new_answer"


# ------------------------------------------------------------------------------
# _edit_exercise_env_editor
# ------------------------------------------------------------------------------


def _fake_identifier_prompt(msg: str, identifier: str | None) -> str | None:
    return "identifier"


def _fake_editor_launcher(
    field_name: str,
    context: dict[str, str],
    initial_field_value: str | None,
) -> str | None:
    return f"new {field_name}"


def test_edit_ex_env_editor_raises_for_unknown_selector(
    application: ExerciseApplication,
) -> None:
    with pytest.raises(InvalidExerciseError, match="No exercise found"):
        _edit_exercise_env_editor(
            application,
            Mock(),
            Mock(),
            selector="missing",
        )


def test_edit_ex_env_editor_with_uuid_selector(
    application: ExerciseApplication,
) -> None:
    exercise_uuid = application.add_exercise(
        prompt="prompt", answer="answer", identifier="exercise1"
    )

    _edit_exercise_env_editor(
        application,
        _fake_identifier_prompt,
        _fake_editor_launcher,
        selector=str(exercise_uuid),
    )

    exercise = application.get_exercise_by_uuid(exercise_uuid)
    assert exercise.identifier == "identifier"
    assert exercise.prompt == "new prompt"
    assert exercise.answer == "new answer"


def test_edit_ex_env_editor_with_identifier_selector(
    application: ExerciseApplication,
) -> None:
    application.add_exercise(prompt="prompt", answer="answer", identifier="exercise1")

    _edit_exercise_env_editor(
        application,
        _fake_identifier_prompt,
        _fake_editor_launcher,
        selector="exercise1",
    )

    exercise = application.get_exercise_by_identifier("identifier")
    assert exercise.prompt == "new prompt"
    assert exercise.answer == "new answer"


def test_edit_exercise_in_env_editor_raises_if_identifier_already_exists(
    application: ExerciseApplication,
) -> None:
    exercise_uuid = application.add_exercise(
        prompt="prompt1",
        answer="answer1",
        identifier="exercise1",
    )

    application.add_exercise(prompt="prompt2", answer="answer2", identifier="exercise2")

    assert exercise_uuid is not None

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
            selector=str(exercise_uuid),
        )


def test_edit_exercise_in_env_editor_raises_if_identifier_is_invalid(
    application: ExerciseApplication,
) -> None:
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
            selector=str(exercise_uuid),
        )


def test_edit_exercise_in_env_editor_do_not_raise_if_same_identifier_provided(
    application: ExerciseApplication,
) -> None:
    exercise_uuid = application.add_exercise(
        prompt="prompt1",
        answer="answer1",
        identifier="exercise1",
    )

    assert exercise_uuid is not None

    def fake_identifier_prompt(msg: str, identifier: str | None) -> str | None:
        return "exercise1"

    _edit_exercise_env_editor(
        application,
        fake_identifier_prompt,
        _fake_editor_launcher,
        selector=str(exercise_uuid),
    )
