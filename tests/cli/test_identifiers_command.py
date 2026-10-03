import pytest

from exercise_library.application import ExerciseApplication
from exercise_library.cli.identifiers_command import list_identifiers


def _add(
    application: ExerciseApplication,
    identifier: str,
) -> None:
    application.add_exercise(
        prompt=f"prompt for {identifier}",
        answer=f"answer for {identifier}",
        identifier=identifier,
    )


def test_list_identifiers_prints_no_identifiers_message(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    list_identifiers(application, identifier=None, depth=None, count=False)

    assert capsys.readouterr().out == "No identifiers found.\n"


def test_list_identifiers_prints_prefixes(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _add(application, "book::chapter01::exercise01")
    _add(application, "other")

    list_identifiers(application, identifier=None, depth=None, count=False)

    assert capsys.readouterr().out == ("book::chapter01::exercise01\nother\n")


def test_list_identifiers_does_not_print_counts_by_default(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _add(application, "book::chapter01")

    list_identifiers(application, identifier=None, depth=None, count=False)

    output = capsys.readouterr().out

    assert "book" in output
    assert "book (1)" not in output


def test_list_identifiers_prints_counts(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _add(application, "book::chapter01::exercise01")
    _add(application, "book::chapter01::exercise02")

    list_identifiers(application, identifier=None, depth=None, count=True)

    assert capsys.readouterr().out == (
        "book::chapter01::exercise01 (1)\nbook::chapter01::exercise02 (1)\n"
    )


def test_list_identifiers_respects_depth(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _add(application, "book::chapter01::exercise01")
    _add(application, "book::chapter02::exercise01")

    list_identifiers(application, identifier=None, depth=2, count=False)

    assert capsys.readouterr().out == ("book::chapter01\nbook::chapter02\n")


def test_list_identifiers_filters_by_identifier(
    application: ExerciseApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _add(application, "book::chapter01::exercise01")
    _add(application, "book::chapter02::exercise01")

    list_identifiers(application, identifier="book::chapter01", depth=None, count=False)

    assert capsys.readouterr().out == "book::chapter01::exercise01\n"
