import argparse
from unittest.mock import Mock, call

import pytest

from exercise_library.application import ExerciseApplication
from exercise_library.cli.add_command import add_exercise


def test_add_exercise_requires_prompt_and_answer(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = argparse.Namespace(
        interactive=False,
        prompt="",
        answer="answer",
        identifier=None,
    )

    with pytest.raises(SystemExit) as exc_info:
        add_exercise(application, args)

    assert exc_info.value.code == 1
    assert "prompt and answer are required" in capsys.readouterr().out


def test_add_exercise_requires_answer(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = argparse.Namespace(
        interactive=False,
        prompt="prompt",
        answer=None,
        identifier=None,
    )

    with pytest.raises(SystemExit) as exc_info:
        add_exercise(application, args)

    assert exc_info.value.code == 1
    assert "prompt and answer are required" in capsys.readouterr().out


def test_add_exercise_adds_exercise(
    application: ExerciseApplication,
) -> None:
    args = argparse.Namespace(
        interactive=False,
        prompt="What is Python?",
        answer="A programming language.",
        identifier="book::chapter01::exercise05",
    )

    add_exercise(application, args)

    exercises = application.repository.browse()

    assert len(exercises) == 1
    assert exercises[0].prompt == "What is Python?"
    assert exercises[0].answer == "A programming language."
    assert exercises[0].identifier == "book::chapter01::exercise05"


def test_add_exercise_prints_success_message(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = argparse.Namespace(
        interactive=False,
        identifier=None,
        prompt="prompt",
        answer="answer",
    )

    add_exercise(application, args)

    output = capsys.readouterr().out

    assert "Successfully added exercise with ID" in output


def test_add_exercise_rejects_empty_interactive_prompt(
    application: ExerciseApplication,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = argparse.Namespace(
        interactive=True,
        identifier=None,
        prompt=None,
        answer=None,
    )

    monkeypatch.setattr(
        "exercise_library.cli.add_command.edit_in_editor",
        Mock(side_effect=["", "answer"]),
    )

    monkeypatch.setattr(
        "builtins.input",
        Mock(return_value=""),
    )

    with pytest.raises(SystemExit) as exc_info:
        add_exercise(application, args)

    assert exc_info.value.code == 1
    assert "Prompt and answer cannot be empty." in capsys.readouterr().out


def test_add_exercise_rejects_empty_interactive_answer(
    application: ExerciseApplication,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = argparse.Namespace(
        interactive=True,
        identifier=None,
        prompt=None,
        answer=None,
    )

    monkeypatch.setattr(
        "exercise_library.cli.add_command.edit_in_editor",
        Mock(side_effect=["prompt", ""]),
    )

    monkeypatch.setattr(
        "builtins.input",
        Mock(return_value=""),
    )

    with pytest.raises(SystemExit) as exc_info:
        add_exercise(application, args)

    assert exc_info.value.code == 1
    assert "Prompt and answer cannot be empty." in capsys.readouterr().out


def test_add_exercise_interactive_opens_editor_for_prompt_and_answer(
    application: ExerciseApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_editor = Mock(
        side_effect=[
            "prompt from editor",
            "answer from editor",
        ]
    )

    monkeypatch.setattr(
        "exercise_library.cli.add_command.edit_in_editor",
        fake_editor,
    )

    monkeypatch.setattr(
        "builtins.input",
        Mock(return_value=""),
    )

    args = argparse.Namespace(
        interactive=True,
        identifier=None,
        prompt=None,
        answer=None,
    )

    add_exercise(application, args)

    assert fake_editor.call_args_list == [
        call("prompt"),
        call("answer"),
    ]

    exercises = application.repository.browse()

    assert len(exercises) == 1
    assert exercises[0].prompt == "prompt from editor"
    assert exercises[0].answer == "answer from editor"


def test_add_exercise_interactive_asks_for_identifier(
    application: ExerciseApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exercise_library.cli.add_command.edit_in_editor",
        Mock(side_effect=["prompt", "answer"]),
    )

    monkeypatch.setattr(
        "builtins.input",
        Mock(return_value="book::chapter01::exercise05"),
    )

    args = argparse.Namespace(
        interactive=True,
        identifier=None,
        prompt=None,
        answer=None,
    )

    add_exercise(application, args)

    exercises = application.repository.browse()

    assert len(exercises) == 1
    assert exercises[0].prompt == "prompt"
    assert exercises[0].answer == "answer"
    assert exercises[0].identifier == "book::chapter01::exercise05"


def test_add_exercise_interactive_uses_provided_identifier(
    application: ExerciseApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exercise_library.cli.add_command.edit_in_editor",
        Mock(side_effect=["prompt", "answer"]),
    )

    fake_input = Mock()
    monkeypatch.setattr(
        "builtins.input",
        fake_input,
    )

    args = argparse.Namespace(
        interactive=True,
        prompt=None,
        answer=None,
        identifier="book::chapter01::exercise05",
    )

    add_exercise(application, args)

    exercises = application.repository.browse()

    assert len(exercises) == 1
    assert exercises[0].identifier == "book::chapter01::exercise05"

    fake_input.assert_not_called()


def test_add_exercise_interactive_allows_empty_identifier(
    application: ExerciseApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exercise_library.cli.add_command.edit_in_editor",
        Mock(side_effect=["prompt", "answer"]),
    )

    monkeypatch.setattr(
        "builtins.input",
        Mock(return_value="   "),
    )

    args = argparse.Namespace(
        interactive=True,
        prompt=None,
        answer=None,
        identifier=None,
    )

    add_exercise(application, args)

    exercises = application.repository.browse()

    assert len(exercises) == 1
    assert exercises[0].identifier is None


def test_add_exercise_interactive_prints_editor_messages(
    application: ExerciseApplication,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "exercise_library.cli.add_command.edit_in_editor",
        Mock(side_effect=["prompt", "answer"]),
    )

    monkeypatch.setattr(
        "builtins.input",
        Mock(return_value=""),
    )

    args = argparse.Namespace(
        interactive=True,
        identifier=None,
        prompt=None,
        answer=None,
    )

    add_exercise(application, args)

    output = capsys.readouterr().out

    assert "Opening editor for prompt..." in output
    assert "Opening editor for answer..." in output


def test_add_exercise_rejects_invalid_identifier(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = argparse.Namespace(
        interactive=False,
        prompt="What is Python?",
        answer="A programming language.",
        identifier="book:chapter01",
    )

    with pytest.raises(SystemExit) as exc_info:
        add_exercise(application, args)

    assert exc_info.value.code == 1

    output = capsys.readouterr().out

    assert (
        "Error: Identifier can only contain letters, numbers, "
        "dash, underscore, and '::' separators."
    ) in output

    assert application.repository.browse() == []
