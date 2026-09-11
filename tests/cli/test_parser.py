from pathlib import Path
from uuid import uuid7

import pytest

from exercise_library.cli.parser import Parser

# ------------------------------------------------------------------------------
# Add command
# ------------------------------------------------------------------------------


def test_add_with_prompt_and_answer() -> None:

    args = Parser().get_args(
        [
            "add",
            "What is 2 + 2?",
            "4",
        ]
    )

    assert args.command == "add"
    assert args.prompt == "What is 2 + 2?"
    assert args.answer == "4"
    assert args.interactive is False
    assert args.identifier is None


def test_add_with_prompt_answer_and_identifier() -> None:
    args = Parser().get_args(
        ["add", "What is 2 + 2?", "4", "--identifier", "exercise1"]
    )

    assert args.command == "add"
    assert args.prompt == "What is 2 + 2?"
    assert args.answer == "4"
    assert args.interactive is False
    assert args.identifier == "exercise1"


def test_add_interactive() -> None:

    args = Parser().get_args(
        [
            "add",
            "--interactive",
        ]
    )

    assert args.command == "add"
    assert args.prompt is None
    assert args.answer is None
    assert args.interactive is True
    assert args.identifier is None


def test_add_interactive_ignores_prompt_answer_and_identifier() -> None:

    args = Parser().get_args(
        [
            "add",
            "--interactive",
            "prompt content",
            "answer content",
            "--identifier",
            "identifier",
        ]
    )

    assert args.command == "add"
    assert args.prompt is None
    assert args.answer is None
    assert args.identifier is None
    assert args.interactive is True


def test_add_with_identifier() -> None:

    args = Parser().get_args(
        [
            "add",
            "What is 2 + 2?",
            "4",
            "--identifier",
            "math",
        ]
    )

    assert args.command == "add"
    assert args.prompt == "What is 2 + 2?"
    assert args.answer == "4"
    assert args.interactive is False
    assert args.identifier == "math"


def test_add_missing_prompt_raises(
    capsys: pytest.CaptureFixture[str],
) -> None:

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(
            [
                "add",
                "4",
            ]
        )

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "prompt and answer are required" in captured.err
    assert "usage:" in captured.err
    assert "add" in captured.err


def test_add_missing_answer_raises(
    capsys: pytest.CaptureFixture[str],
) -> None:

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(
            [
                "add",
                "What is 2 + 2?",
            ]
        )

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "prompt and answer are required" in captured.err
    assert "usage:" in captured.err
    assert "add" in captured.err


def test_add_missing_prompt_and_answer_raises(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(
            [
                "add",
            ]
        )

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "prompt and answer are required" in captured.err
    assert "usage:" in captured.err
    assert "add" in captured.err


# ------------------------------------------------------------------------------
# Browse command
# ------------------------------------------------------------------------------


def test_browse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    args = Parser().get_args(
        [
            "browse",
        ]
    )

    assert args.command == "browse"
    assert args.identifier is None


def test_browse_with_identifier() -> None:

    args = Parser().get_args(
        [
            "browse",
            "--identifier",
            "math",
        ]
    )

    assert args.command == "browse"
    assert args.identifier == "math"


def test_backup_with_file() -> None:
    args = Parser().get_args(
        [
            "backup",
            "--output",
            "file-name.zip",
        ]
    )

    assert args.command == "backup"
    assert isinstance(args.output, Path)
    assert args.output == Path("file-name.zip")


def test_backup_with_file_without_zip_suffix(
    capsys: pytest.CaptureFixture[str],
) -> None:

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(
            [
                "backup",
                "--output",
                "file-name",
            ]
        )

    assert exc_info.value.code == 2
    assert "backup path must end with '.zip'" in capsys.readouterr().err


def test_backup_with_uppercase_zip_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = Parser().get_args(
        [
            "backup",
            "--output",
            "file-name.ZIP",
        ]
    )

    assert args.output == Path("file-name.ZIP")


def test_backup_with_nonexistent_parent_directory(
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = Path("does-not-exist") / "backup.zip"

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(
            [
                "backup",
                "--output",
                str(output),
            ]
        )

    assert exc_info.value.code == 2
    assert (
        f"parent directory does not exist: {output.parent}" in capsys.readouterr().err
    )


def test_backup_with_parent_that_is_a_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parent_file = tmp_path / "not-a-directory"
    parent_file.touch()

    output = parent_file / "backup.zip"

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(
            [
                "backup",
                "--output",
                str(output),
            ]
        )

    assert exc_info.value.code == 2
    assert f"parent path is not a directory: {parent_file}" in capsys.readouterr().err


def test_backup_with_existing_parent_directory(
    tmp_path: Path,
) -> None:
    output = tmp_path / "backup.zip"

    args = Parser().get_args(
        [
            "backup",
            "--output",
            str(output),
        ]
    )

    assert args.command == "backup"
    assert isinstance(args.output, Path)
    assert args.output == output


@pytest.mark.parametrize("filename", [".zip", "    .zip"])
def test_backup_with_empty_filename(
    filename: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / filename

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["backup", "--output", str(output)])

    assert exc_info.value.code == 2
    assert "backup filename must not be empty" in capsys.readouterr().err


def test_command_is_required(
    capsys: pytest.CaptureFixture[str],
) -> None:

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args([])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "the following arguments are required: command" in captured.err


def test_unknown_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["unknown"])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "invalid choice" in captured.err


# ------------------------------------------------------------------------------
# Edit command
# ------------------------------------------------------------------------------
def test_edit_command_requires_id_or_identifier(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["edit"])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "at least 'id' or 'identifier' must be provided." in captured.err


def test_edit_command_raise_if_no_new_field_is_provided(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["edit", "-I", "identifier"])

    assert exc_info.value.code == 2

    assert (
        "Please provide at least one of: "
        + "'new prompt', 'new answer', or 'new identifier'."
    )


def test_edit_command_turns_non_provided_args_into_none() -> None:
    args = Parser().get_args(
        [
            "edit",
            "--id",
            "id",
            "--new-prompt",
            "new prompt",
        ]
    )

    assert args.id == "id"
    assert args.identifier is None
    assert args.new_prompt == "new prompt"
    assert args.new_answer is None
    assert args.new_identifier is None

    args = Parser().get_args(
        [
            "edit",
            "--identifier",
            "identifier",
            "--new-answer",
            "new answer",
        ]
    )

    assert args.id is None
    assert args.identifier == "identifier"
    assert args.new_prompt is None
    assert args.new_answer == "new answer"
    assert args.new_identifier is None


def test_edit_command_gets_args() -> None:
    args = Parser().get_args(
        [
            "edit",
            "--id",
            "id",
            "-I",
            "identifier",
            "--new-prompt",
            "new prompt",
            "--new-answer",
            "new answer",
            "--new-identifier",
            "new-identifier",
        ]
    )

    assert args.id == "id"
    assert args.identifier == "identifier"
    assert args.new_prompt == "new prompt"
    assert args.new_answer == "new answer"
    assert args.new_identifier == "new-identifier"


def test_edit_command_interactive_ignores_new_content_cli_args() -> None:
    args = Parser().get_args(
        [
            "edit",
            "--interactive",
            "-I",
            "identifier",
            "--id",
            "id",
            "--new-prompt",
            "new prompt",
            "--new-answer",
            "new answer",
            "--new-identifier",
            "new-identifier",
        ]
    )

    assert args.interactive
    assert args.identifier == "identifier"
    assert args.id == "id"
    assert args.new_prompt is None
    assert args.new_answer is None
    assert args.new_identifier is None


# ------------------------------------------------------------------------------
# Show command
# ------------------------------------------------------------------------------


def test_show_command_requires_identifier_or_id(
    capsys: pytest.CaptureFixture[str],
) -> None:

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(
            [
                "show",
            ]
        )

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert (
        "show: error: one of the arguments --identifier/-I --id is required"
        in captured.err
    )

    args = Parser().get_args(["show", "-I", "identifier"])
    assert args.identifier == "identifier"

    id = uuid7()

    args = Parser().get_args(["show", "--id", str(id)])
    assert args.id == id


def test_show_command_raises_if_identifier_and_id_provided(
    capsys: pytest.CaptureFixture[str],
) -> None:
    id = uuid7()

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["show", "--id", str(id), "-I", "identifier"])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert (
        "show: error: argument --identifier/-I: not allowed with argument --id"
        in captured.err
    )

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["show", "-I", "identifier", "--id", str(id)])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert (
        "show: error: argument --id: not allowed with argument --identifier/-I"
        in captured.err
    )


def test_show_command_accepts_only_one_field(
    capsys: pytest.CaptureFixture[str],
) -> None:

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["show", "-I", "identifier", "-f", "prompt", "-f", "answer"])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "show: error: -f may only be specified once" in captured.err

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(
            ["show", "-I", "identifier", "--field", "prompt", "--field", "answer"]
        )

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "show: error: --field may only be specified once" in captured.err

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(
            ["show", "-I", "identifier", "-f", "prompt", "--field", "answer"]
        )

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "show: error: --field may only be specified once" in captured.err

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(
            ["show", "-I", "identifier", "--field", "prompt", "-f", "answer"]
        )

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "show: error: -f may only be specified once" in captured.err


def test_show_command_gets_args() -> None:
    args = Parser().get_args(["show", "--identifier", "identifier", "-f", "prompt"])

    assert args.identifier == "identifier"
    assert args.field == "prompt"

    id = uuid7()
    args = Parser().get_args(["show", "--id", str(id), "-f", "answer"])

    assert args.id == id
    assert args.field == "answer"


def test_show_command_rejects_unknown_field(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["show", "--identifier", "identifier", "-f", "unknown"])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert (
        "show: error: argument --field/-f:"
        + " invalid choice: 'unknown' (choose from 'prompt', 'answer')"
    ) in captured.err
