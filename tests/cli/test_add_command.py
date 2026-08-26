import argparse
from unittest.mock import Mock, call
from uuid import uuid7

from exercise_library.cli.add_command import _add_exercise


def test_add_exercise_requires_prompt_and_answer() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    editor = Mock()
    identifier_prompt = Mock()

    args = argparse.Namespace(interactive=False, prompt="", answer="answer")
    assert _add_exercise(application, args, editor, identifier_prompt) is False

    args = argparse.Namespace(interactive=False, prompt="prompt", answer="")
    assert _add_exercise(application, args, editor, identifier_prompt) is False

    args = argparse.Namespace(interactive=False, prompt="", answer="")
    assert _add_exercise(application, args, editor, identifier_prompt) is False


def test_add_exercise_interactive_requires_prompt_and_answer() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    identifier_prompt = Mock(return_value=None)
    args = argparse.Namespace(interactive=True, identifier=None)

    def fake_editor(field_name: str, context: dict[str, str]) -> str | None:
        return None

    editor = Mock(side_effect=fake_editor)
    assert _add_exercise(application, args, editor, identifier_prompt) is False

    def fake_editor2(field_name: str, context: dict[str, str]) -> str | None:
        if field_name == "prompt":
            return None
        else:
            return "answer"

    editor = Mock(side_effect=fake_editor2)
    assert _add_exercise(application, args, editor, identifier_prompt) is False

    def fake_editor3(field_name: str, context: dict[str, str]) -> str | None:
        if field_name == "answer":
            return None
        else:
            return "prompt"

    editor = Mock(side_effect=fake_editor3)
    assert _add_exercise(application, args, editor, identifier_prompt) is False


def test_add_exercise_interactive_returns_if_prompt_is_not_provided() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    identifier_prompt = Mock(return_value=None)
    args = argparse.Namespace(interactive=True, identifier=None)

    def fake_editor(field_name: str, context: dict[str, str]) -> str | None:
        return None

    editor = Mock(side_effect=fake_editor)
    assert _add_exercise(application, args, editor, identifier_prompt) is False
    editor.assert_called_once()
    assert application.add_exercise.call_count == 0


def test_add_exercise_calls_add_exercise() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    editor = Mock()
    identifier_prompt = Mock()

    args = argparse.Namespace(
        interactive=False,
        prompt="What is Python?",
        answer="A programming language.",
        identifier="book::chapter01::exercise05",
    )

    assert _add_exercise(application, args, editor, identifier_prompt) is True
    application.add_exercise.assert_called_once()


def test_add_exercise_interactive_calls_add_exercise() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    identifier_prompt = Mock(return_value=None)
    args = argparse.Namespace(interactive=True, identifier=None)

    def fake_editor(field_name: str, context: dict[str, str]) -> str | None:
        return "some content"

    editor = Mock(side_effect=fake_editor)

    assert _add_exercise(application, args, editor, identifier_prompt) is True
    application.add_exercise.assert_called_once()


def test_add_exercise_interactive_opens_editor_for_prompt_and_answer() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    identifier_prompt = Mock(return_value=None)
    args = argparse.Namespace(interactive=True, identifier=None)

    def fake_editor(field_name: str, context: dict[str, str]) -> str | None:
        return "some content"

    editor = Mock(side_effect=fake_editor)

    assert _add_exercise(application, args, editor, identifier_prompt) is True
    editor.assert_called()
    assert editor.call_count == 2


def test_add_exercise_interactive_opens_identifier_prompt() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    identifier_prompt = Mock(return_value=None)
    args = argparse.Namespace(interactive=True, identifier=None)

    def fake_editor(field_name: str, context: dict[str, str]) -> str | None:
        return "some content"

    editor = Mock(side_effect=fake_editor)

    assert _add_exercise(application, args, editor, identifier_prompt) is True
    identifier_prompt.assert_called_once()


def test_add_exercise_interactive_uses_provided_identifier() -> None:
    application = Mock()
    application.add_exercise.return_value = uuid7()
    editor = Mock(return_value="some content")
    identifier_prompt = Mock(return_value=None)
    args = argparse.Namespace(
        interactive=True, identifier="book::chapter01::exercise05"
    )

    assert _add_exercise(application, args, editor, identifier_prompt) is True
    assert identifier_prompt.call_count == 0
    assert application.add_exercise.call_args_list == [
        call(
            prompt="some content",
            answer="some content",
            identifier="book::chapter01::exercise05",
        ),
    ]


def test_add_exercise_interactive_allows_empty_identifier() -> None:
    args = argparse.Namespace(
        interactive=True,
        prompt=None,
        answer=None,
        identifier=None,
    )

    application = Mock()
    application.add_exercise.return_value = uuid7()
    editor = Mock(return_value="some content")
    identifier_prompt = Mock(return_value=None)

    assert _add_exercise(application, args, editor, identifier_prompt) is True
    application.add_exercise.assert_called_once()
