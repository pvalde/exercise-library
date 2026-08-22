import argparse
import os
import subprocess
from typing import Never
from unittest.mock import Mock, call

import pytest

import exercise_library.cli as cli
from exercise_library.models import Exercise


def test_edit_in_editor_uses_visual_over_editor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VISUAL", "visual-editor")
    monkeypatch.setenv("EDITOR", "other-editor")

    fake_run = Mock()
    monkeypatch.setattr(cli.subprocess, "run", fake_run)  # type: ignore[attr-defined]

    cli.edit_in_editor("prompt")

    command = fake_run.call_args.args[0]

    assert command[0] == "visual-editor"


def test_edit_in_editor_falls_back_to_editor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.setenv("EDITOR", "my-editor")

    fake_run = Mock()

    monkeypatch.setattr(cli.subprocess, "run", fake_run)  # type: ignore[attr-defined]

    cli.edit_in_editor("answer")

    command = fake_run.call_args.args[0]

    assert command[0] == "my-editor"


def test_edit_in_editor_supports_editor_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.setenv("EDITOR", "my-editor --wait --foo")

    fake_run = Mock()
    monkeypatch.setattr(cli.subprocess, "run", fake_run)  # type: ignore[attr-defined]

    cli.edit_in_editor("prompt")

    command = fake_run.call_args.args[0]

    assert command[:-1] == [
        "my-editor",
        "--wait",
        "--foo",
    ]


def test_edit_in_editor_exits_when_no_editor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.delenv("EDITOR", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        cli.edit_in_editor("prompt")

    assert exc_info.value.code == 1


def test_edit_in_editor_removes_generated_comments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> None:
        filename = command[-1]

        with open(filename, "a", encoding="utf-8") as f:
            f.write("# My exercise\n\n")
            f.write("This is **Markdown**.\n")

    fake_run = Mock(side_effect=fake_editor)
    monkeypatch.setattr(cli.subprocess, "run", fake_run)  # type: ignore[attr-defined]

    result = cli.edit_in_editor("prompt")

    assert result == "# My exercise\n\nThis is **Markdown**."


def test_edit_in_editor_preserves_other_html_comments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> None:
        filename = command[-1]

        with open(filename, "a", encoding="utf-8") as f:
            f.write("<!-- Keep this comment -->\n")
            f.write("Some content\n")

    fake_run = Mock(side_effect=fake_editor)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)  # type: ignore[attr-defined]

    result = cli.edit_in_editor("prompt")

    assert result == "<!-- Keep this comment -->\nSome content"


def test_edit_in_editor_strips_surrounding_whitespace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> None:
        filename = command[-1]

        with open(filename, "a", encoding="utf-8") as f:
            f.write("\n\n  Some content  \n\n")

    fake_run = Mock(side_effect=fake_editor)
    monkeypatch.setattr(cli.subprocess, "run", fake_run)  # type: ignore[attr-defined]

    result = cli.edit_in_editor("prompt")

    assert result == "Some content"


def test_edit_in_editor_returns_empty_on_editor_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> Never:
        raise subprocess.CalledProcessError(1, command)

    fake_run = Mock(side_effect=fake_editor)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)  # type: ignore[attr-defined]

    result = cli.edit_in_editor("prompt")

    assert result == ""


def test_edit_in_editor_deletes_temporary_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> None:
        filename = command[-1]

        with open(filename, "a", encoding="utf-8") as f:
            f.write("content\n")

    fake_run = Mock(side_effect=fake_editor)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)  # type: ignore[attr-defined]

    cli.edit_in_editor("prompt")

    file = fake_run.call_args.args[0][-1]
    assert not os.path.exists(file)


def test_edit_in_editor_deletes_file_when_editor_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> Never:
        raise subprocess.CalledProcessError(1, command)

    fake_run = Mock(side_effect=fake_editor)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)  # type: ignore[attr-defined]

    result = cli.edit_in_editor("prompt")

    assert result == ""

    file = fake_run.call_args.args[0][-1]
    assert not os.path.exists(file)


def test_create_parser_requires_command() -> None:
    parser = cli.create_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_create_parser_parses_add_arguments() -> None:
    parser = cli.create_parser()

    args = parser.parse_args(["add", "prompt", "answer"])

    assert args.command == "add"
    assert args.prompt == "prompt"
    assert args.answer == "answer"
    assert args.interactive is False


def test_create_parser_parses_interactive_flag() -> None:
    parser = cli.create_parser()

    args = parser.parse_args(["add", "-i"])

    assert args.command == "add"
    assert args.prompt is None
    assert args.answer is None
    assert args.interactive is True


def test_create_parser_accepts_long_interactive_flag() -> None:
    parser = cli.create_parser()

    args = parser.parse_args(["add", "--interactive"])

    assert args.interactive is True


def test_create_parser_parses_list_command() -> None:
    parser = cli.create_parser()

    args = parser.parse_args(["list"])

    assert args.command == "list"


def test_add_exercise_requires_prompt_and_answer(
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = Mock()
    args = argparse.Namespace(
        interactive=False,
        prompt="",
        answer="answer",
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.add_exercise(repo, args)

    assert exc_info.value.code == 1
    assert "prompt and answer are required" in capsys.readouterr().out
    repo.add.assert_not_called()


def test_add_exercise_requires_answer(capsys: pytest.CaptureFixture[str]) -> None:
    repo = Mock()
    args = argparse.Namespace(
        interactive=False,
        prompt="prompt",
        answer=None,
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.add_exercise(repo, args)

    assert exc_info.value.code == 1
    assert "prompt and answer are required" in capsys.readouterr().out
    repo.add.assert_not_called()


def test_add_exercise_adds_exercise() -> None:
    repo = Mock()
    repo.add.return_value = 1

    args = argparse.Namespace(
        interactive=False,
        prompt="What is Python?",
        answer="A programming language.",
    )

    cli.add_exercise(repo, args)

    repo.add.assert_called_once()
    exercise = repo.add.call_args.args[0]

    assert isinstance(exercise, Exercise)
    assert exercise.prompt == "What is Python?"
    assert exercise.answer == "A programming language."


def test_add_exercise_prints_success_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = Mock()
    repo.add.return_value = 1

    args = argparse.Namespace(
        interactive=False,
        prompt="prompt",
        answer="answer",
    )

    cli.add_exercise(repo, args)

    output = capsys.readouterr().out

    assert "Successfully added exercise with ID 1" in output


def test_add_exercise_rejects_empty_interactive_prompt(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = Mock()
    args = argparse.Namespace(
        interactive=True,
        prompt=None,
        answer=None,
    )

    monkeypatch.setattr(
        cli,
        "edit_in_editor",
        Mock(side_effect=["", "answer"]),
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.add_exercise(repo, args)

    assert exc_info.value.code == 1
    assert "Prompt and answer cannot be empty." in capsys.readouterr().out
    repo.add.assert_not_called()


def test_add_exercise_rejects_empty_interactive_answer(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = Mock()
    args = argparse.Namespace(
        interactive=True,
        prompt=None,
        answer=None,
    )

    monkeypatch.setattr(
        cli,
        "edit_in_editor",
        Mock(side_effect=["prompt", ""]),
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.add_exercise(repo, args)

    assert exc_info.value.code == 1
    assert "Prompt and answer cannot be empty." in capsys.readouterr().out
    repo.add.assert_not_called()


def test_add_exercise_interactive_opens_editor_for_prompt_and_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = Mock()
    repo.add.return_value = 1

    args = argparse.Namespace(
        interactive=True,
        prompt=None,
        answer=None,
    )

    fake_editor = Mock(side_effect=["prompt from editor", "answer from editor"])
    monkeypatch.setattr(cli, "edit_in_editor", fake_editor)

    cli.add_exercise(repo, args)

    # check edit_in_editor was called twice in the correct order
    assert fake_editor.call_args_list == [
        call("prompt"),
        call("answer"),
    ]

    exercise = repo.add.call_args.args[0]
    assert exercise.prompt == "prompt from editor"
    assert exercise.answer == "answer from editor"


def test_add_exercise_interactive_prints_editor_messages(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = Mock()
    repo.add.return_value = 1

    args = argparse.Namespace(
        interactive=True,
        prompt=None,
        answer=None,
    )

    monkeypatch.setattr(
        cli,
        "edit_in_editor",
        Mock(side_effect=["prompt", "answer"]),
    )

    cli.add_exercise(repo, args)

    output = capsys.readouterr().out

    assert "Opening editor for prompt..." in output
    assert "Opening editor for answer..." in output


def test_list_exercises_prints_no_exercises_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = Mock()
    repo.list_all.return_value = []

    cli.list_exercises(repo)

    repo.list_all.assert_called_once()
    assert capsys.readouterr().out == "No exercises found.\n"


def test_list_exercises_prints_exercises(
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = Mock()
    repo.list_all.return_value = [
        Exercise(
            id=1,
            prompt="What is Python?",
            answer="A programming language.",
        ),
        Exercise(
            id=2,
            prompt="What is pytest?",
            answer="A testing framework.",
        ),
    ]

    cli.list_exercises(repo)

    output = capsys.readouterr().out

    assert "[1]" in output
    assert "Prompt:\nWhat is Python?" in output
    assert "Answer:\nA programming language." in output

    assert "[2]" in output
    assert "Prompt:\nWhat is pytest?" in output
    assert "Answer:\nA testing framework." in output

    assert output.count("-" * 40) == 2


def test_list_exercises_preserves_multiline_content(
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = Mock()
    repo.list_all.return_value = [
        Exercise(
            id=1,
            prompt="Line one\nLine two",
            answer="Answer one\nAnswer two",
        )
    ]

    cli.list_exercises(repo)

    output = capsys.readouterr().out

    assert "Prompt:\nLine one\nLine two" in output
    assert "Answer:\nAnswer one\nAnswer two" in output


def test_main_adds_exercise(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_repo = Mock()

    parser = Mock()
    parser.parse_args.return_value = argparse.Namespace(
        command="add",
        prompt="prompt",
        answer="answer",
        interactive=False,
    )

    initialize = Mock(return_value="connection")
    repository = Mock(return_value=fake_repo)
    add_exercise = Mock()

    monkeypatch.setattr(cli, "create_parser", Mock(return_value=parser))
    monkeypatch.setattr(cli, "initialize", initialize)
    monkeypatch.setattr(cli, "ExerciseRepository", repository)
    monkeypatch.setattr(cli, "add_exercise", add_exercise)

    cli.main()

    initialize.assert_called_once()
    repository.assert_called_once_with("connection")
    add_exercise.assert_called_once_with(
        fake_repo,
        parser.parse_args.return_value,
    )


def test_main_lists_exercises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_repo = Mock()

    parser = Mock()
    parser.parse_args.return_value = argparse.Namespace(command="list")
    list_exercises = Mock()
    initialize = Mock(return_value="connection")
    ExerciseRepository = Mock(return_value=fake_repo)

    monkeypatch.setattr(cli, "create_parser", lambda: parser)
    monkeypatch.setattr(cli, "initialize", initialize)
    monkeypatch.setattr(
        cli,
        "ExerciseRepository",
        ExerciseRepository,
    )
    monkeypatch.setattr(cli, "list_exercises", list_exercises)

    cli.main()

    initialize.assert_called_once()
    ExerciseRepository.assert_called_once_with("connection")
    list_exercises.assert_called_once_with(fake_repo)
