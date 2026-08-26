import argparse
import sys

import pytest

from exercise_library.cli.parser import Parser


def get_args(
    monkeypatch: pytest.MonkeyPatch,
    *args: str,
) -> argparse.Namespace:
    monkeypatch.setattr(
        sys,
        "argv",
        ["exercise-library", *args],
    )

    return Parser().get_args()


def test_add_with_prompt_and_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = get_args(
        monkeypatch,
        "add",
        "What is 2 + 2?",
        "4",
    )

    assert args.command == "add"
    assert args.prompt == "What is 2 + 2?"
    assert args.answer == "4"
    assert args.interactive is False
    assert args.identifier is None


def test_add_interactive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = get_args(
        monkeypatch,
        "add",
        "--interactive",
    )

    assert args.command == "add"
    assert args.prompt is None
    assert args.answer is None
    assert args.interactive is True
    assert args.identifier is None


def test_add_interactive_ignores_prompt_and_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = get_args(
        monkeypatch,
        "add",
        "--interactive",
        "prompt content",
        "answer content",
    )

    assert args.command == "add"
    assert args.prompt is None
    assert args.answer is None
    assert args.interactive is True
    assert args.identifier is None


def test_add_with_identifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = get_args(
        monkeypatch,
        "add",
        "What is 2 + 2?",
        "4",
        "--identifier",
        "math",
    )

    assert args.command == "add"
    assert args.prompt == "What is 2 + 2?"
    assert args.answer == "4"
    assert args.interactive is False
    assert args.identifier == "math"


def test_add_missing_prompt(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:

    with pytest.raises(SystemExit) as exc_info:
        get_args(
            monkeypatch,
            "add",
            "4",
        )

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "prompt and answer are required" in captured.err
    assert "usage:" in captured.err
    assert "exercise-library add" in captured.err


def test_add_missing_answer(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:

    with pytest.raises(SystemExit) as exc_info:
        get_args(monkeypatch, "add", "What is 2 + 2?")

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "prompt and answer are required" in captured.err
    assert "usage:" in captured.err
    assert "exercise-library add" in captured.err


def test_browse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = get_args(
        monkeypatch,
        "browse",
    )

    assert args.command == "browse"
    assert args.identifier is None


def test_browse_with_identifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = get_args(
        monkeypatch,
        "browse",
        "--identifier",
        "math",
    )

    assert args.command == "browse"
    assert args.identifier == "math"


def test_command_is_required(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:

    with pytest.raises(SystemExit) as exc_info:
        get_args(monkeypatch)

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "the following arguments are required: command" in captured.err


def test_unknown_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        get_args(monkeypatch, "unknown")

    assert exc_info.value.code == 2

    captured = capsys.readouterr()

    assert "invalid choice" in captured.err
