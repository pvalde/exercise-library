import argparse
import os
import subprocess
from typing import Never
from unittest.mock import Mock, call

import pytest

import exercise_library.cli as cli
from exercise_library.application import ExerciseApplication
from exercise_library.database import initialize
from exercise_library.models import Exercise
from exercise_library.repository import ExerciseRepository


@pytest.fixture
def application() -> ExerciseApplication:
    connection = initialize()
    repository = ExerciseRepository(connection)
    return ExerciseApplication(repository)


def test_edit_in_editor_uses_visual_over_editor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VISUAL", "visual-editor")
    monkeypatch.setenv("EDITOR", "other-editor")

    fake_run = Mock()
    monkeypatch.setattr(
        "exercise_library.cli.subprocess.run",
        fake_run,
    )

    cli.edit_in_editor("prompt")

    command = fake_run.call_args.args[0]

    assert command[0] == "visual-editor"


def test_edit_in_editor_falls_back_to_editor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.setenv("EDITOR", "my-editor")

    fake_run = Mock()
    monkeypatch.setattr(
        "exercise_library.cli.subprocess.run",
        fake_run,
    )

    cli.edit_in_editor("answer")

    command = fake_run.call_args.args[0]

    assert command[0] == "my-editor"


def test_edit_in_editor_supports_editor_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.setenv("EDITOR", "my-editor --wait --foo")

    fake_run = Mock()
    monkeypatch.setattr(
        "exercise_library.cli.subprocess.run",
        fake_run,
    )

    cli.edit_in_editor("prompt")

    command = fake_run.call_args.args[0]

    assert command[:-1] == [
        "my-editor",
        "--wait",
        "--foo",
    ]


def test_edit_in_editor_exits_when_no_editor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    monkeypatch.setattr(
        "exercise_library.cli.subprocess.run",
        fake_run,
    )

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
    monkeypatch.setattr(
        "exercise_library.cli.subprocess.run",
        fake_run,
    )

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
    monkeypatch.setattr(
        "exercise_library.cli.subprocess.run",
        fake_run,
    )

    result = cli.edit_in_editor("prompt")

    assert result == "Some content"


def test_edit_in_editor_returns_empty_on_editor_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> Never:
        raise subprocess.CalledProcessError(1, command)

    fake_run = Mock(side_effect=fake_editor)
    monkeypatch.setattr(
        "exercise_library.cli.subprocess.run",
        fake_run,
    )

    result = cli.edit_in_editor("prompt")

    assert result == ""


def test_edit_in_editor_deletes_temporary_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> None:
        filename = command[-1]

        with open(filename, "a", encoding="utf-8") as f:
            f.write("content\n")

    fake_run = Mock(side_effect=fake_editor)
    monkeypatch.setattr(
        "exercise_library.cli.subprocess.run",
        fake_run,
    )

    cli.edit_in_editor("prompt")

    filename = fake_run.call_args.args[0][-1]

    assert not os.path.exists(filename)


def test_edit_in_editor_deletes_file_when_editor_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "editor")

    def fake_editor(command: list[str], check: bool) -> Never:
        raise subprocess.CalledProcessError(1, command)

    fake_run = Mock(side_effect=fake_editor)
    monkeypatch.setattr(
        "exercise_library.cli.subprocess.run",
        fake_run,
    )

    result = cli.edit_in_editor("prompt")

    assert result == ""

    filename = fake_run.call_args.args[0][-1]

    assert not os.path.exists(filename)


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


def test_create_parser_parses_identifier() -> None:
    parser = cli.create_parser()

    args = parser.parse_args(
        [
            "add",
            "-I",
            "book::chapter01::exercise05",
            "prompt",
            "answer",
        ]
    )

    assert args.command == "add"
    assert args.identifier == "book::chapter01::exercise05"
    assert args.prompt == "prompt"
    assert args.answer == "answer"
    assert args.interactive is False


def test_create_parser_identifier_is_optional() -> None:
    parser = cli.create_parser()

    args = parser.parse_args(["add", "prompt", "answer"])

    assert args.identifier is None


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


def test_create_parser_parses_browse_command() -> None:
    parser = cli.create_parser()

    args = parser.parse_args(["browse"])

    assert args.command == "browse"
    assert args.identifier is None


def test_create_parser_parses_browse_identifier() -> None:
    parser = cli.create_parser()

    args = parser.parse_args(
        [
            "browse",
            "-I",
            "book::chapter01",
        ]
    )

    assert args.command == "browse"
    assert args.identifier == "book::chapter01"


def test_create_parser_accepts_long_browse_identifier_flag() -> None:
    parser = cli.create_parser()

    args = parser.parse_args(
        [
            "browse",
            "--identifier",
            "book::chapter01",
        ]
    )

    assert args.command == "browse"
    assert args.identifier == "book::chapter01"


def test_create_parser_rejects_short_browse_identifier_flag() -> None:
    parser = cli.create_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "browse",
                "-i",
                "book::chapter01",
            ]
        )


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
        cli.add_exercise(application, args)

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
        cli.add_exercise(application, args)

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

    cli.add_exercise(application, args)

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

    cli.add_exercise(application, args)

    output = capsys.readouterr().out

    assert "Successfully added exercise with ID 1" in output


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
        cli,
        "edit_in_editor",
        Mock(side_effect=["", "answer"]),
    )

    monkeypatch.setattr(
        "builtins.input",
        Mock(return_value=""),
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.add_exercise(application, args)

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
        cli,
        "edit_in_editor",
        Mock(side_effect=["prompt", ""]),
    )

    monkeypatch.setattr(
        "builtins.input",
        Mock(return_value=""),
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.add_exercise(application, args)

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
        cli,
        "edit_in_editor",
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

    cli.add_exercise(application, args)

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
        cli,
        "edit_in_editor",
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

    cli.add_exercise(application, args)

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
        cli,
        "edit_in_editor",
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

    cli.add_exercise(application, args)

    exercises = application.repository.browse()

    assert len(exercises) == 1
    assert exercises[0].identifier == "book::chapter01::exercise05"

    fake_input.assert_not_called()


def test_add_exercise_interactive_allows_empty_identifier(
    application: ExerciseApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "edit_in_editor",
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

    cli.add_exercise(application, args)

    exercises = application.repository.browse()

    assert len(exercises) == 1
    assert exercises[0].identifier is None


def test_add_exercise_interactive_prints_editor_messages(
    application: ExerciseApplication,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli,
        "edit_in_editor",
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

    cli.add_exercise(application, args)

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
        cli.add_exercise(application, args)

    assert exc_info.value.code == 1

    output = capsys.readouterr().out

    assert (
        "Error: Identifier can only contain letters, numbers, "
        "dash, underscore, and '::' separators."
    ) in output

    assert application.repository.browse() == []


def test_browse_exercises_prints_no_exercises_message(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli.browse_exercises(application, None)

    assert capsys.readouterr().out == "No exercises found.\n"


def test_browse_exercises_prints_exercises(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first_id = application.repository.add(
        Exercise(
            prompt="What is Python?",
            answer="A programming language.",
        )
    )
    second_id = application.repository.add(
        Exercise(
            prompt="What is pytest?",
            answer="A testing framework.",
        )
    )

    cli.browse_exercises(application, None)

    output = capsys.readouterr().out

    assert f"[{first_id}]" in output
    assert "Prompt:\nWhat is Python?" in output
    assert "Answer:\nA programming language." in output

    assert f"[{second_id}]" in output
    assert "Prompt:\nWhat is pytest?" in output
    assert "Answer:\nA testing framework." in output

    assert output.count("-" * 40) == 2


def test_browse_exercises_prints_filtered_exercises(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exercise_id = application.repository.add(
        Exercise(
            identifier="book::chapter01::exercise05",
            prompt="What is the derivative of x^2?",
            answer="2x",
        )
    )

    cli.browse_exercises(
        application,
        "book::chapter01",
    )

    output = capsys.readouterr().out

    assert f"[{exercise_id}]" in output
    assert "book::chapter01::exercise05" in output
    assert "Prompt:\nWhat is the derivative of x^2?" in output
    assert "Answer:\n2x" in output


def test_browse_exercises_prints_identifier(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    application.repository.add(
        Exercise(
            identifier="book::chapter01::exercise05",
            prompt="What is Python?",
            answer="A programming language.",
        )
    )

    cli.browse_exercises(application, None)

    output = capsys.readouterr().out

    assert "Identifier: book::chapter01::exercise05" in output


def test_browse_exercises_does_not_print_missing_identifier(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    application.repository.add(
        Exercise(
            prompt="What is Python?",
            answer="A programming language.",
        )
    )

    cli.browse_exercises(application, None)

    output = capsys.readouterr().out

    assert "Identifier:" not in output


def test_browse_exercises_preserves_multiline_content(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    application.repository.add(
        Exercise(
            prompt="Line one\nLine two",
            answer="Answer one\nAnswer two",
        )
    )

    cli.browse_exercises(application, None)

    output = capsys.readouterr().out

    assert "Prompt:\nLine one\nLine two" in output
    assert "Answer:\nAnswer one\nAnswer two" in output


def test_main_adds_exercise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = Mock()

    parser.parse_args.return_value = argparse.Namespace(
        command="add",
        prompt="prompt",
        answer="answer",
        interactive=False,
        identifier=None,
    )

    initialize_mock = Mock(return_value="connection")
    repository_mock = Mock()
    application_mock = Mock()
    add_exercise_mock = Mock()

    monkeypatch.setattr(
        cli,
        "create_parser",
        Mock(return_value=parser),
    )
    monkeypatch.setattr(
        cli,
        "initialize",
        initialize_mock,
    )
    monkeypatch.setattr(
        cli,
        "ExerciseRepository",
        Mock(return_value=repository_mock),
    )
    monkeypatch.setattr(
        cli,
        "ExerciseApplication",
        Mock(return_value=application_mock),
    )
    monkeypatch.setattr(
        cli,
        "add_exercise",
        add_exercise_mock,
    )

    cli.main()

    initialize_mock.assert_called_once()
    add_exercise_mock.assert_called_once_with(
        application_mock,
        parser.parse_args.return_value,
    )


def test_main_browse_exercises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = Mock()

    parser.parse_args.return_value = argparse.Namespace(
        command="browse",
        identifier=None,
    )

    initialize_mock = Mock(return_value="connection")
    repository_mock = Mock()
    application_mock = Mock()
    browse_exercises_mock = Mock()

    monkeypatch.setattr(
        cli,
        "create_parser",
        Mock(return_value=parser),
    )
    monkeypatch.setattr(
        cli,
        "initialize",
        initialize_mock,
    )
    monkeypatch.setattr(
        cli,
        "ExerciseRepository",
        Mock(return_value=repository_mock),
    )
    monkeypatch.setattr(
        cli,
        "ExerciseApplication",
        Mock(return_value=application_mock),
    )
    monkeypatch.setattr(
        cli,
        "browse_exercises",
        browse_exercises_mock,
    )

    cli.main()

    initialize_mock.assert_called_once()
    browse_exercises_mock.assert_called_once_with(
        application_mock,
        None,
    )


def test_main_browses_exercises_with_identifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = Mock()

    parser.parse_args.return_value = argparse.Namespace(
        command="browse",
        identifier="book::chapter01",
    )

    initialize_mock = Mock(return_value="connection")
    repository_mock = Mock()
    application_mock = Mock()
    browse_exercises_mock = Mock()

    monkeypatch.setattr(
        cli,
        "create_parser",
        Mock(return_value=parser),
    )
    monkeypatch.setattr(
        cli,
        "initialize",
        initialize_mock,
    )
    monkeypatch.setattr(
        cli,
        "ExerciseRepository",
        Mock(return_value=repository_mock),
    )
    monkeypatch.setattr(
        cli,
        "ExerciseApplication",
        Mock(return_value=application_mock),
    )
    monkeypatch.setattr(
        cli,
        "browse_exercises",
        browse_exercises_mock,
    )

    cli.main()

    initialize_mock.assert_called_once()
    browse_exercises_mock.assert_called_once_with(
        application_mock,
        "book::chapter01",
    )


# import argparse
# import os
# import subprocess
# from typing import Never
# from unittest.mock import Mock, call

# import pytest

# import exercise_library.cli as cli
# from exercise_library.application import ExerciseApplication
# from exercise_library.database import initialize
# from exercise_library.models import Exercise
# from exercise_library.repository import ExerciseRepository


# @pytest.fixture
# def application() -> ExerciseApplication:
#     connection = initialize()
#     repository = ExerciseRepository(connection)
#     return ExerciseApplication(repository)


# def test_edit_in_editor_uses_visual_over_editor(
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     monkeypatch.setenv("VISUAL", "visual-editor")
#     monkeypatch.setenv("EDITOR", "other-editor")

#     fake_run = Mock()
#     monkeypatch.setattr(cli.subprocess, "run", fake_run)

#     cli.edit_in_editor("prompt")

#     command = fake_run.call_args.args[0]

#     assert command[0] == "visual-editor"


# def test_edit_in_editor_falls_back_to_editor(
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     monkeypatch.delenv("VISUAL", raising=False)
#     monkeypatch.setenv("EDITOR", "my-editor")

#     fake_run = Mock()
#     monkeypatch.setattr(cli.subprocess, "run", fake_run)

#     cli.edit_in_editor("answer")

#     command = fake_run.call_args.args[0]

#     assert command[0] == "my-editor"


# def test_edit_in_editor_supports_editor_arguments(
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     monkeypatch.delenv("VISUAL", raising=False)
#     monkeypatch.setenv("EDITOR", "my-editor --wait --foo")

#     fake_run = Mock()
#     monkeypatch.setattr(cli.subprocess, "run", fake_run)

#     cli.edit_in_editor("prompt")

#     command = fake_run.call_args.args[0]

#     assert command[:-1] == [
#         "my-editor",
#         "--wait",
#         "--foo",
#     ]


# def test_edit_in_editor_exits_when_no_editor(
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     monkeypatch.delenv("VISUAL", raising=False)
#     monkeypatch.delenv("EDITOR", raising=False)

#     with pytest.raises(SystemExit) as exc_info:
#         cli.edit_in_editor("prompt")

#     assert exc_info.value.code == 1


# def test_edit_in_editor_removes_generated_comments(
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     monkeypatch.setenv("EDITOR", "editor")

#     def fake_editor(command: list[str], check: bool) -> None:
#         filename = command[-1]

#         with open(filename, "a", encoding="utf-8") as f:
#             f.write("# My exercise\n\n")
#             f.write("This is **Markdown**.\n")

#     fake_run = Mock(side_effect=fake_editor)
#     monkeypatch.setattr(cli.subprocess, "run", fake_run)

#     result = cli.edit_in_editor("prompt")

#     assert result == "# My exercise\n\nThis is **Markdown**."


# def test_edit_in_editor_preserves_other_html_comments(
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     monkeypatch.setenv("EDITOR", "editor")

#     def fake_editor(command: list[str], check: bool) -> None:
#         filename = command[-1]

#         with open(filename, "a", encoding="utf-8") as f:
#             f.write("<!-- Keep this comment -->\n")
#             f.write("Some content\n")

#     fake_run = Mock(side_effect=fake_editor)
#     monkeypatch.setattr(cli.subprocess, "run", fake_run)

#     result = cli.edit_in_editor("prompt")

#     assert result == "<!-- Keep this comment -->\nSome content"


# def test_edit_in_editor_strips_surrounding_whitespace(
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     monkeypatch.setenv("EDITOR", "editor")

#     def fake_editor(command: list[str], check: bool) -> None:
#         filename = command[-1]

#         with open(filename, "a", encoding="utf-8") as f:
#             f.write("\n\n  Some content  \n\n")

#     fake_run = Mock(side_effect=fake_editor)
#     monkeypatch.setattr(cli.subprocess, "run", fake_run)

#     result = cli.edit_in_editor("prompt")

#     assert result == "Some content"


# def test_edit_in_editor_returns_empty_on_editor_failure(
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     monkeypatch.setenv("EDITOR", "editor")

#     def fake_editor(command: list[str], check: bool) -> Never:
#         raise subprocess.CalledProcessError(1, command)

#     fake_run = Mock(side_effect=fake_editor)
#     monkeypatch.setattr(cli.subprocess, "run", fake_run)

#     result = cli.edit_in_editor("prompt")

#     assert result == ""


# def test_edit_in_editor_deletes_temporary_file(
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     monkeypatch.setenv("EDITOR", "editor")

#     def fake_editor(command: list[str], check: bool) -> None:
#         filename = command[-1]

#         with open(filename, "a", encoding="utf-8") as f:
#             f.write("content\n")

#     fake_run = Mock(side_effect=fake_editor)
#     monkeypatch.setattr(cli.subprocess, "run", fake_run)

#     cli.edit_in_editor("prompt")

#     file = fake_run.call_args.args[0][-1]

#     assert not os.path.exists(file)


# def test_edit_in_editor_deletes_file_when_editor_fails(
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     monkeypatch.setenv("EDITOR", "editor")

#     def fake_editor(command: list[str], check: bool) -> Never:
#         raise subprocess.CalledProcessError(1, command)

#     fake_run = Mock(side_effect=fake_editor)
#     monkeypatch.setattr(cli.subprocess, "run", fake_run)

#     result = cli.edit_in_editor("prompt")

#     assert result == ""

#     file = fake_run.call_args.args[0][-1]

#     assert not os.path.exists(file)


# def test_create_parser_requires_command() -> None:
#     parser = cli.create_parser()

#     with pytest.raises(SystemExit):
#         parser.parse_args([])


# def test_create_parser_parses_add_arguments() -> None:
#     parser = cli.create_parser()

#     args = parser.parse_args(["add", "prompt", "answer"])

#     assert args.command == "add"
#     assert args.prompt == "prompt"
#     assert args.answer == "answer"
#     assert args.interactive is False


# def test_create_parser_parses_identifier() -> None:
#     parser = cli.create_parser()

#     args = parser.parse_args(
#         [
#             "add",
#             "-I",
#             "book::chapter01::exercise05",
#             "prompt",
#             "answer",
#         ]
#     )

#     assert args.command == "add"
#     assert args.identifier == "book::chapter01::exercise05"
#     assert args.prompt == "prompt"
#     assert args.answer == "answer"
#     assert args.interactive is False


# def test_create_parser_identifier_is_optional() -> None:
#     parser = cli.create_parser()

#     args = parser.parse_args(["add", "prompt", "answer"])

#     assert args.identifier is None


# def test_create_parser_parses_interactive_flag() -> None:
#     parser = cli.create_parser()

#     args = parser.parse_args(["add", "-i"])

#     assert args.command == "add"
#     assert args.prompt is None
#     assert args.answer is None
#     assert args.interactive is True


# def test_create_parser_accepts_long_interactive_flag() -> None:
#     parser = cli.create_parser()

#     args = parser.parse_args(["add", "--interactive"])

#     assert args.interactive is True


# def test_create_parser_parses_browse_command() -> None:
#     parser = cli.create_parser()

#     args = parser.parse_args(["browse"])

#     assert args.command == "browse"
#     assert args.identifier is None


# def test_create_parser_parses_browse_identifier() -> None:
#     parser = cli.create_parser()

#     args = parser.parse_args(
#         [
#             "browse",
#             "-I",
#             "book::chapter01",
#         ]
#     )

#     assert args.command == "browse"
#     assert args.identifier == "book::chapter01"


# def test_create_parser_accepts_long_browse_identifier_flag() -> None:
#     parser = cli.create_parser()

#     args = parser.parse_args(
#         [
#             "browse",
#             "--identifier",
#             "book::chapter01",
#         ]
#     )

#     assert args.command == "browse"
#     assert args.identifier == "book::chapter01"


# def test_create_parser_rejects_short_browse_identifier_flag() -> None:
#     parser = cli.create_parser()

#     with pytest.raises(SystemExit):
#         parser.parse_args(
#             [
#                 "browse",
#                 "-i",
#                 "book::chapter01",
#             ]
#         )


# def test_add_exercise_requires_prompt_and_answer(
#     application: ExerciseApplication,
#     capsys: pytest.CaptureFixture[str],
# ) -> None:
#     args = argparse.Namespace(
#         interactive=False,
#         prompt="",
#         answer="answer",
#         identifier=None,
#     )

#     with pytest.raises(SystemExit) as exc_info:
#         cli.add_exercise(application, args)

#     assert exc_info.value.code == 1
#     assert "prompt and answer are required" in capsys.readouterr().out


# def test_add_exercise_requires_answer(
#     application: ExerciseApplication,
#     capsys: pytest.CaptureFixture[str],
# ) -> None:
#     args = argparse.Namespace(
#         interactive=False,
#         prompt="prompt",
#         answer=None,
#         identifier=None,
#     )

#     with pytest.raises(SystemExit) as exc_info:
#         cli.add_exercise(application, args)

#     assert exc_info.value.code == 1
#     assert "prompt and answer are required" in capsys.readouterr().out


# def test_add_exercise_adds_exercise(
#     application: ExerciseApplication,
# ) -> None:
#     args = argparse.Namespace(
#         interactive=False,
#         prompt="What is Python?",
#         answer="A programming language.",
#         identifier="book::chapter01::exercise05",
#     )

#     cli.add_exercise(application, args)

#     exercises = application.repository.browse()

#     assert exercises == [
#         Exercise(
#             id=1,
#             prompt="What is Python?",
#             answer="A programming language.",
#             identifier="book::chapter01::exercise05",
#         )
#     ]


# def test_add_exercise_prints_success_message(
#     application: ExerciseApplication,
#     capsys: pytest.CaptureFixture[str],
# ) -> None:
#     args = argparse.Namespace(
#         interactive=False,
#         identifier=None,
#         prompt="prompt",
#         answer="answer",
#     )

#     cli.add_exercise(application, args)

#     output = capsys.readouterr().out

#     assert "Successfully added exercise with ID 1" in output


# def test_add_exercise_rejects_empty_interactive_prompt(
#     application: ExerciseApplication,
#     monkeypatch: pytest.MonkeyPatch,
#     capsys: pytest.CaptureFixture[str],
# ) -> None:
#     args = argparse.Namespace(
#         interactive=True,
#         identifier=None,
#         prompt=None,
#         answer=None,
#     )

#     monkeypatch.setattr(
#         cli,
#         "edit_in_editor",
#         Mock(side_effect=["", "answer"]),
#     )

#     monkeypatch.setattr(
#         "builtins.input",
#         Mock(return_value=""),
#     )

#     with pytest.raises(SystemExit) as exc_info:
#         cli.add_exercise(application, args)

#     assert exc_info.value.code == 1
#     assert "Prompt and answer cannot be empty." in capsys.readouterr().out


# def test_add_exercise_rejects_empty_interactive_answer(
#     application: ExerciseApplication,
#     monkeypatch: pytest.MonkeyPatch,
#     capsys: pytest.CaptureFixture[str],
# ) -> None:
#     args = argparse.Namespace(
#         interactive=True,
#         identifier=None,
#         prompt=None,
#         answer=None,
#     )

#     monkeypatch.setattr(
#         cli,
#         "edit_in_editor",
#         Mock(side_effect=["prompt", ""]),
#     )

#     monkeypatch.setattr(
#         "builtins.input",
#         Mock(return_value=""),
#     )

#     with pytest.raises(SystemExit) as exc_info:
#         cli.add_exercise(application, args)

#     assert exc_info.value.code == 1
#     assert "Prompt and answer cannot be empty." in capsys.readouterr().out


# def test_add_exercise_interactive_opens_editor_for_prompt_and_answer(
#     application: ExerciseApplication,
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     fake_editor = Mock(
#         side_effect=[
#             "prompt from editor",
#             "answer from editor",
#         ]
#     )

#     monkeypatch.setattr(
#         cli,
#         "edit_in_editor",
#         fake_editor,
#     )

#     monkeypatch.setattr(
#         "builtins.input",
#         Mock(return_value=""),
#     )

#     args = argparse.Namespace(
#         interactive=True,
#         identifier=None,
#         prompt=None,
#         answer=None,
#     )

#     cli.add_exercise(application, args)

#     assert fake_editor.call_args_list == [
#         call("prompt"),
#         call("answer"),
#     ]

#     exercises = application.repository.browse()

#     assert exercises == [
#         Exercise(
#             id=1,
#             prompt="prompt from editor",
#             answer="answer from editor",
#         )
#     ]


# def test_add_exercise_interactive_asks_for_identifier(
#     application: ExerciseApplication,
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     monkeypatch.setattr(
#         cli,
#         "edit_in_editor",
#         Mock(side_effect=["prompt", "answer"]),
#     )

#     monkeypatch.setattr(
#         "builtins.input",
#         Mock(return_value="book::chapter01::exercise05"),
#     )

#     args = argparse.Namespace(
#         interactive=True,
#         identifier=None,
#         prompt=None,
#         answer=None,
#     )

#     cli.add_exercise(application, args)

#     exercises = application.repository.browse()

#     assert exercises == [
#         Exercise(
#             id=1,
#             prompt="prompt",
#             answer="answer",
#             identifier="book::chapter01::exercise05",
#         )
#     ]


# def test_add_exercise_interactive_uses_provided_identifier(
#     application: ExerciseApplication,
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     monkeypatch.setattr(
#         cli,
#         "edit_in_editor",
#         Mock(side_effect=["prompt", "answer"]),
#     )

#     fake_input = Mock()
#     monkeypatch.setattr(
#         "builtins.input",
#         fake_input,
#     )

#     args = argparse.Namespace(
#         interactive=True,
#         prompt=None,
#         answer=None,
#         identifier="book::chapter01::exercise05",
#     )

#     cli.add_exercise(application, args)

#     exercises = application.repository.browse()

#     assert exercises == [
#         Exercise(
#             id=1,
#             prompt="prompt",
#             answer="answer",
#             identifier="book::chapter01::exercise05",
#         )
#     ]

#     fake_input.assert_not_called()


# def test_add_exercise_interactive_allows_empty_identifier(
#     application: ExerciseApplication,
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     monkeypatch.setattr(
#         cli,
#         "edit_in_editor",
#         Mock(side_effect=["prompt", "answer"]),
#     )

#     monkeypatch.setattr(
#         "builtins.input",
#         Mock(return_value="   "),
#     )

#     args = argparse.Namespace(
#         interactive=True,
#         prompt=None,
#         answer=None,
#         identifier=None,
#     )

#     cli.add_exercise(application, args)

#     exercises = application.repository.browse()

#     assert exercises == [
#         Exercise(
#             id=1,
#             prompt="prompt",
#             answer="answer",
#             identifier=None,
#         )
#     ]


# def test_add_exercise_interactive_prints_editor_messages(
#     application: ExerciseApplication,
#     monkeypatch: pytest.MonkeyPatch,
#     capsys: pytest.CaptureFixture[str],
# ) -> None:
#     monkeypatch.setattr(
#         cli,
#         "edit_in_editor",
#         Mock(side_effect=["prompt", "answer"]),
#     )

#     monkeypatch.setattr(
#         "builtins.input",
#         Mock(return_value=""),
#     )

#     args = argparse.Namespace(
#         interactive=True,
#         identifier=None,
#         prompt=None,
#         answer=None,
#     )

#     cli.add_exercise(application, args)

#     output = capsys.readouterr().out

#     assert "Opening editor for prompt..." in output
#     assert "Opening editor for answer..." in output


# def test_add_exercise_rejects_invalid_identifier(
#     application: ExerciseApplication,
#     capsys: pytest.CaptureFixture[str],
# ) -> None:
#     args = argparse.Namespace(
#         interactive=False,
#         prompt="What is Python?",
#         answer="A programming language.",
#         identifier="book:chapter01",
#     )

#     with pytest.raises(SystemExit) as exc_info:
#         cli.add_exercise(application, args)

#     assert exc_info.value.code == 1

#     output = capsys.readouterr().out

#     assert (
#         "Error: Identifier can only contain letters, numbers, "
#         "dash, underscore, and '::' separators."
#     ) in output

#     assert application.repository.browse() == []


# def test_browse_exercises_prints_no_exercises_message(
#     application: ExerciseApplication,
#     capsys: pytest.CaptureFixture[str],
# ) -> None:
#     cli.browse_exercises(application, None)

#     assert capsys.readouterr().out == "No exercises found.\n"


# def test_browse_exercises_prints_exercises(
#     application: ExerciseApplication,
#     capsys: pytest.CaptureFixture[str],
# ) -> None:
#     application.repository.add(
#         Exercise(
#             id=1,
#             prompt="What is Python?",
#             answer="A programming language.",
#         )
#     )
#     application.repository.add(
#         Exercise(
#             id=2,
#             prompt="What is pytest?",
#             answer="A testing framework.",
#         )
#     )

#     cli.browse_exercises(application, None)

#     output = capsys.readouterr().out

#     assert "[1]" in output
#     assert "Prompt:\nWhat is Python?" in output
#     assert "Answer:\nA programming language." in output

#     assert "[2]" in output
#     assert "Prompt:\nWhat is pytest?" in output
#     assert "Answer:\nA testing framework." in output

#     assert output.count("-" * 40) == 2


# def test_browse_exercises_prints_filtered_exercises(
#     application: ExerciseApplication,
#     capsys: pytest.CaptureFixture[str],
# ) -> None:
#     exercise_id = application.repository.add(
#         Exercise(
#             identifier="book::chapter01::exercise05",
#             prompt="What is the derivative of x^2?",
#             answer="2x",
#         )
#     )

#     cli.browse_exercises(
#         application,
#         "book::chapter01",
#     )

#     output = capsys.readouterr().out

#     assert f"[{exercise_id}]" in output
#     assert "book::chapter01::exercise05" in output
#     assert "Prompt:\nWhat is the derivative of x^2?" in output
#     assert "Answer:\n2x" in output


# def test_browse_exercises_prints_identifier(
#     application: ExerciseApplication,
#     capsys: pytest.CaptureFixture[str],
# ) -> None:
#     application.repository.add(
#         Exercise(
#             id=1,
#             identifier="book::chapter01::exercise05",
#             prompt="What is Python?",
#             answer="A programming language.",
#         )
#     )

#     cli.browse_exercises(application, None)

#     output = capsys.readouterr().out

#     assert "Identifier: book::chapter01::exercise05" in output


# def test_browse_exercises_does_not_print_missing_identifier(
#     application: ExerciseApplication,
#     capsys: pytest.CaptureFixture[str],
# ) -> None:
#     application.repository.add(
#         Exercise(
#             id=1,
#             prompt="What is Python?",
#             answer="A programming language.",
#         )
#     )

#     cli.browse_exercises(application, None)

#     output = capsys.readouterr().out

#     assert "Identifier:" not in output


# def test_browse_exercises_preserves_multiline_content(
#     application: ExerciseApplication,
#     capsys: pytest.CaptureFixture[str],
# ) -> None:
#     application.repository.add(
#         Exercise(
#             id=1,
#             prompt="Line one\nLine two",
#             answer="Answer one\nAnswer two",
#         )
#     )

#     cli.browse_exercises(application, None)

#     output = capsys.readouterr().out

#     assert "Prompt:\nLine one\nLine two" in output
#     assert "Answer:\nAnswer one\nAnswer two" in output


# def test_main_adds_exercise(
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     parser = Mock()

#     parser.parse_args.return_value = argparse.Namespace(
#         command="add",
#         prompt="prompt",
#         answer="answer",
#         interactive=False,
#         identifier=None,
#     )

#     initialize_mock = Mock(return_value="connection")
#     repository_mock = Mock()
#     application_mock = Mock()
#     add_exercise_mock = Mock()

#     monkeypatch.setattr(
#         cli,
#         "create_parser",
#         Mock(return_value=parser),
#     )
#     monkeypatch.setattr(
#         cli,
#         "initialize",
#         initialize_mock,
#     )
#     monkeypatch.setattr(
#         cli,
#         "ExerciseRepository",
#         Mock(return_value=repository_mock),
#     )
#     monkeypatch.setattr(
#         cli,
#         "ExerciseApplication",
#         Mock(return_value=application_mock),
#     )
#     monkeypatch.setattr(
#         cli,
#         "add_exercise",
#         add_exercise_mock,
#     )

#     cli.main()

#     initialize_mock.assert_called_once()
#     add_exercise_mock.assert_called_once_with(
#         application_mock,
#         parser.parse_args.return_value,
#     )


# def test_main_browse_exercises(
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     parser = Mock()

#     parser.parse_args.return_value = argparse.Namespace(
#         command="browse",
#         identifier=None,
#     )

#     initialize_mock = Mock(return_value="connection")
#     repository_mock = Mock()
#     application_mock = Mock()
#     browse_exercises_mock = Mock()

#     monkeypatch.setattr(
#         cli,
#         "create_parser",
#         Mock(return_value=parser),
#     )
#     monkeypatch.setattr(
#         cli,
#         "initialize",
#         initialize_mock,
#     )
#     monkeypatch.setattr(
#         cli,
#         "ExerciseRepository",
#         Mock(return_value=repository_mock),
#     )
#     monkeypatch.setattr(
#         cli,
#         "ExerciseApplication",
#         Mock(return_value=application_mock),
#     )
#     monkeypatch.setattr(
#         cli,
#         "browse_exercises",
#         browse_exercises_mock,
#     )

#     cli.main()

#     initialize_mock.assert_called_once()
#     browse_exercises_mock.assert_called_once_with(
#         application_mock,
#         None,
#     )


# def test_main_browses_exercises_with_identifier(
#     monkeypatch: pytest.MonkeyPatch,
# ) -> None:
#     parser = Mock()

#     parser.parse_args.return_value = argparse.Namespace(
#         command="browse",
#         identifier="book::chapter01",
#     )

#     initialize_mock = Mock(return_value="connection")
#     repository_mock = Mock()
#     application_mock = Mock()
#     browse_exercises_mock = Mock()

#     monkeypatch.setattr(
#         cli,
#         "create_parser",
#         Mock(return_value=parser),
#     )
#     monkeypatch.setattr(
#         cli,
#         "initialize",
#         initialize_mock,
#     )
#     monkeypatch.setattr(
#         cli,
#         "ExerciseRepository",
#         Mock(return_value=repository_mock),
#     )
#     monkeypatch.setattr(
#         cli,
#         "ExerciseApplication",
#         Mock(return_value=application_mock),
#     )
#     monkeypatch.setattr(
#         cli,
#         "browse_exercises",
#         browse_exercises_mock,
#     )

#     cli.main()

#     initialize_mock.assert_called_once()
#     browse_exercises_mock.assert_called_once_with(
#         application_mock,
#         "book::chapter01",
#     )
