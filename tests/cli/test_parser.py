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
def test_edit_command_requires_selector(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["edit"])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "edit: error: the following arguments are required: selector" in (
        captured.err
    )

    args = Parser().get_args(["edit", "identifier", "--new-prompt", "new prompt"])
    assert args.selector == "identifier"

    uuid = uuid7()

    args = Parser().get_args(["edit", str(uuid), "--new-prompt", "new prompt"])
    assert args.selector == str(uuid)


def test_edit_command_rejects_old_selector_flags(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["edit", "-I", "identifier"])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "unrecognized arguments: -I" in captured.err

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["edit", "--uuid", str(uuid7())])

    assert exc_info.value.code == 2

    assert "unrecognized arguments: --uuid" in capsys.readouterr().err


def test_edit_command_raise_if_no_new_field_is_provided(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["edit", "identifier"])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert (
        "Please provide at least one of: "
        + "'new prompt', 'new answer', or 'new identifier'."
    ) in captured.err


def test_edit_command_turns_non_provided_args_into_none() -> None:
    args = Parser().get_args(
        [
            "edit",
            "uuid",
            "--new-prompt",
            "new prompt",
        ]
    )

    assert args.selector == "uuid"
    assert args.new_prompt == "new prompt"
    assert args.new_answer is None
    assert args.new_identifier is None

    args = Parser().get_args(
        [
            "edit",
            "identifier",
            "--new-answer",
            "new answer",
        ]
    )

    assert args.selector == "identifier"
    assert args.new_prompt is None
    assert args.new_answer == "new answer"
    assert args.new_identifier is None


def test_edit_command_gets_args() -> None:
    args = Parser().get_args(
        [
            "edit",
            "identifier",
            "--new-prompt",
            "new prompt",
            "--new-answer",
            "new answer",
            "--new-identifier",
            "new-identifier",
        ]
    )

    assert args.selector == "identifier"
    assert args.new_prompt == "new prompt"
    assert args.new_answer == "new answer"
    assert args.new_identifier == "new-identifier"


def test_edit_command_interactive_ignores_new_content_cli_args() -> None:
    args = Parser().get_args(
        [
            "edit",
            "identifier",
            "--interactive",
            "--new-prompt",
            "new prompt",
            "--new-answer",
            "new answer",
            "--new-identifier",
            "new-identifier",
        ]
    )

    assert args.interactive
    assert args.selector == "identifier"
    assert args.new_prompt is None
    assert args.new_answer is None
    assert args.new_identifier is None


# ------------------------------------------------------------------------------
# Show command
# ------------------------------------------------------------------------------


def test_show_command_requires_selector(
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

    assert "show: error: the following arguments are required: selector" in (
        captured.err
    )

    args = Parser().get_args(["show", "identifier"])
    assert args.selector == "identifier"

    uuid = uuid7()

    args = Parser().get_args(["show", str(uuid)])
    assert args.selector == str(uuid)


def test_show_command_rejects_old_selector_flags(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["show", "-I", "identifier"])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "unrecognized arguments: -I" in captured.err

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["show", "--uuid", str(uuid7())])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "unrecognized arguments: --uuid" in captured.err


def test_show_command_accepts_only_one_field(
    capsys: pytest.CaptureFixture[str],
) -> None:

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["show", "identifier", "-f", "prompt", "-f", "answer"])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "show: error: -f may only be specified once" in captured.err

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(
            ["show", "identifier", "--field", "prompt", "--field", "answer"]
        )

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "show: error: --field may only be specified once" in captured.err

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["show", "identifier", "-f", "prompt", "--field", "answer"])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "show: error: --field may only be specified once" in captured.err

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["show", "identifier", "--field", "prompt", "-f", "answer"])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "show: error: -f may only be specified once" in captured.err


def test_show_command_gets_args() -> None:
    args = Parser().get_args(["show", "identifier", "-f", "prompt"])

    assert args.selector == "identifier"
    assert args.field == "prompt"
    assert not args.open_in_browser

    uuid = uuid7()
    args = Parser().get_args(["show", str(uuid), "-f", "answer"])

    assert args.selector == str(uuid)
    assert args.field == "answer"
    assert not args.open_in_browser


def test_show_command_gets_args_with_open_in_browser_option() -> None:
    args = Parser().get_args(["show", "identifier", "-f", "prompt", "-o"])

    assert args.selector == "identifier"
    assert args.field == "prompt"
    assert args.open_in_browser

    uuid = uuid7()
    args = Parser().get_args(["show", str(uuid), "-f", "answer", "--open-in-browser"])

    assert args.selector == str(uuid)
    assert args.field == "answer"
    assert args.open_in_browser


def test_show_command_rejects_unknown_field(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["show", "identifier", "-f", "unknown"])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert (
        "show: error: argument --field/-f:"
        + " invalid choice: 'unknown' (choose from 'prompt', 'answer')"
    ) in captured.err


# ------------------------------------------------------------------------------
# Identifiers command
# ------------------------------------------------------------------------------


def test_identifiers_command_defaults() -> None:
    args = Parser().get_args(["identifiers"])

    assert args.command == "identifiers"
    assert args.identifier is None
    assert args.depth is None
    assert args.count is False


def test_identifiers_command_with_identifier() -> None:
    args = Parser().get_args(["identifiers", "--identifier", "book"])

    assert args.identifier == "book"

    args = Parser().get_args(["identifiers", "-I", "book"])

    assert args.identifier == "book"


def test_identifiers_command_with_depth() -> None:
    args = Parser().get_args(["identifiers", "--depth", "2"])

    assert args.depth == 2

    args = Parser().get_args(["identifiers", "-d", "3"])

    assert args.depth == 3


def test_identifiers_command_with_count() -> None:
    args = Parser().get_args(["identifiers", "--count"])

    assert args.count is True

    args = Parser().get_args(["identifiers", "-c"])

    assert args.count is True


def test_identifiers_command_gets_args() -> None:
    args = Parser().get_args(
        ["identifiers", "-I", "book", "-d", "2", "-c"],
    )

    assert args.command == "identifiers"
    assert args.identifier == "book"
    assert args.depth == 2
    assert args.count is True


@pytest.mark.parametrize("value", ["0", "-1"])
def test_identifiers_command_rejects_non_positive_depth(
    value: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["identifiers", "--depth", value])

    assert exc_info.value.code == 2
    assert "must be a positive integer" in capsys.readouterr().err


def test_identifiers_command_rejects_non_integer_depth(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["identifiers", "--depth", "not-a-number"])

    assert exc_info.value.code == 2
    assert "invalid" in capsys.readouterr().err


# ------------------------------------------------------------------------------
# Media command
# ------------------------------------------------------------------------------


def test_media_add_gets_args(tmp_path: Path) -> None:
    source = tmp_path / "diagram.png"
    source.write_bytes(b"image")

    args = Parser().get_args(["media", "add", str(source)])

    assert args.command == "media"
    assert args.media_command == "add"
    assert args.path == source


def test_media_add_rejects_missing_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing = tmp_path / "missing.png"

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["media", "add", str(missing)])

    assert exc_info.value.code == 2
    assert f"file does not exist: {missing}" in capsys.readouterr().err


def test_media_add_rejects_directory(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["media", "add", str(tmp_path)])

    assert exc_info.value.code == 2
    assert f"not a file: {tmp_path}" in capsys.readouterr().err


def test_media_list_gets_args() -> None:
    args = Parser().get_args(["media", "list"])

    assert args.command == "media"
    assert args.media_command == "list"


def test_media_requires_subcommand(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["media"])

    assert exc_info.value.code == 2
    assert "media_command" in capsys.readouterr().err


def test_next_defaults() -> None:
    args = Parser().get_args(["next"])

    assert args.command == "next"
    assert args.identifier is None
    assert args.status == "all"
    assert args.dry_run is False


def test_next_accepts_all_flags() -> None:
    args = Parser().get_args(["next", "-I", "math", "--status", "new", "--dry-run"])

    assert args.identifier == "math"
    assert args.status == "new"
    assert args.dry_run is True


def test_next_rejects_invalid_status() -> None:
    with pytest.raises(SystemExit):
        Parser().get_args(["next", "--status", "bogus"])


def test_rate_parses_positional_selector_and_rating() -> None:
    args = Parser().get_args(["rate", "math::limits", "good"])

    assert args.command == "rate"
    assert args.selector == "math::limits"
    assert args.rating == "good"


def test_rate_parses_uuid_selector() -> None:
    uuid = uuid7()

    args = Parser().get_args(["rate", str(uuid), "good"])

    assert args.selector == str(uuid)
    assert args.rating == "good"


def test_rate_requires_a_selector_and_rating(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["rate"])

    assert exc_info.value.code == 2
    assert "the following arguments are required: selector, rating" in (
        capsys.readouterr().err
    )

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["rate", "math::limits"])

    assert exc_info.value.code == 2
    assert "the following arguments are required: rating" in capsys.readouterr().err


def test_rate_rejects_old_selector_flags(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["rate", "-I", "math::limits", "good"])

    assert exc_info.value.code == 2
    assert "unrecognized arguments: -I" in capsys.readouterr().err

    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["rate", "--uuid", str(uuid7()), "good"])

    assert exc_info.value.code == 2
    assert "unrecognized arguments: --uuid" in capsys.readouterr().err


def test_rate_rejects_invalid_rating(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        Parser().get_args(["rate", "math::limits", "meh"])

    assert exc_info.value.code == 2
    assert "invalid choice: 'meh'" in capsys.readouterr().err
