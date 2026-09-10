from unittest.mock import Mock
from uuid import uuid7

import pytest

from exercise_library.cli.add_command import (
    AddInteractiveError,
    _add_exercise_in_env_editor,
    add_exercise,
)

# ------------------------------------------------------------------------------
# add_exercise_in_env_editor
# ------------------------------------------------------------------------------


def test_add_exercise_in_env_editor_raises_if_prompt_and_answer_are_none() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    identifier_prompt = Mock(return_value=None)

    def fake_editor_launcher(
        field_name: str,
        context: dict[str, str],
    ) -> str | None:
        return None

    editor_launcher = Mock(side_effect=fake_editor_launcher)

    with pytest.raises(AddInteractiveError, match="Prompt cannot be empty."):
        _add_exercise_in_env_editor(
            application,
            editor_launcher,
            identifier_prompt,
        )

    editor_launcher.assert_called_once()

    def fake_editor_launcher2(
        field_name: str,
        context: dict[str, str],
    ) -> str | None:
        if field_name == "answer":
            return None
        else:
            return "prompt"

    editor_launcher2 = Mock(side_effect=fake_editor_launcher2)
    with pytest.raises(AddInteractiveError, match="Answer cannot be empty."):
        _add_exercise_in_env_editor(
            application,
            editor_launcher2,
            identifier_prompt,
        )

    assert editor_launcher2.call_count == 2


def test_add_exercise_in_env_editor_raises_if_prompt_and_answer_are_empty_str() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    identifier_prompt = Mock(return_value=None)

    def fake_editor_launcher(
        field_name: str,
        context: dict[str, str],
    ) -> str | None:
        return ""

    editor_launcher = Mock(side_effect=fake_editor_launcher)

    with pytest.raises(AddInteractiveError, match="Prompt cannot be empty."):
        _add_exercise_in_env_editor(
            application,
            editor_launcher,
            identifier_prompt,
        )

    editor_launcher.assert_called_once()

    def fake_editor_launcher2(
        field_name: str,
        context: dict[str, str],
    ) -> str | None:
        if field_name == "answer":
            return ""
        else:
            return "prompt"

    editor_launcher2 = Mock(side_effect=fake_editor_launcher2)
    with pytest.raises(AddInteractiveError, match="Answer cannot be empty."):
        _add_exercise_in_env_editor(
            application,
            editor_launcher2,
            identifier_prompt,
        )

    assert editor_launcher2.call_count == 2


def test_add_exercise_in_env_editor_calls_add_exercise() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    identifier_prompt = Mock(return_value=None)

    def fake_editor_launcher(
        field_name: str,
        context: dict[str, str],
    ) -> str | None:
        return "some content"

    editor_launcher = Mock(side_effect=fake_editor_launcher)

    _add_exercise_in_env_editor(application, editor_launcher, identifier_prompt)

    identifier_prompt.assert_called_once()
    application.add_exercise.assert_called_once()
    application.add_exercise.assert_called_with(
        prompt="some content",
        answer="some content",
        identifier=None,
    )


def test_add_exercise_in_env_editor_calls_add_exercise_with_identifier() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    application.is_valid_identifier.return_value = True
    application.identifier_exists.return_value = False
    identifier_prompt = Mock(return_value="identifier")

    def fake_editor_launcher(
        field_name: str,
        context: dict[str, str],
    ) -> str | None:
        return "some content"

    editor_launcher = Mock(side_effect=fake_editor_launcher)

    _add_exercise_in_env_editor(application, editor_launcher, identifier_prompt)

    identifier_prompt.assert_called_once()
    application.add_exercise.assert_called_once()
    application.add_exercise.assert_called_with(
        prompt="some content",
        answer="some content",
        identifier="identifier",
    )


def test_add_exercise_in_env_editor_opens_editor_for_prompt_and_answer() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    identifier_prompt = Mock(return_value=None)

    def fake_editor_launcher(field_name: str, context: dict[str, str]) -> str | None:
        return "some content"

    editor_launcher = Mock(side_effect=fake_editor_launcher)

    _add_exercise_in_env_editor(application, editor_launcher, identifier_prompt)
    editor_launcher.assert_called()
    assert editor_launcher.call_count == 2


def test_add_exercise_in_env_editor_opens_identifier_prompt() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    identifier_prompt = Mock(return_value=None)

    def fake_editor_launcher(field_name: str, context: dict[str, str]) -> str | None:
        return "some content"

    editor_launcher = Mock(side_effect=fake_editor_launcher)

    _add_exercise_in_env_editor(application, editor_launcher, identifier_prompt)
    identifier_prompt.assert_called_once()


def test_add_exercise_in_env_editor_allows_empty_identifier() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    editor_launcher = Mock(return_value="some content")
    identifier_prompt = Mock(return_value=None)

    _add_exercise_in_env_editor(application, editor_launcher, identifier_prompt)
    application.add_exercise.assert_called_once()


def test_add_exercise_in_env_editor_raises_if_identifier_already_exists() -> None:
    application = Mock()
    application.is_valid_identifier.return_value = True
    application.identifier_exists.return_value = True

    editor_launcher = Mock()
    identifier_prompt = Mock(return_value="valid-identifier")

    with pytest.raises(
        AddInteractiveError,
        match="'valid-identifier' already exists.",
    ):
        _add_exercise_in_env_editor(application, editor_launcher, identifier_prompt)


def test_add_exercise_in_env_editor_raises_if_identifier_is_invalid() -> None:
    application = Mock()
    application.is_valid_identifier.return_value = False

    editor_launcher = Mock()
    identifier_prompt = Mock(return_value="Invalid identifier")

    with pytest.raises(
        AddInteractiveError,
        match="'Invalid identifier' is an invalid identifier.",
    ):
        _add_exercise_in_env_editor(application, editor_launcher, identifier_prompt)


# ------------------------------------------------------------------------------
# add_exercise_in_env_editor
# ------------------------------------------------------------------------------


def test_add_exercise_calls_add_exercise() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()

    add_exercise(application, "identifier", "prompt", "answer")
    application.add_exercise.assert_called_once()
    application.add_exercise.assert_called_once_with(
        prompt="prompt",
        answer="answer",
        identifier="identifier",
    )
