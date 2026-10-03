import sys

import pytest

from exercise_library.cli.main import main


def run_main(
    monkeypatch: pytest.MonkeyPatch,
    *args: str,
) -> int:
    monkeypatch.setattr(
        sys,
        "argv",
        ["exercise-library", *args],
    )

    return main()


def test_add_exercise(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = run_main(
        monkeypatch,
        "add",
        "What is 2 + 2?",
        "4",
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "Exercise was successfully added to the library.\n"
    assert captured.err == ""


def test_browse_exercises(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_main(
        monkeypatch,
        "add",
        "What is 2 + 2?",
        "4",
    )
    capsys.readouterr()

    exit_code = run_main(
        monkeypatch,
        "browse",
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "What is 2 + 2?" in captured.out
    assert captured.err == ""


def test_add_exercise_with_identifier(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = run_main(
        monkeypatch,
        "add",
        "What is 2 + 2?",
        "4",
        "--identifier",
        "math",
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "Exercise was successfully added to the library.\n"
    assert captured.err == ""


def test_browse_exercises_with_identifier(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_main(
        monkeypatch,
        "add",
        "What is 2 + 2?",
        "4",
        "--identifier",
        "math",
    )
    capsys.readouterr()

    exit_code = run_main(
        monkeypatch,
        "browse",
        "--identifier",
        "math",
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "What is 2 + 2?" in captured.out
    assert captured.err == ""


def test_application_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_main(monkeypatch, "add", "What is 2 + 2?", "4", '--identifier="A"')
    capsys.readouterr()

    exit_code = run_main(monkeypatch, "add", "What is 2 + 2?", "4", '--identifier="A"')

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.startswith("ERROR:")


def test_add_then_browse(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        run_main(
            monkeypatch,
            "add",
            "What is Python?",
            "A programming language.",
        )
        == 0
    )
    capsys.readouterr()

    assert run_main(monkeypatch, "browse") == 0

    captured = capsys.readouterr()

    assert "What is Python?" in captured.out
    assert "UUID" in captured.out
    assert "IDENTIFIER" in captured.out
    assert "PROMPT" in captured.out
    assert "(no identifier)" in captured.out


def test_identifiers_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_main(monkeypatch, "add", "p1", "a1", "-I", "book::chapter01::exercise01")
    run_main(monkeypatch, "add", "p2", "a2", "-I", "book::chapter02::exercise01")
    capsys.readouterr()

    exit_code = run_main(monkeypatch, "identifiers")

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == (
        "book::chapter01::exercise01\nbook::chapter02::exercise01\n"
    )
    assert captured.err == ""


def test_identifiers_command_with_depth_and_count(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_main(monkeypatch, "add", "p1", "a1", "-I", "book::chapter01::exercise01")
    run_main(monkeypatch, "add", "p2", "a2", "-I", "book::chapter01::exercise02")
    run_main(monkeypatch, "add", "p3", "a3", "-I", "book::chapter02::exercise01")
    capsys.readouterr()

    exit_code = run_main(monkeypatch, "identifiers", "--depth", "2", "--count")

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ("book::chapter01 (2)\nbook::chapter02 (1)\n")
    assert captured.err == ""


def test_identifiers_command_without_matches(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = run_main(monkeypatch, "identifiers")

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "No identifiers found.\n"
    assert captured.err == ""
